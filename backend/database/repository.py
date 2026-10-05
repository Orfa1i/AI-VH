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
from ..clinical.models import ClinicalReport, PhysicianReview

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
        top_k: int = 3,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic cosine similarity search over medical knowledge chunks.
        Supports native pgvector on PostgreSQL and fast cosine dot-product on SQLite.
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
                if specialty:
                    cur.execute(
                        """
                        SELECT id, specialty, book_title, chapter, topic, content, metadata,
                               (1.0 - (embedding <=> %s::vector)) AS score
                        FROM knowledge_chunks
                        WHERE specialty = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                        """,
                        (emb_str, specialty, emb_str, top_k)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, specialty, book_title, chapter, topic, content, metadata,
                               (1.0 - (embedding <=> %s::vector)) AS score
                        FROM knowledge_chunks
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                        """,
                        (emb_str, emb_str, top_k)
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

            # SQLite or standard fallback
            if specialty:
                cur.execute("SELECT id, specialty, book_title, chapter, topic, content, embedding, metadata FROM knowledge_chunks WHERE specialty = ?;", (specialty,))
            else:
                cur.execute("SELECT id, specialty, book_title, chapter, topic, content, embedding, metadata FROM knowledge_chunks;")
            rows = cur.fetchall()

            scored = []
            for r in rows:
                row_dict = dict(r)
                emb_raw = row_dict.pop("embedding", None)
                chunk_emb = json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw
                
                # Cosine similarity (dot product of L2 normalized vectors)
                sim = 0.0
                if chunk_emb and len(chunk_emb) == len(q_vec):
                    sim = sum(a * b for a, b in zip(q_vec, chunk_emb))

                # Topic token matching boost
                topic_tokens = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", row_dict["topic"].lower()))
                topic_overlap = len(q_tokens.intersection(topic_tokens)) / max(len(topic_tokens), 1) if topic_tokens else 0.0

                # Keyword lexical overlap boost in chapter and content
                content_tokens = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", (row_dict["chapter"] + " " + row_dict["content"]).lower()))
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
            "clinical_reports": 0,
            "encounters": 0,
            "dpo_feedback_pairs": 0,
        }
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            for tbl in ["physician_reviews", "report_evaluations", "clinical_reports", "encounters", "patients", "dpo_feedback_pairs"]:
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
                "avatar_url": "/assets/dr_marcus_vance.jpg",
                "total_encounters": 142,
            },
        ]

        for s in default_roster:
            self.add_staff_member(s)
        logger.info(f"Initialized hospital staff roster with {len(default_roster)} clinical personnel (Dr. Marcus Vance).")


# Global singleton repository
db_repo = DatabaseRepository()
db_repo.seed_default_staff()



