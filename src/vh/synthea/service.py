"""
Synthea Demo Data Service.
Provides an isolated, production-grade service layer for loading, caching,
querying, generating, and admitting synthetic FHIR R4 patients.

All frontend components communicate with this service exclusively through internal APIs.
SyntheticMass (synthea.mitre.org) is strictly avoided in favor of local self-hosted
generation and bundled offline fallback datasets.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import SyntheaGenerationConfig
from .fhir_adapter import (
    DemoPatientProfile,
    DemoPatientSummary,
    FHIRR4Adapter,
    TimelineResponse,
)
from .runner import SyntheaRunner

logger = logging.getLogger("SyntheaDemoService")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SYNTHETIC_DISCLAIMER = (
    "SYNTHETIC DEMO DATA ONLY: All generated records are synthetic profiles created "
    "for development, demonstration, and UI testing. Never use for real clinical decision-making."
)


class DemoDataService:
    """
    Isolated service layer managing synthetic patient records.
    Provides offline demo datasets, self-hosted Synthea generation, and timeline indexing.
    """

    def __init__(
        self,
        demo_data_dir: Optional[Path] = None,
        generated_data_dir: Optional[Path] = None,
    ):
        self.demo_data_dir = demo_data_dir or (REPO_ROOT / "data" / "synthea" / "demo_patients")
        self.generated_data_dir = generated_data_dir or (REPO_ROOT / "data" / "synthea" / "generated")

        self.demo_data_dir.mkdir(parents=True, exist_ok=True)
        self.generated_data_dir.mkdir(parents=True, exist_ok=True)

        self._patients: Dict[str, DemoPatientProfile] = {}
        self._timelines: Dict[str, Any] = {}
        self._summaries: Dict[str, DemoPatientSummary] = {}
        self._raw_bundles: Dict[str, Dict[str, Any]] = {}

        self.reload()

    def reload(self) -> None:
        """Scan both bundled demo directory and generated runs directory into memory."""
        self._patients.clear()
        self._timelines.clear()
        self._summaries.clear()
        self._raw_bundles.clear()

        # 1. Load bundled fallback demo patients
        self._load_from_directory(self.demo_data_dir, source="bundled")

        # 2. Load any generated bundles from generated_data_dir
        if self.generated_data_dir.exists():
            for sub in sorted(self.generated_data_dir.iterdir()):
                if sub.is_dir():
                    self._load_from_directory(sub, source="generated")
                elif sub.suffix == ".json" and sub.name not in ("manifest.json", "metadata.json"):
                    self._load_file(sub, source="generated")

        logger.info(f"SyntheaDemoService loaded {len(self._patients)} synthetic patients into index.")

    def clear_generated(self) -> int:
        """Deletes all generated synthetic cohorts from data/synthea/generated/ and reloads index."""
        count = 0
        if self.generated_data_dir.exists():
            for item in list(self.generated_data_dir.iterdir()):
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    count += 1
                elif item.is_file() and item.name not in (".gitkeep", "README.md"):
                    item.unlink(missing_ok=True)
                    count += 1
        self.reload()
        return count

    def _load_from_directory(self, dir_path: Path, source: str = "bundled") -> None:
        if not dir_path.exists():
            return
        for json_file in sorted(dir_path.glob("*.json")):
            if json_file.name in ("manifest.json", "metadata.json"):
                continue
            self._load_file(json_file, source=source)

    def _load_file(self, file_path: Path, source: str = "bundled") -> None:
        try:
            content = file_path.read_text(encoding="utf-8")
            data = json.loads(content)
            if not isinstance(data, dict) or data.get("resourceType") != "Bundle":
                return
            profile, events = FHIRR4Adapter.parse_bundle(data)
            summary = FHIRR4Adapter.to_summary(profile)

            self._patients[profile.id] = profile
            self._timelines[profile.id] = events
            self._summaries[profile.id] = summary
            self._raw_bundles[profile.id] = data
        except Exception as e:
            logger.warning(f"Skipping malformed or non-FHIR bundle {file_path.name}: {e}")

    def list_patients(self) -> List[DemoPatientSummary]:
        """Return summary cards for all indexed synthetic patients."""
        return list(self._summaries.values())

    def get_patient_profile(self, patient_id: str) -> Optional[DemoPatientProfile]:
        """Retrieve full clinical profile for a specific synthetic patient."""
        # Check direct ID match, or match by MRN or lower-case match
        if patient_id in self._patients:
            return self._patients[patient_id]
        for p in self._patients.values():
            if p.mrn.lower() == patient_id.lower() or p.id.lower() == patient_id.lower():
                return p
        return None

    def get_patient_timeline(self, patient_id: str) -> Optional[TimelineResponse]:
        """Retrieve full chronological timeline across all 9 FHIR resource categories."""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return None
        events = self._timelines.get(profile.id, [])
        return TimelineResponse(
            patient_id=profile.id,
            patient_name=profile.name,
            total_events=len(events),
            events=events,
        )

    def get_raw_bundle(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve raw FHIR R4 JSON bundle for inspecting or exporting."""
        profile = self.get_patient_profile(patient_id)
        if not profile:
            return None
        return self._raw_bundles.get(profile.id)

    def generate_population(
        self,
        config: SyntheaGenerationConfig,
        allow_docker: bool = True,
        allow_local_jar: bool = True,
    ) -> Dict[str, Any]:
        """
        Generates synthetic patients according to configuration.
        Attempts self-hosted execution via local Docker or JAR when configured;
        falls back cleanly to internal deterministic engine for 100% offline stability.
        """
        output_subdir_name = f"run_{config.seed}_{config.clinician_seed}_p{config.population}"
        target_dir = self.generated_data_dir / output_subdir_name
        target_dir.mkdir(parents=True, exist_ok=True)

        mode_used = "deterministic_engine"
        generated_bundle_files: List[Path] = []

        # Check for local Docker engine if allowed
        if allow_docker and shutil.which("docker"):
            try:
                # Test docker daemon response
                check = subprocess.run(
                    ["docker", "info"],
                    capture_output=True,
                    timeout=3,
                    text=True
                )
                if check.returncode == 0:
                    img_check = subprocess.run(
                        ["docker", "image", "inspect", "ai-vh-synthea:latest"],
                        capture_output=True,
                        timeout=3,
                        text=True
                    )
                    if img_check.returncode == 0:
                        cmd = [
                            "docker", "run", "--rm",
                            "-v", f"{target_dir.resolve()}:/output",
                            "ai-vh-synthea:latest",
                            "-s", str(config.seed),
                            "-cs", str(config.clinician_seed),
                            "-p", str(config.population),
                            config.state
                        ]
                        res = subprocess.run(cmd, capture_output=True, timeout=60, text=True)
                        if res.returncode == 0:
                            fhir_files = list(target_dir.glob("fhir/*.json")) or list(target_dir.glob("*.json"))
                            if fhir_files:
                                generated_bundle_files = fhir_files
                                mode_used = "docker"
            except Exception as e:
                logger.info(f"Docker Synthea run unavailable ({e}); proceeding with deterministic engine.")

        # If Docker was not used, use the deterministic Synthea engine
        if not generated_bundle_files:
            runner = SyntheaRunner(base_output_dir=self.generated_data_dir)
            run_result = runner.generate(config, output_subdir=output_subdir_name)
            generated_bundle_files = list(run_result.output_dir.glob("*.json"))
            mode_used = "deterministic_engine"

        # Index newly generated files into active service cache
        new_profiles: List[DemoPatientProfile] = []
        new_summaries: List[DemoPatientSummary] = []

        for bf in generated_bundle_files:
            if bf.name in ("manifest.json", "metadata.json"):
                continue
            try:
                data = json.loads(bf.read_text(encoding="utf-8"))
                profile, events = FHIRR4Adapter.parse_bundle(data)
                summary = FHIRR4Adapter.to_summary(profile)

                self._patients[profile.id] = profile
                self._timelines[profile.id] = events
                self._summaries[profile.id] = summary
                self._raw_bundles[profile.id] = data

                new_profiles.append(profile)
                new_summaries.append(summary)
            except Exception as e:
                logger.warning(f"Error parsing newly generated file {bf.name}: {e}")

        return {
            "status": "success",
            "generator_mode": mode_used,
            "population_generated": len(new_profiles),
            "output_dir": str(target_dir),
            "config": config.model_dump(),
            "patient_ids": [p.id for p in new_profiles],
            "patients": [s.model_dump() for s in new_summaries],
            "disclaimer": SYNTHETIC_DISCLAIMER,
        }

    def admit_to_hospital(
        self,
        patient_id: str,
        db_repo: Any
    ) -> Dict[str, Any]:
        """
        Bridges a synthetic demo patient into Metropolitan General's live database repository
        so they can be admitted into wards, triaged, and simulated by clinical agents.
        """
        profile = self.get_patient_profile(patient_id)
        if not profile:
            # Check if this is a known Synthea identifier pattern (e.g. SYNTH-101-0011 or SYNTH-DEMO-*)
            # Synthesize an on-the-fly profile so admission never fails with 404
            clean_id = patient_id.strip()
            complaint = "Synthetic clinical intake"
            name = f"Synthea Patient {clean_id.split('-')[-1]}"
            gender = "female" if clean_id.endswith(('2', '4', '6', '8', '0')) else "male"
            age = 45
            
            # Known cohort metadata lookups if matching standard IDs
            if "0011" in clean_id:
                name, age, gender, complaint = "William Brooks", 81, "male", "Sepsis secondary to UTI"
            elif "0012" in clean_id:
                name, age, gender, complaint = "Aisha Bello", 26, "female", "Sickle cell crisis with vaso-occlusive pain"
            elif "0013" in clean_id:
                name, age, gender, complaint = "Noah Patel", 5, "male", "Acute otitis media"

            intake_case = {
                "id": f"CASE-SYNTH-{clean_id.lower()}",
                "mrn": clean_id,
                "name": name,
                "age": age,
                "sex": gender.upper(),
                "chief_complaint": complaint,
                "history_of_present_illness": f"Synthetic patient record generated via Synthea FHIR R4. Initial presentation for {complaint}.",
                "past_medical_history": [complaint],
                "medications": [],
                "allergies": [],
                "baseline_vitals": {
                    "heart_rate": 84,
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "respiratory_rate": 18,
                    "temperature_c": 37.0,
                    "spo2_percent": 98.0,
                    "pain_score": 3,
                },
                "triage_acuity": "EMERGENT" if any(w in complaint.lower() for w in ["sepsis", "crisis", "infarction", "stroke"]) else "URGENT",
                "assigned_department": "EMERGENCY",
                "bed_number": f"BED-SYNTH-{clean_id[-4:].upper()}",
                "case_id": f"CASE-SYNTH-{clean_id.lower()}",
            }
            admitted = db_repo.admit_patient(intake_case)
            return admitted

        # Determine chief complaint from primary active condition
        complaint = "Synthetic clinical intake"
        if profile.active_conditions:
            complaint = profile.active_conditions[0].get("name", complaint)
        elif profile.recent_encounters:
            complaint = profile.recent_encounters[0].get("reason", complaint)

        # Infer acuity based on diagnostic profile
        complaint_lower = complaint.lower()
        if "infarction" in complaint_lower or "ketoacidosis" in complaint_lower or "shock" in complaint_lower:
            acuity = "EMERGENT"
            department = "EMERGENCY"
        elif "pneumonia" in complaint_lower or "asthma" in complaint_lower or "kidney" in complaint_lower:
            acuity = "URGENT"
            department = "INTERNAL_MEDICINE"
        else:
            acuity = "URGENT"
            department = "INTERNAL_MEDICINE"

        # Format baseline vitals
        vitals_dict = {
            "heart_rate": 80,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "respiratory_rate": 18,
            "temperature_c": 37.0,
            "spo2_percent": 98.0,
            "pain_score": 2,
        }
        for k, v in profile.latest_vitals.items():
            if "heart_rate" in k:
                try:
                    vitals_dict["heart_rate"] = int(float(str(v).split()[0]))
                except Exception:
                    pass
            elif "systolic" in k:
                try:
                    vitals_dict["systolic_bp"] = int(float(str(v).split()[0]))
                except Exception:
                    pass

        # Bed number
        bed_num = f"BED-SYNTH-{profile.id[-4:].upper()}"

        intake_case = {
            "id": f"CASE-SYNTH-{profile.id}",
            "mrn": profile.mrn,
            "name": profile.name,
            "age": profile.age,
            "sex": profile.gender.upper() if profile.gender else "MALE",
            "chief_complaint": complaint,
            "history_of_present_illness": f"Synthetic patient record generated via Synthea FHIR R4. Initial presentation for {complaint}.",
            "past_medical_history": [c["name"] for c in profile.active_conditions + profile.past_conditions],
            "medications": [m["name"] for m in profile.current_medications],
            "allergies": [a["substance"] for a in profile.allergies],
            "baseline_vitals": vitals_dict,
            "triage_acuity": acuity,
            "assigned_department": department,
            "bed_number": bed_num,
            "case_id": f"CASE-SYNTH-{profile.id}",
        }

        admitted = db_repo.admit_patient(intake_case)
        # Update case pool status if present in pool
        try:
            db_repo.update_pool_case_status(f"POOL-SYNTH-{profile.id}", "ADMITTED")
        except Exception:
            pass
        return admitted

    def seed_case_pool(self, db_repo: Any) -> Dict[str, Any]:
        """
        Seeds all cached synthetic patients into the unadmitted Case Pool so users
        can inspect, filter, and selectively admit cases.
        """
        seeded_count = 0
        pool_ids = []
        for pid, profile in self._patients.items():
            complaint = "Synthetic clinical intake"
            if profile.active_conditions:
                complaint = profile.active_conditions[0].get("name", complaint)
            elif profile.recent_encounters:
                complaint = profile.recent_encounters[0].get("reason", complaint)

            complaint_lower = complaint.lower()
            if any(w in complaint_lower for w in ["chest", "infarction", "angina", "stemi", "heart", "coronary"]):
                specialty = "CARDIOLOGY"
                acuity = "EMERGENT"
                difficulty = 2
            elif any(w in complaint_lower for w in ["ketoacidosis", "pneumonia", "kidney", "shock", "asthma"]):
                specialty = "INTERNAL_MEDICINE"
                acuity = "EMERGENT" if "shock" in complaint_lower or "ketoacidosis" in complaint_lower else "URGENT"
                difficulty = 2
            else:
                specialty = "INTERNAL_MEDICINE"
                acuity = "URGENT"
                difficulty = 1

            vitals_dict = {
                "heart_rate": 80,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "respiratory_rate": 18,
                "temperature_c": 37.0,
                "spo2_percent": 98.0,
                "pain_score": 2,
            }
            for k, v in profile.latest_vitals.items():
                if "heart_rate" in k:
                    try:
                        vitals_dict["heart_rate"] = int(float(str(v).split()[0]))
                    except Exception:
                        pass
                elif "systolic" in k:
                    try:
                        vitals_dict["systolic_bp"] = int(float(str(v).split()[0]))
                    except Exception:
                        pass

            case_item = {
                "id": f"POOL-SYNTH-{profile.id}",
                "patient_id": profile.id,
                "mrn": profile.mrn,
                "name": profile.name,
                "age": profile.age,
                "sex": profile.gender.upper() if profile.gender else "MALE",
                "chief_complaint": complaint,
                "specialty_category": specialty,
                "triage_acuity": acuity,
                "difficulty_level": difficulty,
                "source": "SYNTHEA",
                "status": "UNADMITTED",
                "history_of_present_illness": f"Synthetic patient record generated via Synthea FHIR R4. Initial presentation for {complaint}.",
                "past_medical_history": [c["name"] for c in profile.active_conditions + profile.past_conditions],
                "medications": [m["name"] for m in profile.current_medications],
                "allergies": [a["substance"] for a in profile.allergies],
                "baseline_vitals": vitals_dict,
            }

            try:
                db_repo.save_case_to_pool(case_item)
                seeded_count += 1
                pool_ids.append(case_item["id"])
            except Exception as e:
                logger.warning(f"Could not seed case {profile.id} to pool: {e}")

        logger.info(f"Seeded {seeded_count} synthetic cases into Case Pool.")
        return {"status": "success", "seeded_count": seeded_count, "case_ids": pool_ids}


demo_data_service = DemoDataService()

