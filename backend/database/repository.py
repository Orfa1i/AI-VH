"""
AI Virtual Hospital - Clinical Database Repository
Provides unified CRUD, querying, and persistent storage for clinical reports,
physician reviews, DPO pairs, and knowledge embeddings across PostgreSQL and SQLite.
"""

import json
import logging
import uuid
import random
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .connection import db_manager, DatabaseConnectionManager
from .schema import SQLITE_SCHEMA, POSTGRES_SCHEMA
from ..clinical.models import ClinicalReport, PhysicianReview, TrainingDatasetRecord

logger = logging.getLogger("DatabaseRepository")


class DatabaseRepository:
    def __init__(self, manager: Optional[DatabaseConnectionManager] = None):
        self.manager = manager or db_manager
        self.init_schema()

    def init_schema(self):
        """Initializes tables and indexes in the active database engine."""
        ddl = POSTGRES_SCHEMA if self.manager.engine_type == "postgresql" else SQLITE_SCHEMA
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if self.manager.engine_type == "sqlite":
                cur.executescript(ddl)
                # Ensure raw_json column exists in clinical_reports for existing sqlite DBs
                cur.execute("PRAGMA table_info(clinical_reports);")
                cols = [row[1] for row in cur.fetchall()]
                if "raw_json" not in cols:
                    try:
                        cur.execute("ALTER TABLE clinical_reports ADD COLUMN raw_json TEXT DEFAULT '{}';")
                    except Exception as e:
                        logger.warning(f"Could not add raw_json column to clinical_reports: {e}")
            else:
                cur.execute(ddl)
            logger.info(f"Database schema initialized successfully on {self.manager.engine_type}.")

    # =========================================================================
    # Clinical Reports
    # =========================================================================

    def save_report(self, report: ClinicalReport, case_id: Optional[str] = None) -> str:
        """Persists or updates a clinical report record."""
        case_id = case_id or getattr(report, "patient_id", "CASE-101")
        is_pg = self.manager.engine_type == "postgresql"
        raw_json_str = report.model_dump_json()

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            # Ensure encounter exists
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO encounters (encounter_id, case_id, patient_name, status, current_department, report_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (encounter_id) DO UPDATE SET report_id = EXCLUDED.report_id;
                    """,
                    (report.encounter_id, case_id, report.patient_name, "COMPLETED", "INTERNAL_MEDICINE", report.id)
                )
                cur.execute(
                    """
                    INSERT INTO clinical_reports (
                        id, encounter_id, case_id, patient_name, primary_diagnosis,
                        confidence_score, created_at, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        primary_diagnosis = EXCLUDED.primary_diagnosis,
                        confidence_score = EXCLUDED.confidence_score,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (
                        report.id, report.encounter_id, case_id, report.patient_name,
                        report.primary_diagnosis, report.diagnostic_confidence,
                        report.created_at, raw_json_str
                    )
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO encounters (encounter_id, case_id, patient_name, status, current_department, report_id)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (report.encounter_id, case_id, report.patient_name, "COMPLETED", "INTERNAL_MEDICINE", report.id)
                )
                cur.execute(
                    """
                    INSERT OR REPLACE INTO clinical_reports (
                        id, encounter_id, case_id, patient_name, primary_diagnosis,
                        confidence_score, created_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        report.id, report.encounter_id, case_id, report.patient_name,
                        report.primary_diagnosis, report.diagnostic_confidence,
                        report.created_at.isoformat(), raw_json_str
                    )
                )
            logger.info(f"Clinical report {report.id} saved to {self.manager.engine_type} database.")
            return report.id

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single clinical report by ID."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT raw_json FROM clinical_reports WHERE id = %s" if is_pg else "SELECT raw_json FROM clinical_reports WHERE id = ?"
            cur.execute(query, (report_id,))
            row = cur.fetchone()
            if not row:
                return None
            val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
            return json.loads(val) if isinstance(val, str) else val

    def get_report_model(self, report_id: str) -> Optional[ClinicalReport]:
        """Retrieves a single clinical report reconstructed as a Pydantic model."""
        data = self.get_report(report_id)
        if not data:
            return None
        return ClinicalReport.model_validate(data)

    def list_reports(self, case_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Lists reports with optional case filtering."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if case_id:
                query = "SELECT raw_json FROM clinical_reports WHERE case_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s" if is_pg else "SELECT raw_json FROM clinical_reports WHERE case_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
                cur.execute(query, (case_id, limit, offset))
            else:
                query = "SELECT raw_json FROM clinical_reports ORDER BY created_at DESC LIMIT %s OFFSET %s" if is_pg else "SELECT raw_json FROM clinical_reports ORDER BY created_at DESC LIMIT ? OFFSET ?"
                cur.execute(query, (limit, offset))
            rows = cur.fetchall()
            results = []
            for row in rows:
                val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
                results.append(json.loads(val) if isinstance(val, str) else val)
            return results

    def count_reports(self) -> int:
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM clinical_reports;")
            res = cur.fetchone()
            return res[0] if res else 0

    # =========================================================================
    # Report Evaluations (Independent 6-Dimension Pipeline)
    # =========================================================================

    def save_evaluation(self, eval_result: Any) -> str:
        """Persists automated multi-stage evaluation result."""
        is_pg = self.manager.engine_type == "postgresql"
        data = eval_result.model_dump() if hasattr(eval_result, "model_dump") else dict(eval_result)
        raw_json_str = json.dumps(data, default=str)
        eval_id = data.get("evaluation_id", str(uuid.uuid4()))
        report_id = data.get("report_id", "")
        encounter_id = data.get("encounter_id", "")
        score = float(data.get("overall_score", 0.0))
        severity = str(data.get("severity", "INFO"))
        status = str(data.get("final_status", "PASSED"))
        passed = bool(data.get("passed", False))
        evaluated_at = data.get("evaluated_at", datetime.now(timezone.utc).isoformat())
        if isinstance(evaluated_at, datetime):
            evaluated_at = evaluated_at.isoformat()

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO report_evaluations (
                        id, report_id, encounter_id, overall_score, severity,
                        final_status, passed, evaluated_at, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        overall_score = EXCLUDED.overall_score,
                        severity = EXCLUDED.severity,
                        final_status = EXCLUDED.final_status,
                        passed = EXCLUDED.passed,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (eval_id, report_id, encounter_id, score, severity, status, passed, evaluated_at, raw_json_str)
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO report_evaluations (
                        id, report_id, encounter_id, overall_score, severity,
                        final_status, passed, evaluated_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (eval_id, report_id, encounter_id, score, severity, status, passed, evaluated_at, raw_json_str)
                )
        return eval_id

    def get_evaluation_for_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves evaluation result for a report ID."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT raw_json FROM report_evaluations WHERE report_id = %s ORDER BY evaluated_at DESC LIMIT 1" if is_pg else "SELECT raw_json FROM report_evaluations WHERE report_id = ? ORDER BY evaluated_at DESC LIMIT 1"
            cur.execute(query, (report_id,))
            row = cur.fetchone()
            if not row:
                return None
            val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
            return json.loads(val) if isinstance(val, str) else val

    # =========================================================================
    # Physician Reviews
    # =========================================================================

    def save_review(self, review: PhysicianReview) -> str:
        """Persists a physician review and associates it with the clinical report."""
        is_pg = self.manager.engine_type == "postgresql"
        raw_json_str = review.model_dump_json()

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO physician_reviews (
                        id, report_id, encounter_id, physician_name, overall_score,
                        approved, reviewed_at, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        overall_score = EXCLUDED.overall_score,
                        approved = EXCLUDED.approved,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (
                        review.id, review.report_id, review.encounter_id, review.physician_name,
                        review.overall_score, review.approved, review.reviewed_at, raw_json_str
                    )
                )
                cur.execute(
                    "UPDATE encounters SET review_id = %s WHERE encounter_id = %s;",
                    (review.id, review.encounter_id)
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO physician_reviews (
                        id, report_id, encounter_id, physician_name, overall_score,
                        approved, reviewed_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        review.id, review.report_id, review.encounter_id, review.physician_name,
                        review.overall_score, review.approved, review.reviewed_at.isoformat(),
                        raw_json_str
                    )
                )
                cur.execute(
                    "UPDATE encounters SET review_id = ? WHERE encounter_id = ?;",
                    (review.id, review.encounter_id)
                )
            logger.info(f"Physician review {review.id} saved to {self.manager.engine_type} database.")
            return review.id

    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT raw_json FROM physician_reviews WHERE id = %s" if is_pg else "SELECT raw_json FROM physician_reviews WHERE id = ?"
            cur.execute(query, (review_id,))
            row = cur.fetchone()
            if not row:
                return None
            val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
            return json.loads(val) if isinstance(val, str) else val

    def get_review_model(self, review_id: str) -> Optional[PhysicianReview]:
        data = self.get_review(review_id)
        if not data:
            return None
        return PhysicianReview.model_validate(data)

    def get_review_for_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT raw_json FROM physician_reviews WHERE report_id = %s" if is_pg else "SELECT raw_json FROM physician_reviews WHERE report_id = ?"
            cur.execute(query, (report_id,))
            row = cur.fetchone()
            if not row:
                return None
            val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
            return json.loads(val) if isinstance(val, str) else val

    def list_reviews(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT raw_json FROM physician_reviews ORDER BY reviewed_at DESC LIMIT %s OFFSET %s" if is_pg else "SELECT raw_json FROM physician_reviews ORDER BY reviewed_at DESC LIMIT ? OFFSET ?"
            cur.execute(query, (limit, offset))
            rows = cur.fetchall()
            results = []
            for row in rows:
                val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
                results.append(json.loads(val) if isinstance(val, str) else val)
            return results

    def count_reviews(self) -> int:
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM physician_reviews;")
            res = cur.fetchone()
            return res[0] if res else 0

    # =========================================================================
    # Training Dataset Records (Provenance & Deduplication Linked)
    # =========================================================================

    def save_training_dataset_record(self, record: TrainingDatasetRecord) -> str:
        """
        Persists an immutable, provenance-linked training dataset record holding all 13
        lifecycle fields for model training dataset compilation.
        """
        is_pg = self.manager.engine_type == "postgresql"
        data = record.model_dump() if hasattr(record, "model_dump") else dict(record)
        raw_json_str = json.dumps(data, default=str)
        orig_input_str = json.dumps(data.get("original_input", {}), default=str)
        orig_output_str = json.dumps(data.get("original_ai_output", {}), default=str)
        reviewer_fb_str = json.dumps(data.get("reviewer_feedback", {}), default=str)
        corrected_out_str = json.dumps(data.get("corrected_output", {}), default=str)
        provenance_str = json.dumps(data.get("provenance", {}), default=str)
        ts_str = data.get("timestamp")
        if isinstance(ts_str, datetime):
            ts_str = ts_str.isoformat()
        elif not ts_str:
            ts_str = datetime.now(timezone.utc).isoformat()

        eligibility_val = (
            record.dataset_eligibility.value
            if hasattr(record.dataset_eligibility, "value")
            else str(record.dataset_eligibility)
        )

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO training_dataset_records (
                        id, case_id, patient_id, report_id, model_version, specialty,
                        review_status, dataset_eligibility, original_input,
                        original_ai_output, reviewer_feedback, corrected_output,
                        provenance, timestamp, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        review_status = EXCLUDED.review_status,
                        dataset_eligibility = EXCLUDED.dataset_eligibility,
                        reviewer_feedback = EXCLUDED.reviewer_feedback,
                        corrected_output = EXCLUDED.corrected_output,
                        provenance = EXCLUDED.provenance,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (
                        record.id, record.case_id, record.patient_id, record.report_id,
                        record.model_version, record.specialty, record.review_status,
                        eligibility_val, orig_input_str, orig_output_str, reviewer_fb_str,
                        corrected_out_str, provenance_str, ts_str, raw_json_str
                    )
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO training_dataset_records (
                        id, case_id, patient_id, report_id, model_version, specialty,
                        review_status, dataset_eligibility, original_input,
                        original_ai_output, reviewer_feedback, corrected_output,
                        provenance, timestamp, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        record.id, record.case_id, record.patient_id, record.report_id,
                        record.model_version, record.specialty, record.review_status,
                        eligibility_val, orig_input_str, orig_output_str, reviewer_fb_str,
                        corrected_out_str, provenance_str, ts_str, raw_json_str
                    )
                )
        logger.info(f"Training dataset record {record.id} saved (Eligibility: {eligibility_val}).")
        return record.id

    def get_training_dataset_records(self, eligibility: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves training dataset records with optional eligibility filter."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if eligibility:
                query = (
                    "SELECT raw_json FROM training_dataset_records WHERE dataset_eligibility = %s ORDER BY timestamp DESC"
                    if is_pg
                    else "SELECT raw_json FROM training_dataset_records WHERE dataset_eligibility = ? ORDER BY timestamp DESC"
                )
                cur.execute(query, (eligibility,))
            else:
                query = "SELECT raw_json FROM training_dataset_records ORDER BY timestamp DESC"
                cur.execute(query)
            rows = cur.fetchall()
            results = []
            for row in rows:
                val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
                results.append(json.loads(val) if isinstance(val, str) else val)
            return results

    def is_patient_case_reviewed(self, patient_id: str, case_id: str) -> bool:
        """Checks if a given patient/case has already been processed into the training dataset."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = (
                "SELECT COUNT(*) FROM training_dataset_records WHERE patient_id = %s AND case_id = %s AND dataset_eligibility = 'ELIGIBLE'"
                if is_pg
                else "SELECT COUNT(*) FROM training_dataset_records WHERE patient_id = ? AND case_id = ? AND dataset_eligibility = 'ELIGIBLE'"
            )
            cur.execute(query, (patient_id, case_id))
            res = cur.fetchone()
            count = res[0] if res else 0
            return count > 0

    # =========================================================================
    # DPO / Preference Learning Pairs
    # =========================================================================

    def save_dpo_pair(self, pair: Any) -> str:
        """Persists a DPO training pair into the feedback repository."""
        is_pg = self.manager.engine_type == "postgresql"
        pair_id = getattr(pair, "id", f"DPO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
        raw_json_str = pair.model_dump_json() if hasattr(pair, "model_dump_json") else json.dumps(pair)

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO dpo_feedback_pairs (
                        id, prompt, chosen, rejected, reward_margin, is_safety_critical,
                        source, encounter_id, case_id, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    (
                        pair_id, pair.prompt, pair.chosen, pair.rejected, pair.reward_margin,
                        pair.is_safety_critical, getattr(pair, "source", "HUMAN_PHYSICIAN"),
                        getattr(pair, "encounter_id", None), getattr(pair, "case_id", None),
                        raw_json_str
                    )
                )
            else:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO dpo_feedback_pairs (
                        id, prompt, chosen, rejected, reward_margin, is_safety_critical,
                        source, encounter_id, case_id, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        pair_id, pair.prompt, pair.chosen, pair.rejected, pair.reward_margin,
                        pair.is_safety_critical, getattr(pair, "source", "HUMAN_PHYSICIAN"),
                        getattr(pair, "encounter_id", None), getattr(pair, "case_id", None),
                        raw_json_str
                    )
                )
            return pair_id

    def list_dpo_pairs(self) -> List[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT raw_json FROM dpo_feedback_pairs ORDER BY created_at DESC;")
            rows = cur.fetchall()
            pairs = []
            for row in rows:
                val = row["raw_json"] if isinstance(row, dict) or hasattr(row, "keys") else row[0]
                pairs.append(json.loads(val) if isinstance(val, str) else val)
            return pairs

    # =========================================================================
    # Knowledge Chunks & Vector Embeddings
    # =========================================================================

    def save_knowledge_chunk(
        self,
        chunk_id: str,
        specialty: str,
        book_title: str,
        chapter: str,
        topic: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Stores a medical knowledge chunk with optional embedding vector."""
        is_pg = self.manager.engine_type == "postgresql"
        emb_data = embedding if is_pg and self.manager.pgvector_enabled else (json.dumps(embedding) if embedding else None)
        meta_json = json.dumps(metadata or {})

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content;
                    """,
                    (chunk_id, specialty, book_title, chapter, topic, content, emb_data, meta_json)
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (chunk_id, specialty, book_title, chapter, topic, content, emb_data, meta_json)
                )
            return chunk_id

    def batch_save_knowledge_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Batch inserts or replaces medical knowledge chunks for high throughput."""
        if not chunks:
            return 0
        is_pg = self.manager.engine_type == "postgresql"
        rows = []
        for c in chunks:
            chunk_id = c["id"]
            specialty = c.get("specialty", "Internal Medicine")
            book_title = c.get("book_title") or c.get("book", "Harrison's Principles of Internal Medicine, 21st Edition (2022)")
            chapter = c.get("chapter", "Harrison's Internal Medicine")
            topic = c.get("topic", "")
            content = c.get("content") or c.get("text", "")
            embedding = c.get("embedding")
            emb_data = embedding if is_pg and self.manager.pgvector_enabled else (json.dumps(embedding) if embedding else None)
            metadata = c.get("metadata") or {
                "page": c.get("page"),
                "chapter": chapter,
                "topic": topic,
            }
            meta_json = json.dumps(metadata)
            rows.append((chunk_id, specialty, book_title, chapter, topic, content, emb_data, meta_json))

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.executemany(
                    """
                    INSERT INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata;
                    """,
                    rows
                )
            else:
                cur.executemany(
                    """
                    INSERT OR REPLACE INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    rows
                )
            conn.commit()
            return len(rows)

    @staticmethod
    def compute_embedding(text: str, dim: int = 128) -> List[float]:
        """Computes a normalized dense semantic representation for medical text retrieval."""
        import re
        import math
        tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text.lower())
        vec = [0.0] * dim
        if not tokens:
            return vec

        for token in tokens:
            if len(token) <= 2:
                continue
            idx = abs(hash(token)) % dim
            sign = 1.0 if (abs(hash(token + "_sign")) % 2 == 0) else -1.0
            weight = math.log(1.0 + len(token))
            vec[idx] += sign * weight

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    def search_knowledge_chunks(
        self,
        query: str,
        specialty: Optional[str] = None,
        book_title: Optional[str] = None,
        top_k: int = 5,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs high-performance semantic vector and lexical retrieval over medical knowledge chunks.
        Supports native pgvector on PostgreSQL and fast candidate pre-filtering on SQLite.
        """
        import math
        import re
        q_vec = query_vector if (query_vector is not None and len(query_vector) > 0) else self.compute_embedding(query)
        q_tokens = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", query.lower()))
        is_pg = self.manager.engine_type == "postgresql"

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg and self.manager.pgvector_enabled:
                emb_str = f"[{','.join(str(x) for x in q_vec)}]"
                where_pg = []
                params_pg = [emb_str]
                if specialty and specialty.strip() and specialty.upper() != "ALL":
                    where_pg.append("specialty = %s")
                    params_pg.append(specialty.strip())
                if book_title and book_title.strip() and book_title.upper() != "ALL":
                    where_pg.append("book_title ILIKE %s")
                    params_pg.append(f"%{book_title.strip()}%")

                where_sql = f"WHERE {' AND '.join(where_pg)}" if where_pg else ""
                cur.execute(
                    f"""
                    SELECT id, specialty, book_title, chapter, topic, content, metadata,
                           (1.0 - (embedding <=> %s::vector)) AS score
                    FROM knowledge_chunks
                    {where_sql}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    tuple(params_pg + [emb_str, top_k])
                )
                rows = cur.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if isinstance(item.get("metadata"), str):
                        try:
                            item["metadata"] = json.loads(item["metadata"])
                        except Exception:
                            pass
                    results.append(item)
                return results

            # SQLite or standard fallback with fast candidate retrieval
            where_base = []
            params_base = []
            if specialty and specialty.strip() and specialty.upper() != "ALL":
                where_base.append("specialty = ?")
                params_base.append(specialty.strip())
            if book_title and book_title.strip() and book_title.upper() != "ALL":
                where_base.append("book_title LIKE ?")
                params_base.append(f"%{book_title.strip()}%")

            # Extract significant query words for candidate matching
            sig_words = [w for w in q_tokens if len(w) > 2]
            candidate_rows = []
            
            if sig_words:
                like_clauses = []
                candidate_params = list(params_base)
                for w in sig_words[:6]:
                    like_clauses.append("(topic LIKE ? OR content LIKE ? OR chapter LIKE ?)")
                    candidate_params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
                
                comb_where = list(where_base)
                if like_clauses:
                    comb_where.append(f"({' OR '.join(like_clauses)})")
                
                where_str = f"WHERE {' AND '.join(comb_where)}" if comb_where else ""
                cur.execute(
                    f"SELECT id, specialty, book_title, chapter, topic, content, embedding, metadata FROM knowledge_chunks {where_str} LIMIT 300;",
                    tuple(candidate_params)
                )
                candidate_rows = cur.fetchall()

            # Fallback if no lexical candidate match found (e.g. abbreviations/synonyms)
            if not candidate_rows:
                where_str = f"WHERE {' AND '.join(where_base)}" if where_base else ""
                cur.execute(
                    f"SELECT id, specialty, book_title, chapter, topic, content, embedding, metadata FROM knowledge_chunks {where_str} LIMIT 250;",
                    tuple(params_base)
                )
                candidate_rows = cur.fetchall()

            scored = []
            for r in candidate_rows:
                row_dict = dict(r)
                emb_raw = row_dict.pop("embedding", None)
                chunk_emb = json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw

                # Cosine similarity (dot product of L2 normalized vectors)
                sim = 0.0
                if chunk_emb and len(chunk_emb) == len(q_vec):
                    sim = sum(a * b for a, b in zip(q_vec, chunk_emb))

                # Topic token matching boost
                topic_tokens = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", row_dict.get("topic", "").lower()))
                topic_overlap = len(q_tokens.intersection(topic_tokens)) / max(len(topic_tokens), 1) if topic_tokens else 0.0

                # Keyword lexical overlap boost in chapter and content
                content_tokens = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", (row_dict.get("chapter", "") + " " + row_dict.get("content", "")).lower()))
                content_overlap = len(q_tokens.intersection(content_tokens)) / max(len(q_tokens), 1) if q_tokens else 0.0

                composite_score = round(0.40 * max(sim, 0.0) + 0.35 * topic_overlap + 0.25 * content_overlap, 4)

                meta = row_dict.get("metadata")
                if isinstance(meta, str):
                    try:
                        row_dict["metadata"] = json.loads(meta)
                    except Exception:
                        pass

                row_dict["score"] = composite_score
                scored.append(row_dict)

            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]

    def count_knowledge_chunks(self) -> int:
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM knowledge_chunks;")
            res = cur.fetchone()
            return res[0] if res else 0

    def get_knowledge_books_summary(self) -> Dict[str, Any]:
        """Returns statistics and metadata breakdown for all medical knowledge textbooks."""
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT book_title, specialty, COUNT(*) as total_chunks, COUNT(DISTINCT chapter) as total_chapters
                FROM knowledge_chunks
                GROUP BY book_title, specialty
                ORDER BY total_chunks DESC;
            """)
            rows = cur.fetchall()
            books = []
            total_chunks = 0
            for r in rows:
                row_dict = dict(r)
                cnt = row_dict["total_chunks"]
                total_chunks += cnt
                title = row_dict["book_title"]
                spec = row_dict["specialty"]

                # Fetch 2 sample chunks for preview
                cur.execute("""
                    SELECT id, chapter, topic, substr(content, 1, 280) as excerpt
                    FROM knowledge_chunks
                    WHERE book_title = ?
                    LIMIT 2;
                """, (title,))
                samples = [dict(s) for s in cur.fetchall()]

                # Generate clean identifier
                slug = (
                    title.lower()
                    .replace(" ", "-")
                    .replace("'", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace(":", "")
                    .replace(",", "")
                )

                books.append({
                    "id": slug,
                    "title": title,
                    "specialty": spec,
                    "chunk_count": cnt,
                    "chapter_count": row_dict.get("total_chapters", 0),
                    "status": "ACTIVE",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "embedding_dim": 384,
                    "sample_chunks": samples,
                })

            return {
                "total_chunks": total_chunks,
                "total_books": len(books),
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dim": 384,
                "books": books,
            }

    def list_knowledge_chunks(
        self,
        book_title: Optional[str] = None,
        specialty: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        search_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lists vector chunks with metadata and preview vector values for inspection."""
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            where_clauses = []
            params = []
            if book_title and book_title.strip() and book_title.upper() != "ALL":
                where_clauses.append("book_title LIKE ?")
                params.append(f"%{book_title.strip()}%")
            if specialty and specialty.strip() and specialty.upper() != "ALL":
                where_clauses.append("specialty = ?")
                params.append(specialty.strip())
            if search_query and search_query.strip():
                where_clauses.append("(topic LIKE ? OR content LIKE ? OR chapter LIKE ?)")
                sq = f"%{search_query.strip()}%"
                params.extend([sq, sq, sq])

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Count total matching
            cur.execute(f"SELECT COUNT(*) FROM knowledge_chunks {where_sql};", tuple(params))
            cnt_row = cur.fetchone()
            total = cnt_row[0] if cnt_row else 0

            # Fetch paginated rows
            cur.execute(
                f"""
                SELECT id, specialty, book_title, chapter, topic, content, embedding, metadata
                FROM knowledge_chunks
                {where_sql}
                ORDER BY id ASC
                LIMIT ? OFFSET ?;
                """,
                tuple(params + [min(max(limit, 1), 100), max(offset, 0)])
            )
            rows = cur.fetchall()

            chunks = []
            for r in rows:
                row_dict = dict(r)
                emb_raw = row_dict.pop("embedding", None)
                chunk_emb = json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw
                vector_preview = []
                if isinstance(chunk_emb, list) and len(chunk_emb) > 0:
                    vector_preview = [round(float(v), 4) for v in chunk_emb[:5]]

                meta = row_dict.get("metadata")
                if isinstance(meta, str):
                    try:
                        row_dict["metadata"] = json.loads(meta)
                    except Exception:
                        pass

                row_dict["vector_preview"] = vector_preview
                row_dict["vector_dim"] = len(chunk_emb) if isinstance(chunk_emb, list) else 384
                row_dict["char_length"] = len(row_dict.get("content", ""))
                chunks.append(row_dict)

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "chunks": chunks,
            }

    # =========================================================================
    # Patient Case Intake & Admission Repository
    # =========================================================================

    def admit_patient(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts an incoming clinical case or manual intake form into an admitted
        patient record with deterministic MRN, department assignment, and bed allocation.
        Enforces patient-level deduplication to prevent duplicate admissions.
        """
        name = case_data.get("name", "Unknown Patient").strip()
        age = int(case_data.get("age", 50))
        sex = case_data.get("sex", "Unknown").strip()

        # Deterministic MRN generation if not explicitly provided
        if not case_data.get("mrn"):
            identity_key = f"{name.lower()}|{age}|{sex.lower()}"
            hash_digest = hashlib.sha256(identity_key.encode("utf-8")).hexdigest()[:6].upper()
            mrn = f"MRN-{hash_digest}"
        else:
            mrn = case_data["mrn"]

        patient_id = case_data.get("id") or f"PAT-{mrn.replace('MRN-', '')}"

        # Deduplication check: if patient already admitted and active, return existing record
        existing = self.get_patient(mrn)
        if existing and existing.get("admission_status") != "DISCHARGED":
            logger.info(f"Patient {name} (MRN: {mrn}) is already active in census. Returning existing record.")
            return existing

        acuity = case_data.get("triage_acuity", "URGENT")
        complaint = case_data.get("chief_complaint", "Undifferentiated clinical presentation")
        department = case_data.get("assigned_department", "EMERGENCY")
        bed = case_data.get("bed_number") or f"{department[:3]}-BAY-01"
        admitted_at = datetime.now(timezone.utc)
        raw_json_str = json.dumps(case_data)

        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO patients (
                        id, mrn, name, age, sex, triage_acuity, chief_complaint,
                        admission_status, assigned_department, bed_number, admitted_at, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        admission_status = EXCLUDED.admission_status,
                        assigned_department = EXCLUDED.assigned_department,
                        bed_number = EXCLUDED.bed_number,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (
                        patient_id, mrn, name, age, sex, acuity, complaint,
                        "ADMITTED", department, bed, admitted_at, raw_json_str
                    )
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO patients (
                        id, mrn, name, age, sex, triage_acuity, chief_complaint,
                        admission_status, assigned_department, bed_number, admitted_at, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        patient_id, mrn, name, age, sex, acuity, complaint,
                        "ADMITTED", department, bed, admitted_at.isoformat(), raw_json_str
                    )
                )

        logger.info(f"Admitted patient {name} (ID: {patient_id}, MRN: {mrn}) to {department} {bed}.")
        return {
            "id": patient_id,
            "mrn": mrn,
            "name": name,
            "age": age,
            "sex": sex,
            "triage_acuity": acuity,
            "chief_complaint": complaint,
            "admission_status": "ADMITTED",
            "assigned_department": department,
            "bed_number": bed,
            "admitted_at": admitted_at.isoformat(),
            "case_data": case_data,
        }

    # =========================================================================
    # Case Pool Repository
    # =========================================================================

    def save_case_to_pool(self, case_item: Dict[str, Any]) -> str:
        """Stores a structured clinical case into the unadmitted Case Pool."""
        case_id = case_item.get("id") or f"POOL-{uuid.uuid4().hex[:8].upper()}"
        name = case_item.get("name", "Unknown Case")
        age = int(case_item.get("age", 50))
        sex = case_item.get("sex", "Unknown")
        acuity = str(case_item.get("triage_acuity", "URGENT"))
        complaint = case_item.get("chief_complaint", "Undifferentiated clinical presentation")
        specialty = case_item.get("specialty_category", "INTERNAL_MEDICINE")
        source = case_item.get("source", "SYNTHEA")
        diff_level = int(case_item.get("difficulty_level", 1))
        status = case_item.get("status", "UNADMITTED")
        raw_json_str = json.dumps(case_item)

        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO case_pool (
                        id, name, age, sex, triage_acuity, chief_complaint,
                        specialty_category, source, difficulty_level, status, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        triage_acuity = EXCLUDED.triage_acuity,
                        chief_complaint = EXCLUDED.chief_complaint,
                        specialty_category = EXCLUDED.specialty_category,
                        difficulty_level = EXCLUDED.difficulty_level,
                        status = EXCLUDED.status,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (case_id, name, age, sex, acuity, complaint, specialty, source, diff_level, status, raw_json_str)
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO case_pool (
                        id, name, age, sex, triage_acuity, chief_complaint,
                        specialty_category, source, difficulty_level, status, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (case_id, name, age, sex, acuity, complaint, specialty, source, diff_level, status, raw_json_str)
                )
        return case_id

    def list_pool_cases(
        self,
        status: Optional[str] = "UNADMITTED",
        specialty: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Lists cases in the Case Pool, filterable by status and specialty."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM case_pool"
            params: List[Any] = []
            conditions: List[str] = []
            if status:
                conditions.append("status = %s" if is_pg else "status = ?")
                params.append(status)
            if specialty:
                conditions.append("specialty_category = %s" if is_pg else "specialty_category = ?")
                params.append(specialty)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY created_at DESC"
            query += " LIMIT %s OFFSET %s" if is_pg else " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                if "raw_json" in d and isinstance(d["raw_json"], str):
                    try:
                        d["case_details"] = json.loads(d.pop("raw_json"))
                    except Exception:
                        pass
                results.append(d)
            return results

    def get_pool_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single case from the Case Pool by ID."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM case_pool WHERE id = %s" if is_pg else "SELECT * FROM case_pool WHERE id = ?"
            cur.execute(query, (case_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            if "raw_json" in d and isinstance(d["raw_json"], str):
                try:
                    d["case_details"] = json.loads(d.pop("raw_json"))
                except Exception:
                    pass
            return d

    def update_pool_case_status(self, case_id: str, status: str) -> bool:
        """Updates case status in the pool (e.g. UNADMITTED -> ADMITTED)."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "UPDATE case_pool SET status = %s WHERE id = %s" if is_pg else "UPDATE case_pool SET status = ? WHERE id = ?"
            cur.execute(query, (status, case_id))
            return cur.rowcount > 0

    def count_pool_cases(self, status: Optional[str] = None) -> int:
        """Counts cases in the Case Pool."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT COUNT(*) FROM case_pool"
            params: List[Any] = []
            if status:
                query += " WHERE status = %s" if is_pg else " WHERE status = ?"
                params.append(status)
            cur.execute(query, tuple(params))
            res = cur.fetchone()
            return res[0] if res else 0

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM patients WHERE id = %s OR mrn = %s" if is_pg else "SELECT * FROM patients WHERE id = ? OR mrn = ?"
            cur.execute(query, (patient_id, patient_id))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            if "raw_json" in d and isinstance(d["raw_json"], str):
                try:
                    d["case_data"] = json.loads(d.pop("raw_json"))
                except Exception:
                    pass
            return d

    def list_patients(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if status:
                query = "SELECT * FROM patients WHERE admission_status = %s ORDER BY admitted_at DESC LIMIT %s OFFSET %s" if is_pg else "SELECT * FROM patients WHERE admission_status = ? ORDER BY admitted_at DESC LIMIT ? OFFSET ?"
                cur.execute(query, (status, limit, offset))
            else:
                query = "SELECT * FROM patients ORDER BY admitted_at DESC LIMIT %s OFFSET %s" if is_pg else "SELECT * FROM patients ORDER BY admitted_at DESC LIMIT ? OFFSET ?"
                cur.execute(query, (limit, offset))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                if "raw_json" in d and isinstance(d["raw_json"], str):
                    try:
                        d["case_data"] = json.loads(d.pop("raw_json"))
                    except Exception:
                        pass
                results.append(d)
            return results

    def discharge_patient(self, patient_id: str) -> bool:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = (
                "UPDATE patients SET admission_status = 'DISCHARGED', bed_number = NULL WHERE (id = %s OR mrn = %s) AND admission_status != 'DISCHARGED'"
                if is_pg
                else "UPDATE patients SET admission_status = 'DISCHARGED', bed_number = NULL WHERE (id = ? OR mrn = ?) AND admission_status != 'DISCHARGED'"
            )
            cur.execute(query, (patient_id, patient_id))
            return cur.rowcount > 0

    def count_patients(self, status: Optional[str] = None) -> int:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if status:
                query = "SELECT COUNT(*) FROM patients WHERE admission_status = %s;" if is_pg else "SELECT COUNT(*) FROM patients WHERE admission_status = ?;"
                cur.execute(query, (status,))
            else:
                cur.execute("SELECT COUNT(*) FROM patients;")
            res = cur.fetchone()
            return res[0] if res else 0

    def seed_default_admitted_patients(self) -> int:
        """
        Seeds canonical admitted patient records into the patients table if no admitted
        patients currently exist. This guarantees that real-time clinical triage testing
        always has officially admitted patients with complete EHR charts (vitals, labs,
        imaging, department and bed numbers), while strictly setting admission_status = 'ADMITTED'.
        """
        if self.count_patients(status="ADMITTED") > 0:
            return 0

        canonical_patients = [
            {
                "id": "PAT-8921-OB",
                "mrn": "VH-8921-OB",
                "name": "Elena Vance",
                "age": 32,
                "sex": "Female",
                "triage_acuity": "EMERGENT",
                "chief_complaint": "Severe throbbing frontal headache, blurred vision with floaters, sharp right upper quadrant pain.",
                "history_of_present_illness": "32-year-old female at 34+2 weeks gestation presenting with acute-onset severe headache unresponsive to acetaminophen, persistent scotomas, and worsening RUQ pain over the past 6 hours.",
                "assigned_department": "OBSTETRICS",
                "bed_number": "OB-BAY-01",
                "past_medical_history": ["Nulliparous until current gestation", "Gestational hypertension diagnosed at 28 weeks"],
                "medications": ["Prenatal multivitamins", "Labetalol 100mg PO BID"],
                "allergies": ["Sulfa drugs (hives)"],
                "baseline_vitals": {
                    "heart_rate": 88,
                    "systolic_bp": 178,
                    "diastolic_bp": 112,
                    "respiratory_rate": 18,
                    "temperature_c": 36.8,
                    "spo2_percent": 98.0,
                    "pain_score": 7
                },
                "labs": [
                    {"name": "Platelets", "val": "62 ×10⁹/L", "ref": "150-400", "flag": "Low", "status": "low"},
                    {"name": "AST / ALT", "val": "210 / 195 U/L", "ref": "<35", "flag": "High", "status": "high"},
                    {"name": "LDH", "val": "680 U/L", "ref": "140-280", "flag": "High", "status": "high"},
                    {"name": "Urine PCR", "val": "1.8 mg/mg", "ref": "<0.3", "flag": "High", "status": "high"}
                ],
                "imaging": [
                    {
                        "title": "Bedside RUQ Ultrasound",
                        "mod": "POCUS Scan",
                        "desc": "Liver capsule intact, no subcapsular haematoma; gallbladder normal",
                        "icon": "scan",
                        "modalText": "<b>Findings:</b> Homogeneous liver parenchyma without subcapsular fluid collection or hematoma."
                    }
                ],
                "presumptive_diagnosis": "Preeclampsia with severe features complicated by HELLP syndrome"
            },
            {
                "id": "PAT-3391-CCU",
                "mrn": "VH-3391-CCU",
                "name": "Arthur Pendelton",
                "age": 64,
                "sex": "Male",
                "triage_acuity": "RESUSCITATION",
                "chief_complaint": "Crushing substernal chest pressure radiating to left jaw, diaphoresis, dyspnea at rest.",
                "history_of_present_illness": "64-year-old male with heavy retrosternal chest pain radiating to left arm and neck for 90 minutes. Diaphoretic, pale, cold extremities.",
                "assigned_department": "CARDIOLOGY",
                "bed_number": "CCU-BAY-03",
                "past_medical_history": ["Hypertension", "Hyperlipidemia", "Type 2 Diabetes"],
                "medications": ["Atorvastatin 40mg", "Metformin 1000mg BID", "Lisinopril 20mg"],
                "allergies": ["NKDA"],
                "baseline_vitals": {
                    "heart_rate": 112,
                    "systolic_bp": 82,
                    "diastolic_bp": 54,
                    "respiratory_rate": 26,
                    "temperature_c": 36.4,
                    "spo2_percent": 91.0,
                    "pain_score": 9
                },
                "labs": [
                    {"name": "Troponin I", "val": "14.2 ng/mL", "ref": "<0.04", "flag": "Critical", "status": "critical"},
                    {"name": "BNP", "val": "1420 pg/mL", "ref": "<100", "flag": "High", "status": "high"},
                    {"name": "Lactate", "val": "3.8 mmol/L", "ref": "0.5-2.0", "flag": "High", "status": "high"}
                ],
                "imaging": [
                    {
                        "title": "12-Lead ECG",
                        "mod": "Cardiology Panel",
                        "desc": "Marked ST elevations in V1-V4 with reciprocal depressions in II, III, aVF",
                        "icon": "ecg",
                        "modalText": "<b>Findings:</b> Hyperacute anterolateral STEMI with cardiogenic shock signs."
                    }
                ],
                "presumptive_diagnosis": "Acute anterolateral STEMI with cardiogenic shock"
            },
            {
                "id": "PAT-4102-ICU",
                "mrn": "VH-4102-ICU",
                "name": "Marcus Holloway",
                "age": 58,
                "sex": "Male",
                "triage_acuity": "RESUSCITATION",
                "chief_complaint": "High fevers, rigors, progressive confusion, productive cough with rust-colored sputum.",
                "history_of_present_illness": "58-year-old male with 4-day history of worsening cough and fever, acutely decompensating over 8 hours with altered mental status and hypotension refractory to fluid bolus.",
                "assigned_department": "EMERGENCY",
                "bed_number": "ICU-BAY-02",
                "past_medical_history": ["COPD", "Former smoker (35 pack-years)"],
                "medications": ["Tiotropium inhaler", "Albuterol PRN"],
                "allergies": ["Penicillin (anaphylaxis)"],
                "baseline_vitals": {
                    "heart_rate": 128,
                    "systolic_bp": 78,
                    "diastolic_bp": 46,
                    "respiratory_rate": 32,
                    "temperature_c": 39.4,
                    "spo2_percent": 88.0,
                    "pain_score": 4
                },
                "labs": [
                    {"name": "WBC Count", "val": "24.6 ×10⁹/L", "ref": "4.5-11.0", "flag": "High", "status": "high"},
                    {"name": "Lactate", "val": "4.6 mmol/L", "ref": "0.5-2.0", "flag": "Critical", "status": "critical"},
                    {"name": "Procalcitonin", "val": "18.4 ng/mL", "ref": "<0.1", "flag": "High", "status": "high"}
                ],
                "imaging": [
                    {
                        "title": "Portable Chest Radiograph",
                        "mod": "Radiology",
                        "desc": "Dense right lower lobe cavitary consolidation with air bronchograms",
                        "icon": "scan",
                        "modalText": "<b>Findings:</b> Severe necrotizing pneumonia suspicious for MRSA."
                    }
                ],
                "presumptive_diagnosis": "Septic shock secondary to severe MRSA pneumonia"
            },
            {
                "id": "PAT-7742-NEURO",
                "mrn": "VH-7742-NEURO",
                "name": "Diana Reyes",
                "age": 71,
                "sex": "Female",
                "triage_acuity": "RESUSCITATION",
                "chief_complaint": "Acute right-sided hemiplegia, expressive aphasia, right facial droop noted 75 minutes ago.",
                "history_of_present_illness": "71-year-old female witnessed by daughter developing sudden loss of speech and dense right-sided paralysis at breakfast. Last known normal 75 minutes prior to ED presentation.",
                "assigned_department": "NEUROLOGY",
                "bed_number": "STROKE-BAY-01",
                "past_medical_history": ["Atrial fibrillation", "Hypertension"],
                "medications": ["Apixaban 5mg BID", "Amlodipine 10mg"],
                "allergies": ["NKDA"],
                "baseline_vitals": {
                    "heart_rate": 94,
                    "systolic_bp": 186,
                    "diastolic_bp": 104,
                    "respiratory_rate": 18,
                    "temperature_c": 36.9,
                    "spo2_percent": 97.0,
                    "pain_score": 0
                },
                "labs": [
                    {"name": "Blood Glucose", "val": "6.1 mmol/L", "ref": "4.0-7.0", "flag": "Normal", "status": "normal"},
                    {"name": "INR", "val": "1.2", "ref": "0.9-1.2", "flag": "Normal", "status": "normal"},
                    {"name": "Platelets", "val": "220 ×10⁹/L", "ref": "150-400", "flag": "Normal", "status": "normal"}
                ],
                "imaging": [
                    {
                        "title": "Non-Contrast Head CT & CTA",
                        "mod": "Neuro-Radiology",
                        "desc": "Hyperdense left MCA sign, ASPECTS 8, CTA confirms left M1 occlusion",
                        "icon": "scan",
                        "modalText": "<b>Findings:</b> Acute left MCA large vessel occlusion eligible for mechanical thrombectomy."
                    }
                ],
                "presumptive_diagnosis": "Acute ischemic stroke with left MCA large vessel occlusion (LVO)"
            },
            {
                "id": "PAT-1904-SURG",
                "mrn": "VH-1904-SURG",
                "name": "Liam Chen",
                "age": 26,
                "sex": "Male",
                "triage_acuity": "EMERGENT",
                "chief_complaint": "Periumbilical abdominal pain migrating to right lower quadrant, anorexia, nausea, fever.",
                "history_of_present_illness": "26-year-old male with 18 hours of continuous abdominal pain starting periumbilically and localizing to McBurney's point. Positive Rovsing and psoas signs on exam.",
                "assigned_department": "SURGERY",
                "bed_number": "SURG-BAY-04",
                "past_medical_history": ["None"],
                "medications": ["None"],
                "allergies": ["NKDA"],
                "baseline_vitals": {
                    "heart_rate": 104,
                    "systolic_bp": 126,
                    "diastolic_bp": 78,
                    "respiratory_rate": 20,
                    "temperature_c": 38.3,
                    "spo2_percent": 99.0,
                    "pain_score": 8
                },
                "labs": [
                    {"name": "WBC Count", "val": "16.8 ×10⁹/L", "ref": "4.5-11.0", "flag": "High", "status": "high"},
                    {"name": "Neutrophils %", "val": "86%", "ref": "40-70", "flag": "High", "status": "high"},
                    {"name": "CRP", "val": "48 mg/L", "ref": "<5", "flag": "High", "status": "high"}
                ],
                "imaging": [
                    {
                        "title": "Abdominal Ultrasound & CT",
                        "mod": "Surgical Imaging",
                        "desc": "Non-compressible, dilated appendix (9mm) with appendicolith and periappendiceal fat stranding",
                        "icon": "scan",
                        "modalText": "<b>Findings:</b> Acute uncomplicated suppurative appendicitis requiring laparoscopic appendectomy."
                    }
                ],
                "presumptive_diagnosis": "Acute suppurative appendicitis with localized peritonitis"
            }
        ]

        count = 0
        for p in canonical_patients:
            self.admit_patient(p)
            count += 1
        logger.info(f"Seeded {count} canonical admitted patients into hospital wards.")
        return count

    # =========================================================================
    # Hospital Staff Management
    # =========================================================================

    def add_staff_member(self, staff: Dict[str, Any]) -> str:
        staff_id = staff.get("id") or f"STAFF-{staff.get('name', 'USER').replace(' ', '').upper()[:8]}"
        name = staff.get("name", "Medical Officer")
        role = staff.get("role", "DOCTOR")
        specialty = staff.get("specialty", "GENERAL_MEDICINE")
        title = staff.get("title", "Clinical Specialist")
        department = staff.get("department", "INTERNAL_MEDICINE")
        status = staff.get("status", "ON_DUTY")
        credentials = staff.get("credentials", "MD")
        raw_json_str = json.dumps(staff)

        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO hospital_staff (id, name, role, specialty, title, department, status, credentials, raw_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        department = EXCLUDED.department,
                        status = EXCLUDED.status,
                        raw_json = EXCLUDED.raw_json;
                    """,
                    (staff_id, name, role, specialty, title, department, status, credentials, raw_json_str)
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO hospital_staff (id, name, role, specialty, title, department, status, credentials, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (staff_id, name, role, specialty, title, department, status, credentials, raw_json_str)
                )
        logger.info(f"Staff member {name} ({title}) updated in database.")
        return staff_id

    def get_staff_member(self, staff_id: str) -> Optional[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM hospital_staff WHERE id = %s" if is_pg else "SELECT * FROM hospital_staff WHERE id = ?"
            cur.execute(query, (staff_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            extra = {}
            if "raw_json" in d and isinstance(d["raw_json"], str):
                try:
                    extra = json.loads(d.pop("raw_json"))
                except Exception:
                    pass
            extra.update(d)
            return extra

    def list_staff(self, role: Optional[str] = None, department: Optional[str] = None) -> List[Dict[str, Any]]:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM hospital_staff"
            params = []
            conditions = []
            if role:
                conditions.append("role = %s" if is_pg else "role = ?")
                params.append(role)
            if department:
                conditions.append("department = %s" if is_pg else "department = ?")
                params.append(department)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY name ASC;"
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                extra = {}
                if "raw_json" in d and isinstance(d["raw_json"], str):
                    try:
                        extra = json.loads(d.pop("raw_json"))
                    except Exception:
                        pass
                extra.update(d)
                results.append(extra)
            return results

    def update_staff_status(self, staff_id: str, status: str) -> bool:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            # Fetch existing raw_json to update it
            fetch_query = "SELECT raw_json FROM hospital_staff WHERE id = %s" if is_pg else "SELECT raw_json FROM hospital_staff WHERE id = ?"
            cur.execute(fetch_query, (staff_id,))
            row = cur.fetchone()
            if not row:
                return False
            raw_data = {}
            if row[0]:
                try:
                    raw_data = json.loads(row[0])
                except Exception:
                    pass
            raw_data["status"] = status
            new_json_str = json.dumps(raw_data)

            update_query = "UPDATE hospital_staff SET status = %s, raw_json = %s WHERE id = %s;" if is_pg else "UPDATE hospital_staff SET status = ?, raw_json = ? WHERE id = ?;"
            cur.execute(update_query, (status, new_json_str, staff_id))
            return cur.rowcount > 0

    def delete_staff_member(self, staff_id: str) -> bool:
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "DELETE FROM hospital_staff WHERE id = %s;" if is_pg else "DELETE FROM hospital_staff WHERE id = ?;"
            cur.execute(query, (staff_id,))
            return cur.rowcount > 0

    def delete_all_staff_except(self, keep_ids: List[str]) -> int:
        if not keep_ids:
            return 0
        is_pg = self.manager.engine_type == "postgresql"
        placeholders = ", ".join(["%s" if is_pg else "?" for _ in keep_ids])
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = f"DELETE FROM hospital_staff WHERE id NOT IN ({placeholders});"
            cur.execute(query, tuple(keep_ids))
            return cur.rowcount

    def count_staff(self) -> int:
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM hospital_staff;")
            res = cur.fetchone()
            return res[0] if res else 0

    def purge_mock_data(self) -> Dict[str, int]:
        """Safely purges mock/test data from patients, encounters, clinical_reports,
        physician_reviews, and dpo_feedback_pairs.
        Strictly preserves knowledge_chunks (Harrison's RAG embeddings) and hospital_staff."""
        deleted = {
            "patients": 0,
            "physician_reviews": 0,
            "report_evaluations": 0,
            "training_dataset_records": 0,
            "clinical_reports": 0,
            "encounters": 0,
            "dpo_feedback_pairs": 0,
        }
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            for tbl in ["training_dataset_records", "physician_reviews", "report_evaluations", "clinical_reports", "encounters", "patients", "dpo_feedback_pairs"]:
                cur.execute(f"DELETE FROM {tbl};")
                deleted[tbl] = cur.rowcount
            logger.info(f"Purged mock data: {deleted}")
        return deleted

    # =========================================================================
    # Knowledge Chunks & Vector Store
    # =========================================================================

    def compute_embedding(self, text: str) -> List[float]:
        """Computes 384-dimensional dense semantic embedding using all-MiniLM-L6-v2."""
        from ..rag.vector_embedder import get_vector_embedder
        embedder = get_vector_embedder()
        return embedder.embed_query(text)

    def compute_embeddings_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """Computes dense semantic embeddings for batch of texts on GPU."""
        from ..rag.vector_embedder import get_vector_embedder
        embedder = get_vector_embedder()
        return embedder.embed_texts(texts, batch_size=batch_size)

    def save_knowledge_chunk(
        self,
        chunk_id: str,
        specialty: str,
        book_title: str,
        chapter: str,
        topic: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        is_pg = self.manager.engine_type == "postgresql"
        emb_val = json.dumps(embedding) if embedding and not is_pg else embedding
        meta_val = json.dumps(metadata or {})
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute(
                    """
                    INSERT INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata;
                    """,
                    (chunk_id, specialty, book_title, chapter, topic, content, emb_val, meta_val)
                )
            else:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (chunk_id, specialty, book_title, chapter, topic, content, emb_val, meta_val)
                )
            return True

    def batch_save_knowledge_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Batch inserts knowledge chunks with vectors into the active database."""
        if not chunks:
            return 0
        is_pg = self.manager.engine_type == "postgresql"
        rows = []
        for c in chunks:
            emb = c.get("embedding")
            emb_val = json.dumps(emb) if emb and not is_pg else emb
            meta = dict(c.get("metadata", {}))
            if "page" not in meta and "page" in c:
                meta["page"] = c["page"]
            meta_val = json.dumps(meta)
            rows.append((
                c["id"],
                c.get("specialty", "INTERNAL_MEDICINE"),
                c.get("book_title", "Harrison's Principles of Internal Medicine, 21st Edition (2022)"),
                c.get("chapter", "General"),
                c.get("topic", "Clinical Medicine"),
                c.get("content", c.get("text", "")),
                emb_val,
                meta_val
            ))

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                for r in rows:
                    cur.execute(
                        """
                        INSERT INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata;
                        """,
                        r
                    )
            else:
                cur.executemany(
                    """
                    INSERT OR REPLACE INTO knowledge_chunks (id, specialty, book_title, chapter, topic, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    rows
                )
            return len(rows)

    def count_knowledge_chunks(self) -> int:
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM knowledge_chunks;")
            res = cur.fetchone()
            return res[0] if res else 0

    def search_knowledge_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        specialty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Searches knowledge chunks using vector cosine similarity."""
        is_pg = self.manager.engine_type == "postgresql"
        if not query_embedding:
            return []

        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg and self.manager.pgvector_enabled:
                cur.execute(
                    """
                    SELECT id, specialty, book_title, chapter, topic, content, metadata,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM knowledge_chunks
                    ORDER BY similarity DESC
                    LIMIT %s;
                    """,
                    (query_embedding, top_k)
                )
                rows = cur.fetchall()
                results = []
                for r in rows:
                    meta = r[6] if isinstance(r[6], dict) else json.loads(r[6] or "{}")
                    results.append({
                        "id": r[0],
                        "specialty": r[1],
                        "book": r[2],
                        "chapter": r[3],
                        "topic": r[4],
                        "text": r[5],
                        "page": meta.get("page", 0),
                        "similarity": round(float(r[7]), 3),
                    })
                return results

            # SQLite fallback: in-memory cosine similarity calculation
            cur.execute("SELECT id, specialty, book_title, chapter, topic, content, embedding, metadata FROM knowledge_chunks;")
            rows = cur.fetchall()

            import numpy as np

            q_vec = np.array(query_embedding, dtype=np.float32)
            q_norm = np.linalg.norm(q_vec)
            if q_norm == 0:
                return []

            scored = []
            for r in rows:
                emb_raw = r[6]
                if not emb_raw:
                    continue
                try:
                    vec = np.array(json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw, dtype=np.float32)
                    v_norm = np.linalg.norm(vec)
                    if v_norm > 0:
                        sim = float(np.dot(q_vec, vec) / (q_norm * v_norm))
                        scored.append((sim, r))
                except Exception:
                    continue

            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for sim, r in scored[:top_k]:
                meta = {}
                if r[7]:
                    try:
                        meta = json.loads(r[7])
                    except Exception:
                        pass
                results.append({
                    "id": r[0],
                    "specialty": r[1],
                    "book": r[2],
                    "chapter": r[3],
                    "topic": r[4],
                    "text": r[5],
                    "page": meta.get("page", 0),
                    "similarity": round(sim, 3),
                })
            return results

    def seed_default_staff(self):
        """Populates the canonical AI-VH healthcare team (Internal Medicine specialist Dr. Marcus Vance)."""
        if self.count_staff() > 0:
            return

        default_roster = [
            {
                "id": "STAFF-VANCE",
                "name": "Dr. Marcus Vance",
                "role": "DOCTOR",
                "specialty": "INTERNAL_MEDICINE",
                "title": "Chief of Internal Medicine & Clinical Reasoning Specialist",
                "department": "INTERNAL_MEDICINE",
                "status": "ON_DUTY",
                "credentials": "MD, FACP",
                "bio": "Attending physician specializing in diagnostic differentiation, Harrison's guideline adherence, and acute inpatient workups.",
                "system_prompt": "Expert internal medicine consultant. Prioritizes evidence-grounded differential diagnosis and contraindication avoidance.",
                "avatar_url": "/assets/png/vh-agent-internal-medicine-512.png",
                "total_encounters": 142,
            },
        ]

        for s in default_roster:
            self.add_staff_member(s)
        logger.info(f"Initialized hospital staff roster with {len(default_roster)} clinical personnel (Dr. Marcus Vance).")

    # =========================================================================
    # Knowledge Sources Management
    # =========================================================================

    def list_knowledge_sources(self) -> List[Dict[str, Any]]:
        """Returns all registered clinical knowledge sources."""
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, url, description, status, source_type, last_synced_at, error_message, created_at
                FROM knowledge_sources
                ORDER BY created_at ASC
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "url": r[2],
                    "description": r[3] or "",
                    "status": r[4],
                    "source_type": r[5],
                    "last_synced_at": r[6].isoformat() if hasattr(r[6], "isoformat") else (str(r[6]) if r[6] else None),
                    "error_message": r[7],
                    "created_at": r[8].isoformat() if hasattr(r[8], "isoformat") else str(r[8]),
                }
                for r in rows
            ]

    def get_knowledge_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Gets a single knowledge source by ID."""
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, url, description, status, source_type, last_synced_at, error_message, created_at
                FROM knowledge_sources
                WHERE id = ?
            """ if self.manager.engine_type == "sqlite" else """
                SELECT id, name, url, description, status, source_type, last_synced_at, error_message, created_at
                FROM knowledge_sources
                WHERE id = %s
            """, (source_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "url": row[2],
                "description": row[3] or "",
                "status": row[4],
                "source_type": row[5],
                "last_synced_at": row[6].isoformat() if hasattr(row[6], "isoformat") else (str(row[6]) if row[6] else None),
                "error_message": row[7],
                "created_at": row[8].isoformat() if hasattr(row[8], "isoformat") else str(row[8]),
            }

    def save_knowledge_source(
        self,
        source_id: str,
        name: str,
        url: str,
        description: str = "",
        status: str = "ACTIVE",
        source_type: str = "CUSTOM",
        last_synced_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> str:
        """Inserts or updates a medical knowledge source."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            if is_pg:
                cur.execute("""
                    INSERT INTO knowledge_sources (id, name, url, description, status, source_type, last_synced_at, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        url = EXCLUDED.url,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        source_type = EXCLUDED.source_type,
                        last_synced_at = EXCLUDED.last_synced_at,
                        error_message = EXCLUDED.error_message
                """, (source_id, name, url, description, status, source_type, last_synced_at, error_message))
            else:
                cur.execute("""
                    INSERT OR REPLACE INTO knowledge_sources (id, name, url, description, status, source_type, last_synced_at, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (source_id, name, url, description, status, source_type, last_synced_at, error_message))
        return source_id

    def update_knowledge_source_status(
        self,
        source_id: str,
        status: str,
        error_message: Optional[str] = None,
        last_synced_at: Optional[datetime] = None,
    ) -> bool:
        """Updates the operational status of a knowledge source."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = """
                UPDATE knowledge_sources
                SET status = %s, error_message = %s, last_synced_at = COALESCE(%s, last_synced_at)
                WHERE id = %s
            """ if is_pg else """
                UPDATE knowledge_sources
                SET status = ?, error_message = ?, last_synced_at = COALESCE(?, last_synced_at)
                WHERE id = ?
            """
            cur.execute(query, (status, error_message, last_synced_at, source_id))
            return cur.rowcount > 0

    def delete_knowledge_source(self, source_id: str) -> bool:
        """Deletes a knowledge source."""
        is_pg = self.manager.engine_type == "postgresql"
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            query = "DELETE FROM knowledge_sources WHERE id = %s" if is_pg else "DELETE FROM knowledge_sources WHERE id = ?"
            cur.execute(query, (source_id,))
            return cur.rowcount > 0

    def count_knowledge_sources(self) -> int:
        """Returns total configured knowledge sources."""
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM knowledge_sources")
            return cur.fetchone()[0]

    def seed_default_knowledge_sources(self):
        """Seeds default canonical medical knowledge sources if table is empty."""
        if self.count_knowledge_sources() > 0:
            return

        now = datetime.now(timezone.utc)
        defaults = [
            {
                "source_id": "SRC-PUBMED",
                "name": "PubMed / MEDLINE Clinical Library",
                "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                "description": "National Center for Biotechnology Information (NCBI) peer-reviewed biomedical literature and clinical guidelines.",
                "status": "ACTIVE",
                "source_type": "PUBMED",
                "last_synced_at": now,
            },
            {
                "source_id": "SRC-OPENFDA",
                "name": "openFDA Drug Labels & Safety Alerts",
                "url": "https://api.fda.gov/drug/label.json",
                "description": "FDA structured product labeling, boxed warnings, indications, contraindications, and adverse reaction registries.",
                "status": "ACTIVE",
                "source_type": "OPENFDA",
                "last_synced_at": now,
            },
            {
                "source_id": "SRC-RXNORM",
                "name": "NLM RxNorm Clinical Formulary",
                "url": "https://rxnav.nlm.nih.gov/REST/",
                "description": "National Library of Medicine standardized clinical drug nomenclature, RXCUIs, and active ingredient maps.",
                "status": "ACTIVE",
                "source_type": "RXNORM",
                "last_synced_at": now,
            },
        ]
        for src in defaults:
            self.save_knowledge_source(**src)
        logger.info(f"Seeded {len(defaults)} default clinical knowledge sources.")


# Global singleton repository
db_repo = DatabaseRepository()
db_repo.seed_default_staff()
db_repo.seed_default_knowledge_sources()
db_repo.seed_default_admitted_patients()





