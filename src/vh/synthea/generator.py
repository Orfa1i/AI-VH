"""
Deterministic Synthea FHIR R4 bundle generator engine.
Produces reproducible patient populations with clinical encounters, diagnoses, and vitals.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from .config import SyntheaGenerationConfig
from .validator import validate_fhir_bundle

FIRST_NAMES_MALE = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles"]
FIRST_NAMES_FEMALE = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

SPECIALTY_CONDITIONS = [
    {"code": "22298006", "system": "http://snomed.info/sct", "display": "Myocardial infarction"},
    {"code": "233604007", "system": "http://snomed.info/sct", "display": "Pneumonia"},
    {"code": "46635009", "system": "http://snomed.info/sct", "display": "Diabetes mellitus type 1 with ketoacidosis"},
    {"code": "38341003", "system": "http://snomed.info/sct", "display": "Hypertension"},
    {"code": "53741008", "system": "http://snomed.info/sct", "display": "Coronary arteriosclerosis"},
]


def generate_deterministic_population(
    config: SyntheaGenerationConfig,
    output_dir: Path
) -> List[Path]:
    """
    Generate a population of FHIR R4 patient bundles with byte-for-byte reproducibility.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    rng_patient = random.Random(config.seed)
    rng_clinician = random.Random(config.clinician_seed)

    ref_dt = datetime.strptime(config.reference_date, "%Y-%m-%d")
    generated_files: List[Path] = []

    for i in range(1, config.population + 1):
        patient_id = f"pat-{config.seed}-{i:04d}"
        clinician_id = f"clin-{config.clinician_seed}-{(i % 5) + 1:03d}"

        # Demographics
        if config.gender:
            gender = "male" if config.gender.upper().startswith("M") else "female"
        else:
            gender = rng_patient.choice(["male", "female"])

        first_name = rng_patient.choice(FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE)
        last_name = rng_patient.choice(LAST_NAMES)

        if config.age_range:
            age = rng_patient.randint(config.age_range[0], config.age_range[1])
        else:
            age = rng_patient.randint(25, 75)

        birth_dt = ref_dt - timedelta(days=int(age * 365.25) + rng_patient.randint(0, 360))
        birth_str = birth_dt.strftime("%Y-%m-%d")

        city = config.city or ("Boston" if config.state == "Massachusetts" else "Metropolis")

        # Clinical parameters
        hr = rng_patient.randint(62, 115)
        sys_bp = rng_patient.randint(110, 165)
        dia_bp = rng_patient.randint(70, 95)
        temp = round(36.5 + rng_patient.uniform(0.0, 2.8), 1)
        rr = rng_patient.randint(14, 26)

        cond_item = rng_patient.choice(SPECIALTY_CONDITIONS)

        bundle_id = f"bundle-{config.seed}-{i:04d}"
        bundle_json: Dict[str, Any] = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "transaction",
            "timestamp": f"{config.reference_date}T08:00:00Z",
            "entry": [
                {
                    "fullUrl": f"urn:uuid:{patient_id}",
                    "resource": {
                        "resourceType": "Patient",
                        "id": patient_id,
                        "identifier": [
                            {
                                "system": "https://github.com/synthetichealth/synthea",
                                "value": f"SYNTH-{config.seed}-{i:04d}"
                            }
                        ],
                        "name": [
                            {
                                "use": "official",
                                "family": last_name,
                                "given": [first_name]
                            }
                        ],
                        "gender": gender,
                        "birthDate": birth_str,
                        "address": [
                            {
                                "city": city,
                                "state": config.state,
                                "country": "US"
                            }
                        ]
                    },
                    "request": {"method": "POST", "url": "Patient"}
                },
                {
                    "fullUrl": f"urn:uuid:enc-{patient_id}",
                    "resource": {
                        "resourceType": "Encounter",
                        "id": f"enc-{patient_id}",
                        "status": "finished",
                        "class": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                                        "code": "IMP",
                                        "display": "inpatient encounter"
                                    }
                                ]
                            }
                        ],
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "participant": [
                            {
                                "actor": {
                                    "reference": f"urn:uuid:{clinician_id}",
                                    "display": f"Dr. Assigned Clinician {clinician_id}"
                                }
                            }
                        ]
                    },
                    "request": {"method": "POST", "url": "Encounter"}
                },
                {
                    "fullUrl": f"urn:uuid:cond-{patient_id}",
                    "resource": {
                        "resourceType": "Condition",
                        "id": f"cond-{patient_id}",
                        "clinicalStatus": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                    "code": "active"
                                }
                            ]
                        },
                        "code": {
                            "coding": [
                                {
                                    "system": cond_item["system"],
                                    "code": cond_item["code"],
                                    "display": cond_item["display"]
                                }
                            ]
                        },
                        "subject": {"reference": f"urn:uuid:{patient_id}"}
                    },
                    "request": {"method": "POST", "url": "Condition"}
                },
                {
                    "fullUrl": f"urn:uuid:obs-hr-{patient_id}",
                    "resource": {
                        "resourceType": "Observation",
                        "id": f"obs-hr-{patient_id}",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8867-4",
                                    "display": "Heart rate"
                                }
                            ]
                        },
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "valueQuantity": {
                            "value": float(hr),
                            "unit": "/min",
                            "system": "http://unitsofmeasure.org",
                            "code": "/min"
                        }
                    },
                    "request": {"method": "POST", "url": "Observation"}
                },
                {
                    "fullUrl": f"urn:uuid:obs-bp-{patient_id}",
                    "resource": {
                        "resourceType": "Observation",
                        "id": f"obs-bp-{patient_id}",
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": "vital-signs"
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "85354-9",
                                    "display": "Blood pressure systolic & diastolic"
                                }
                            ]
                        },
                        "subject": {"reference": f"urn:uuid:{patient_id}"},
                        "component": [
                            {
                                "code": {
                                    "coding": [
                                        {"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}
                                    ]
                                },
                                "valueQuantity": {
                                    "value": float(sys_bp),
                                    "unit": "mmHg",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "mm[Hg]"
                                }
                            },
                            {
                                "code": {
                                    "coding": [
                                        {"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}
                                    ]
                                },
                                "valueQuantity": {
                                    "value": float(dia_bp),
                                    "unit": "mmHg",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "mm[Hg]"
                                }
                            }
                        ]
                    },
                    "request": {"method": "POST", "url": "Observation"}
                }
            ]
        }

        # Validate before writing
        validate_fhir_bundle(bundle_json)

        bundle_path = output_dir / f"patient_{i:04d}_{config.seed}.json"
        bundle_path.write_text(json.dumps(bundle_json, indent=2, sort_keys=True), encoding="utf-8")
        generated_files.append(bundle_path)

    return generated_files
