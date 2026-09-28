"""
Idempotent FHIR R4 bundle loader for AI-VH patient repository.
Extracts clinical resources, normalizes patient and encounter linkages, and prevents duplicate records.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field

from .patient_repo import PatientRepository


class LoadSummary(BaseModel):
    """Execution summary of an ingested population of FHIR bundles."""
    total_files: int = 0
    total_resources: int = 0
    created_count: int = 0
    updated_count: int = 0
    resource_types: Dict[str, int] = Field(default_factory=dict)


def clean_reference(ref_str: Optional[str]) -> Optional[str]:
    """Clean urn:uuid: or Type/ prefixes from FHIR reference strings."""
    if not ref_str:
        return None
    val = ref_str.replace("urn:uuid:", "")
    if "/" in val:
        val = val.split("/")[-1]
    return val


class FHIRBundleLoader:
    """
    Idempotent loader ingesting Synthea-generated FHIR R4 bundles into PatientRepository.
    """

    def __init__(self, repo: PatientRepository):
        self.repo = repo

    def load_bundle(self, bundle_source: Union[Dict[str, Any], Path, str]) -> Dict[str, Any]:
        """
        Load a single FHIR R4 transaction or collection bundle idempotently.
        """
        if isinstance(bundle_source, (str, Path)):
            p = Path(bundle_source)
            if not p.exists():
                raise FileNotFoundError(f"Bundle file not found: {p}")
            data = json.loads(p.read_text(encoding="utf-8"))
        elif isinstance(bundle_source, dict):
            data = bundle_source
        else:
            raise TypeError(f"Expected dict, Path, or str for bundle_source, got {type(bundle_source)}")

        if data.get("resourceType") != "Bundle":
            raise ValueError(f"Expected resourceType 'Bundle', received '{data.get('resourceType')}'")

        entries = data.get("entry", [])
        bundle_timestamp = data.get("timestamp")

        # First pass: Identify primary patient ID in bundle
        bundle_patient_id: Optional[str] = None
        for entry in entries:
            res = entry.get("resource", {})
            if res.get("resourceType") == "Patient":
                bundle_patient_id = clean_reference(res.get("id"))
                break

        created_in_bundle = 0
        updated_in_bundle = 0
        types_in_bundle: Dict[str, int] = {}

        # Second pass: Ingest all resources
        for entry in entries:
            res = entry.get("resource", {})
            res_type = res.get("resourceType")
            res_id = clean_reference(res.get("id"))

            if not res_type or not res_id:
                continue

            # Determine patient_id
            if res_type == "Patient":
                patient_id = res_id
            else:
                raw_subj = res.get("subject", {}).get("reference") or res.get("patient", {}).get("reference")
                patient_id = clean_reference(raw_subj) or bundle_patient_id

            # Determine encounter_id
            raw_enc = res.get("encounter", {}).get("reference") or res.get("context", {}).get("reference")
            encounter_id = clean_reference(raw_enc)

            # Determine effective_datetime
            effective_datetime = (
                res.get("effectiveDateTime")
                or res.get("effectiveInstant")
                or res.get("issued")
                or res.get("period", {}).get("start")
                or res.get("onsetDateTime")
                or res.get("recordedDate")
                or res.get("authoredOn")
                or bundle_timestamp
            )

            # Determine clinical code
            code: Optional[str] = None
            if "code" in res and isinstance(res["code"], dict):
                codings = res["code"].get("coding", [])
                if codings and isinstance(codings, list):
                    code = codings[0].get("code")
            elif "medicationCodeableConcept" in res and isinstance(res["medicationCodeableConcept"], dict):
                codings = res["medicationCodeableConcept"].get("coding", [])
                if codings and isinstance(codings, list):
                    code = codings[0].get("code")

            created = self.repo.upsert_resource(
                resource_type=res_type,
                resource_id=res_id,
                patient_id=patient_id,
                encounter_id=encounter_id,
                effective_datetime=effective_datetime,
                code=code,
                data=res
            )

            if created:
                created_in_bundle += 1
            else:
                updated_in_bundle += 1

            types_in_bundle[res_type] = types_in_bundle.get(res_type, 0) + 1

        return {
            "total_entries": len(entries),
            "created": created_in_bundle,
            "updated": updated_in_bundle,
            "types": types_in_bundle
        }

    def load_directory(self, bundles_dir: Union[Path, str]) -> LoadSummary:
        """
        Scan a directory of FHIR bundle files and load all resources idempotently.
        """
        target = Path(bundles_dir)
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"Directory not found: {target}")

        bundle_files = sorted(
            [f for f in target.glob("*.json") if f.name not in ("manifest.json", "metadata.json")]
        )

        total_files = len(bundle_files)
        total_resources = 0
        total_created = 0
        total_updated = 0
        aggregated_types: Dict[str, int] = {}

        for bf in bundle_files:
            res_summary = self.load_bundle(bf)
            total_resources += res_summary["total_entries"]
            total_created += res_summary["created"]
            total_updated += res_summary["updated"]

            for rtype, rcount in res_summary["types"].items():
                aggregated_types[rtype] = aggregated_types.get(rtype, 0) + rcount

        return LoadSummary(
            total_files=total_files,
            total_resources=total_resources,
            created_count=total_created,
            updated_count=total_updated,
            resource_types=aggregated_types
        )
