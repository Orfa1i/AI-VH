"""
AI Virtual Hospital - Clinical Database Repository
Provides unified CRUD, querying, and persistent storage for clinical reports,
physician reviews, DPO pairs, and knowledge embeddings across PostgreSQL and SQLite.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

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

    def count_knowledge_chunks(self) -> int:
        with self.manager.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM knowledge_chunks;")
            res = cur.fetchone()
            return res[0] if res else 0


# Global singleton repository
db_repo = DatabaseRepository()
