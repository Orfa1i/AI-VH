"""
Patient repository for AI Virtual Hospital (AI-VH).
Provides relational indexing and JSON document storage for FHIR R4 clinical resources.
Supports PostgreSQL JSONB and embedded SQLite for seamless offline testing.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class PatientRepository:
    """
    Relational JSON repository managing FHIR R4 patient records, encounters,
    diagnostic observations, conditions, and medications.
    """

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        pg_url: Optional[str] = None
    ):
        self.db_path = Path(db_path) if db_path else (REPO_ROOT / "data" / "patients.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.pg_url = pg_url
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create fhir_resources table and performance indexes."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fhir_resources (
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    patient_id TEXT,
                    encounter_id TEXT,
                    effective_datetime TEXT,
                    code TEXT,
                    data TEXT NOT NULL,
                    PRIMARY KEY (resource_type, resource_id)
                );
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_fhir_patient_type ON fhir_resources(patient_id, resource_type);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_fhir_patient_time ON fhir_resources(patient_id, effective_datetime);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_fhir_code ON fhir_resources(code);"
            )

    def upsert_resource(
        self,
        resource_type: str,
        resource_id: str,
        patient_id: Optional[str],
        encounter_id: Optional[str],
        effective_datetime: Optional[str],
        code: Optional[str],
        data: Dict[str, Any]
    ) -> bool:
        """
        Idempotently insert or update a FHIR resource.
        Returns True if newly created, False if updated.
        """
        json_data = json.dumps(data)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM fhir_resources WHERE resource_type = ? AND resource_id = ?;",
                (resource_type, resource_id)
            )
            exists = cursor.fetchone() is not None

            if exists:
                conn.execute(
                    """
                    UPDATE fhir_resources
                    SET patient_id = ?,
                        encounter_id = ?,
                        effective_datetime = ?,
                        code = ?,
                        data = ?
                    WHERE resource_type = ? AND resource_id = ?;
                    """,
                    (
                        patient_id,
                        encounter_id,
                        effective_datetime,
                        code,
                        json_data,
                        resource_type,
                        resource_id
                    )
                )
                return False
            else:
                conn.execute(
                    """
                    INSERT INTO fhir_resources (
                        resource_type, resource_id, patient_id, encounter_id, effective_datetime, code, data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        resource_type,
                        resource_id,
                        patient_id,
                        encounter_id,
                        effective_datetime,
                        code,
                        json_data
                    )
                )
                return True

    def count_resources(self, resource_type: Optional[str] = None) -> int:
        """Return count of stored resources, optionally filtered by type."""
        with self._get_connection() as conn:
            if resource_type:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM fhir_resources WHERE resource_type = ?;",
                    (resource_type,)
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM fhir_resources;")
            return cursor.fetchone()[0]

    def list_patient_ids(self) -> List[str]:
        """Return sorted list of all unique patient IDs stored in repository."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT resource_id FROM fhir_resources WHERE resource_type = 'Patient' ORDER BY resource_id;"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full FHIR Patient resource by patient ID."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT data FROM fhir_resources WHERE resource_type = 'Patient' AND resource_id = ?;",
                (clean_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return json.loads(row[0])

    def get_encounters(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve all encounters for a patient, ordered chronologically."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT data FROM fhir_resources
                WHERE resource_type = 'Encounter' AND patient_id = ?
                ORDER BY effective_datetime ASC, resource_id ASC;
                """,
                (clean_id,)
            )
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def get_observations(
        self,
        patient_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve observations for a patient within an optional time window and code filter."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        query = ["SELECT data FROM fhir_resources WHERE resource_type = 'Observation' AND patient_id = ?"]
        params: List[Any] = [clean_id]

        if start_time:
            query.append("AND effective_datetime >= ?")
            params.append(start_time)
        if end_time:
            query.append("AND effective_datetime <= ?")
            params.append(end_time)
        if code:
            query.append("AND code = ?")
            params.append(code)

        query.append("ORDER BY effective_datetime ASC, resource_id ASC;")
        full_sql = " ".join(query)

        with self._get_connection() as conn:
            cursor = conn.execute(full_sql, params)
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def get_conditions(self, patient_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        """Retrieve conditions recorded for a patient."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT data FROM fhir_resources
                WHERE resource_type = 'Condition' AND patient_id = ?
                ORDER BY effective_datetime ASC, resource_id ASC;
                """,
                (clean_id,)
            )
            items = [json.loads(row[0]) for row in cursor.fetchall()]
            if active_only:
                filtered = []
                for item in items:
                    cstatus = item.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
                    if cstatus == "active":
                        filtered.append(item)
                return filtered
            return items

    def get_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve medication requests and orders for a patient."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT data FROM fhir_resources
                WHERE resource_type IN ('MedicationRequest', 'MedicationOrder') AND patient_id = ?
                ORDER BY effective_datetime ASC, resource_id ASC;
                """,
                (clean_id,)
            )
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def get_allergies(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve allergy records for a patient."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT data FROM fhir_resources
                WHERE resource_type = 'AllergyIntolerance' AND patient_id = ?
                ORDER BY effective_datetime ASC, resource_id ASC;
                """,
                (clean_id,)
            )
            return [json.loads(row[0]) for row in cursor.fetchall()]

    def get_clinical_timeline(
        self,
        patient_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve all clinical events (encounters, observations, conditions, medications) ordered chronologically."""
        clean_id = patient_id.replace("urn:uuid:", "").replace("Patient/", "")
        query = ["SELECT data FROM fhir_resources WHERE patient_id = ?"]
        params: List[Any] = [clean_id]

        if start_time:
            query.append("AND (effective_datetime IS NULL OR effective_datetime >= ?)")
            params.append(start_time)
        if end_time:
            query.append("AND (effective_datetime IS NULL OR effective_datetime <= ?)")
            params.append(end_time)

        query.append("ORDER BY effective_datetime ASC, resource_type ASC, resource_id ASC;")
        full_sql = " ".join(query)

        with self._get_connection() as conn:
            cursor = conn.execute(full_sql, params)
            return [json.loads(row[0]) for row in cursor.fetchall()]
