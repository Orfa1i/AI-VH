"""
FHIR R4 Adapter for Synthea Synthetic Patient Bundles.
Parses, normalizes, and maps multi-resource transaction bundles into internal
domain models and a unified chronological clinical timeline.

Supported FHIR R4 Resources:
- Patient
- Encounter
- Condition
- Observation (vitals and laboratory)
- MedicationRequest
- AllergyIntolerance
- Procedure
- Immunization
- CarePlan
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """Normalized clinical timeline event extracted from a FHIR R4 resource."""
    id: str
    resource_type: str
    category: str = Field(
        ...,
        description="Category: encounter, condition, observation, medication, allergy, procedure, immunization, careplan"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp for sorting")
    display_date: str = Field(..., description="Human-readable date format")
    title: str
    subtitle: Optional[str] = None
    status: Optional[str] = None
    code: Optional[str] = None
    system: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class DemoPatientSummary(BaseModel):
    """High-level summary card for synthetic patient lists and directory views."""
    id: str
    mrn: str
    name: str
    gender: str
    birth_date: str
    age: int
    city: str
    state: str
    active_condition_count: int = 0
    encounter_count: int = 0
    observation_count: int = 0
    medication_count: int = 0
    allergy_count: int = 0
    procedure_count: int = 0
    immunization_count: int = 0
    care_plan_count: int = 0
    primary_diagnoses: List[str] = Field(default_factory=list)


class DemoPatientProfile(BaseModel):
    """Complete structured medical profile mapped from FHIR R4 resources."""
    id: str
    mrn: str
    name: str
    gender: str
    birth_date: str
    age: int
    city: str
    state: str
    country: str = "US"
    demographics: Dict[str, Any] = Field(default_factory=dict)
    active_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    past_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_encounters: List[Dict[str, Any]] = Field(default_factory=list)
    current_medications: List[Dict[str, Any]] = Field(default_factory=list)
    allergies: List[Dict[str, Any]] = Field(default_factory=list)
    latest_vitals: Dict[str, Any] = Field(default_factory=dict)
    recent_labs: List[Dict[str, Any]] = Field(default_factory=list)
    procedures: List[Dict[str, Any]] = Field(default_factory=list)
    immunizations: List[Dict[str, Any]] = Field(default_factory=list)
    care_plans: List[Dict[str, Any]] = Field(default_factory=list)
    total_timeline_events: int = 0


class TimelineResponse(BaseModel):
    """Response payload for the unified chronological patient timeline endpoint."""
    patient_id: str
    patient_name: str
    total_events: int
    events: List[TimelineEvent]


def calculate_age(birth_date_str: str, ref_date_str: Optional[str] = None) -> int:
    """Calculate age in years from birth date string."""
    try:
        b_dt = datetime.strptime(birth_date_str[:10], "%Y-%m-%d")
        if ref_date_str:
            ref_dt = datetime.strptime(ref_date_str[:10], "%Y-%m-%d")
        else:
            ref_dt = datetime.now()
        age = ref_dt.year - b_dt.year - ((ref_dt.month, ref_dt.day) < (b_dt.month, b_dt.day))
        return max(0, age)
    except Exception:
        return 0


def format_codeable_concept(cc: Optional[Dict[str, Any]]) -> Tuple[str, str, str]:
    """
    Extract (display, code, system) from a FHIR CodeableConcept structure.
    Returns fallback strings if missing.
    """
    if not cc or not isinstance(cc, dict):
        return ("Unknown", "", "")

    display = cc.get("text", "")
    code = ""
    system = ""

    codings = cc.get("coding", [])
    if isinstance(codings, list) and len(codings) > 0:
        first = codings[0]
        if isinstance(first, dict):
            if not display:
                display = first.get("display", "")
            code = str(first.get("code", ""))
            system = str(first.get("system", ""))

    if not display:
        display = code or "Unspecified"

    return (display, code, system)


def extract_iso_timestamp(resource: Dict[str, Any]) -> str:
    """Extract best available timestamp from FHIR resource for timeline sorting."""
    # Check common FHIR date fields in order of specificity
    candidates = [
        resource.get("effectiveDateTime"),
        resource.get("recordedDate"),
        resource.get("authoredOn"),
        resource.get("occurrenceDateTime"),
        resource.get("onsetDateTime"),
        resource.get("performedDateTime"),
    ]

    for c in candidates:
        if c and isinstance(c, str):
            return c

    # Check period objects
    period = resource.get("period") or resource.get("performedPeriod")
    if isinstance(period, dict) and period.get("start"):
        return str(period["start"])

    # Check dateAsserted or date
    if resource.get("date") and isinstance(resource["date"], str):
        return resource["date"]

    return "2026-01-01T00:00:00Z"


def clean_display_date(iso_str: str) -> str:
    """Converts ISO timestamp into readable YYYY-MM-DD or YYYY-MM-DD HH:MM."""
    if not iso_str:
        return "N/A"
    clean = iso_str.replace("T", " ").replace("Z", "")
    if len(clean) > 16:
        return clean[:16]
    return clean[:10]


class FHIRR4Adapter:
    """
    Parses and translates FHIR R4 Bundle into internal patient summary,
    full medical profile, and unified clinical timeline.
    """

    @classmethod
    def parse_bundle(
        cls,
        bundle_dict: Dict[str, Any]
    ) -> Tuple[DemoPatientProfile, List[TimelineEvent]]:
        """
        Parses a FHIR R4 Bundle dictionary and returns both the structured
        DemoPatientProfile and the complete sorted List of TimelineEvents.
        """
        if not isinstance(bundle_dict, dict) or bundle_dict.get("resourceType") != "Bundle":
            raise ValueError("Input data is not a valid FHIR R4 Bundle")

        entries = bundle_dict.get("entry", [])
        if not isinstance(entries, list):
            raise ValueError("FHIR Bundle has no entries")

        # Bucket resources by resourceType
        resources_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for entry in entries:
            res = entry.get("resource")
            if isinstance(res, dict) and "resourceType" in res:
                rtype = res["resourceType"]
                if rtype not in resources_by_type:
                    resources_by_type[rtype] = []
                resources_by_type[rtype].append(res)

        # 1. Parse Patient
        patient_list = resources_by_type.get("Patient", [])
        if not patient_list:
            raise ValueError("FHIR Bundle contains no Patient resource")

        patient_res = patient_list[0]
        patient_id = patient_res.get("id", "PAT-SYNTH-UNKNOWN")

        # MRN / Identifier
        mrn = f"MRN-{patient_id}"
        identifiers = patient_res.get("identifier", [])
        if isinstance(identifiers, list):
            for ident in identifiers:
                if isinstance(ident, dict) and ident.get("value"):
                    mrn = str(ident["value"])
                    break

        # Name
        first_name = "Synthetic"
        last_name = "Patient"
        name_list = patient_res.get("name", [])
        if isinstance(name_list, list) and len(name_list) > 0:
            name_obj = name_list[0]
            if isinstance(name_obj, dict):
                last_name = name_obj.get("family", last_name)
                given = name_obj.get("given", [])
                if isinstance(given, list) and len(given) > 0:
                    first_name = " ".join(str(g) for g in given)
                elif isinstance(given, str):
                    first_name = given

        full_name = f"{first_name} {last_name}".strip()
        gender = str(patient_res.get("gender", "unknown")).lower()
        birth_date = str(patient_res.get("birthDate", "1980-01-01"))
        age = calculate_age(birth_date)

        # Address
        city = "Metropolis"
        state = "State"
        country = "US"
        addresses = patient_res.get("address", [])
        if isinstance(addresses, list) and len(addresses) > 0:
            addr = addresses[0]
            if isinstance(addr, dict):
                city = addr.get("city", city)
                state = addr.get("state", state)
                country = addr.get("country", country)

        demographics = {
            "telecom": patient_res.get("telecom", []),
            "maritalStatus": patient_res.get("maritalStatus", {}).get("text", "Unknown"),
            "language": "en-US",
            "city": city,
            "state": state,
            "country": country,
        }

        # Containers for profile
        active_conditions: List[Dict[str, Any]] = []
        past_conditions: List[Dict[str, Any]] = []
        recent_encounters: List[Dict[str, Any]] = []
        current_medications: List[Dict[str, Any]] = []
        allergies: List[Dict[str, Any]] = []
        latest_vitals: Dict[str, Any] = {}
        recent_labs: List[Dict[str, Any]] = []
        procedures: List[Dict[str, Any]] = []
        immunizations: List[Dict[str, Any]] = []
        care_plans: List[Dict[str, Any]] = []

        timeline_events: List[TimelineEvent] = []

        # 2. Parse Encounters
        for enc in resources_by_type.get("Encounter", []):
            enc_id = enc.get("id", f"enc-{len(recent_encounters)}")
            ts = extract_iso_timestamp(enc)
            status = enc.get("status", "finished")
            enc_class = "ambulatory"
            c_obj = enc.get("class")
            if isinstance(c_obj, dict):
                enc_class = c_obj.get("code") or c_obj.get("display") or enc_class
            elif isinstance(c_obj, list) and len(c_obj) > 0:
                enc_class = c_obj[0].get("code") or c_obj[0].get("display") or enc_class

            # Title & Reason
            reason_display = "Clinical Encounter"
            reasons = enc.get("reasonCode", [])
            if isinstance(reasons, list) and len(reasons) > 0:
                disp, _, _ = format_codeable_concept(reasons[0])
                if disp:
                    reason_display = disp

            title = f"{enc_class.title()} Encounter: {reason_display}"
            participant_name = "Medical Team"
            participants = enc.get("participant", [])
            if isinstance(participants, list) and len(participants) > 0:
                actor = participants[0].get("actor", {})
                if isinstance(actor, dict) and actor.get("display"):
                    participant_name = actor["display"]

            enc_dict = {
                "id": enc_id,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
                "class": enc_class,
                "status": status,
                "reason": reason_display,
                "provider": participant_name,
            }
            recent_encounters.append(enc_dict)

            timeline_events.append(TimelineEvent(
                id=enc_id,
                resource_type="Encounter",
                category="encounter",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=title,
                subtitle=f"Provider: {participant_name}",
                status=status,
                details=enc_dict
            ))

        # 3. Parse Conditions
        for cond in resources_by_type.get("Condition", []):
            cond_id = cond.get("id", f"cond-{len(active_conditions)}")
            ts = extract_iso_timestamp(cond)
            display, code, system = format_codeable_concept(cond.get("code"))

            # Clinical status
            clin_status = "active"
            cs_obj = cond.get("clinicalStatus")
            if isinstance(cs_obj, dict):
                coding = cs_obj.get("coding", [])
                if isinstance(coding, list) and len(coding) > 0:
                    clin_status = coding[0].get("code", clin_status)

            cond_dict = {
                "id": cond_id,
                "name": display,
                "code": code,
                "system": system,
                "status": clin_status,
                "onset": ts,
                "display_date": clean_display_date(ts),
            }

            if clin_status in ("active", "recurrence", "relapse"):
                active_conditions.append(cond_dict)
            else:
                past_conditions.append(cond_dict)

            timeline_events.append(TimelineEvent(
                id=cond_id,
                resource_type="Condition",
                category="condition",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=f"Diagnosis: {display}",
                subtitle=f"Code: {code} ({system})",
                status=clin_status,
                code=code,
                system=system,
                details=cond_dict
            ))

        # 4. Parse Observations (vitals vs laboratory)
        for obs in resources_by_type.get("Observation", []):
            obs_id = obs.get("id", f"obs-{len(timeline_events)}")
            ts = extract_iso_timestamp(obs)
            display, code, system = format_codeable_concept(obs.get("code"))
            status = obs.get("status", "final")

            # Category check
            is_vital = False
            cat_list = obs.get("category", [])
            if isinstance(cat_list, list):
                for cat in cat_list:
                    if isinstance(cat, dict):
                        for c in cat.get("coding", []):
                            if c.get("code") == "vital-signs":
                                is_vital = True
                                break

            # Check value or components
            val_str = ""
            unit_str = ""
            val_qty = obs.get("valueQuantity")
            if isinstance(val_qty, dict):
                val_str = str(val_qty.get("value", ""))
                unit_str = str(val_qty.get("unit", ""))
            elif obs.get("valueCodeableConcept"):
                val_str, _, _ = format_codeable_concept(obs.get("valueCodeableConcept"))
            elif obs.get("valueString"):
                val_str = obs.get("valueString")

            # Check multi-component observations (e.g. Blood Pressure)
            components = obs.get("component", [])
            comp_details = []
            if isinstance(components, list) and len(components) > 0:
                for comp in components:
                    c_disp, c_code, _ = format_codeable_concept(comp.get("code"))
                    c_qty = comp.get("valueQuantity", {})
                    c_val = c_qty.get("value", "")
                    c_unit = c_qty.get("unit", "")
                    comp_details.append({"name": c_disp, "code": c_code, "value": c_val, "unit": c_unit})
                if not val_str and len(comp_details) >= 2:
                    val_str = f"{comp_details[0]['value']}/{comp_details[1]['value']}"
                    unit_str = comp_details[0]['unit']

            formatted_title = f"{display}: {val_str} {unit_str}".strip()

            obs_dict = {
                "id": obs_id,
                "name": display,
                "code": code,
                "system": system,
                "value": val_str,
                "unit": unit_str,
                "status": status,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
                "is_vital": is_vital,
                "components": comp_details
            }

            # Map into latest_vitals or recent_labs
            if is_vital:
                # Update latest vitals record
                norm_key = display.lower().replace(" ", "_")
                latest_vitals[norm_key] = f"{val_str} {unit_str}".strip()
            else:
                recent_labs.append(obs_dict)

            timeline_events.append(TimelineEvent(
                id=obs_id,
                resource_type="Observation",
                category="observation",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=formatted_title,
                subtitle=f"LOINC {code} | {status}",
                status=status,
                code=code,
                system=system,
                details=obs_dict
            ))

        # 5. Parse MedicationRequests
        for med in resources_by_type.get("MedicationRequest", []):
            med_id = med.get("id", f"med-{len(current_medications)}")
            ts = extract_iso_timestamp(med)
            display, code, system = format_codeable_concept(med.get("medicationCodeableConcept"))
            status = med.get("status", "active")

            dosage_text = ""
            dosage_inst = med.get("dosageInstruction", [])
            if isinstance(dosage_inst, list) and len(dosage_inst) > 0:
                first_d = dosage_inst[0]
                if isinstance(first_d, dict):
                    dosage_text = first_d.get("text", "")

            med_dict = {
                "id": med_id,
                "name": display,
                "code": code,
                "system": system,
                "status": status,
                "dosage": dosage_text,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
            }

            if status == "active":
                current_medications.append(med_dict)

            timeline_events.append(TimelineEvent(
                id=med_id,
                resource_type="MedicationRequest",
                category="medication",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=f"Medication: {display}",
                subtitle=dosage_text or f"Status: {status}",
                status=status,
                code=code,
                system=system,
                details=med_dict
            ))

        # 6. Parse AllergyIntolerances
        for alg in resources_by_type.get("AllergyIntolerance", []):
            alg_id = alg.get("id", f"alg-{len(allergies)}")
            ts = extract_iso_timestamp(alg)
            display, code, system = format_codeable_concept(alg.get("code"))
            criticality = alg.get("criticality", "low")
            clin_status = "active"
            cs_obj = alg.get("clinicalStatus")
            if isinstance(cs_obj, dict):
                coding = cs_obj.get("coding", [])
                if isinstance(coding, list) and len(coding) > 0:
                    clin_status = coding[0].get("code", clin_status)

            alg_dict = {
                "id": alg_id,
                "substance": display,
                "code": code,
                "system": system,
                "criticality": criticality,
                "status": clin_status,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
            }
            allergies.append(alg_dict)

            timeline_events.append(TimelineEvent(
                id=alg_id,
                resource_type="AllergyIntolerance",
                category="allergy",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=f"Allergy: {display}",
                subtitle=f"Criticality: {criticality} | Status: {clin_status}",
                status=clin_status,
                code=code,
                system=system,
                details=alg_dict
            ))

        # 7. Parse Procedures
        for proc in resources_by_type.get("Procedure", []):
            proc_id = proc.get("id", f"proc-{len(procedures)}")
            ts = extract_iso_timestamp(proc)
            display, code, system = format_codeable_concept(proc.get("code"))
            status = proc.get("status", "completed")

            proc_dict = {
                "id": proc_id,
                "name": display,
                "code": code,
                "system": system,
                "status": status,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
            }
            procedures.append(proc_dict)

            timeline_events.append(TimelineEvent(
                id=proc_id,
                resource_type="Procedure",
                category="procedure",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=f"Procedure: {display}",
                subtitle=f"Status: {status} | Code: {code}",
                status=status,
                code=code,
                system=system,
                details=proc_dict
            ))

        # 8. Parse Immunizations
        for imm in resources_by_type.get("Immunization", []):
            imm_id = imm.get("id", f"imm-{len(immunizations)}")
            ts = extract_iso_timestamp(imm)
            display, code, system = format_codeable_concept(imm.get("vaccineCode"))
            status = imm.get("status", "completed")

            imm_dict = {
                "id": imm_id,
                "vaccine": display,
                "code": code,
                "system": system,
                "status": status,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
            }
            immunizations.append(imm_dict)

            timeline_events.append(TimelineEvent(
                id=imm_id,
                resource_type="Immunization",
                category="immunization",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=f"Immunization: {display}",
                subtitle=f"CVX: {code} | Status: {status}",
                status=status,
                code=code,
                system=system,
                details=imm_dict
            ))

        # 9. Parse CarePlans
        for cp in resources_by_type.get("CarePlan", []):
            cp_id = cp.get("id", f"cp-{len(care_plans)}")
            ts = extract_iso_timestamp(cp)
            title = cp.get("title") or "Care Plan"
            category_list = cp.get("category", [])
            if isinstance(category_list, list) and len(category_list) > 0:
                c_disp, _, _ = format_codeable_concept(category_list[0])
                if c_disp and c_disp != "Unspecified":
                    title = f"Care Plan: {c_disp}"

            status = cp.get("status", "active")
            intent = cp.get("intent", "order")

            activities = []
            for act in cp.get("activity", []):
                if isinstance(act, dict):
                    detail = act.get("detail", {})
                    if isinstance(detail, dict):
                        act_code = detail.get("code")
                        act_disp, _, _ = format_codeable_concept(act_code)
                        activities.append(act_disp)

            cp_dict = {
                "id": cp_id,
                "title": title,
                "status": status,
                "intent": intent,
                "timestamp": ts,
                "display_date": clean_display_date(ts),
                "activities": activities,
            }
            care_plans.append(cp_dict)

            timeline_events.append(TimelineEvent(
                id=cp_id,
                resource_type="CarePlan",
                category="careplan",
                timestamp=ts,
                display_date=clean_display_date(ts),
                title=title,
                subtitle=f"Status: {status} | Activities: {len(activities)}",
                status=status,
                details=cp_dict
            ))

        # Sort timeline events chronologically descending (newest first)
        timeline_events.sort(key=lambda e: e.timestamp, reverse=True)

        profile = DemoPatientProfile(
            id=patient_id,
            mrn=mrn,
            name=full_name,
            gender=gender,
            birth_date=birth_date,
            age=age,
            city=city,
            state=state,
            country=country,
            demographics=demographics,
            active_conditions=active_conditions,
            past_conditions=past_conditions,
            recent_encounters=recent_encounters,
            current_medications=current_medications,
            allergies=allergies,
            latest_vitals=latest_vitals,
            recent_labs=recent_labs[:25],
            procedures=procedures,
            immunizations=immunizations,
            care_plans=care_plans,
            total_timeline_events=len(timeline_events),
        )

        return (profile, timeline_events)

    @classmethod
    def to_summary(
        cls,
        profile: DemoPatientProfile
    ) -> DemoPatientSummary:
        """Converts full patient profile into a lightweight summary card."""
        primary_diagnoses = [c["name"] for c in profile.active_conditions[:3]]
        return DemoPatientSummary(
            id=profile.id,
            mrn=profile.mrn,
            name=profile.name,
            gender=profile.gender,
            birth_date=profile.birth_date,
            age=profile.age,
            city=profile.city,
            state=profile.state,
            active_condition_count=len(profile.active_conditions),
            encounter_count=len(profile.recent_encounters),
            observation_count=profile.total_timeline_events - len(profile.active_conditions) - len(profile.recent_encounters),
            medication_count=len(profile.current_medications),
            allergy_count=len(profile.allergies),
            procedure_count=len(profile.procedures),
            immunization_count=len(profile.immunizations),
            care_plan_count=len(profile.care_plans),
            primary_diagnoses=primary_diagnoses,
        )
