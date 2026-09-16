"""
AI Virtual Hospital - Clinical Database Repository
Provides unified CRUD, querying, and persistent storage for clinical reports,
physician reviews, DPO pairs, and knowledge embeddings across PostgreSQL and SQLite.
"""

import json
import logging
import uuid
import random
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
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic cosine similarity search over medical knowledge chunks.
        Supports native pgvector on PostgreSQL and fast cosine dot-product on SQLite.
        """
        import math
        import re
        q_vec = self.compute_embedding(query)
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
        patient record with MRN, department assignment, and bed allocation.
        """
        patient_id = case_data.get("id") or f"PAT-{uuid.uuid4().hex[:8].upper()}"
        mrn = case_data.get("mrn") or f"MRN-{random.randint(100000, 999999)}"
        name = case_data.get("name", "Unknown Patient")
        age = int(case_data.get("age", 50))
        sex = case_data.get("sex", "Unknown")
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
            query = "UPDATE patients SET admission_status = 'DISCHARGED' WHERE id = %s OR mrn = %s" if is_pg else "UPDATE patients SET admission_status = 'DISCHARGED' WHERE id = ? OR mrn = ?"
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



