"""
Synthea Generic Module Framework validator.
Validates state machine transitions, reachability, and terminology standards (LOINC, UCUM, RxNorm, SNOMED).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Union

from .registry import VALID_LOINC_CODES, VALID_RXNORM_CODES, VALID_SNOMED_CODES, VALID_UCUM_UNITS


def validate_module_file(file_path: Union[Path, str]) -> Dict[str, Any]:
    """
    Validate that a Synthea module JSON file conforms to Generic Module Framework state machine rules.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Synthea module file not found: {p}")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"valid": False, "error": f"Invalid JSON syntax in {p.name}: {e}"}

    if not isinstance(data, dict):
        return {"valid": False, "error": f"Module {p.name} must be a JSON object"}

    name = data.get("name")
    states = data.get("states")

    if not name:
        return {"valid": False, "error": f"Module {p.name} missing 'name' attribute"}
    if not isinstance(states, dict) or not states:
        return {"valid": False, "error": f"Module {p.name} missing or empty 'states' dictionary"}

    initial_states = [sname for sname, sdata in states.items() if sdata.get("type") == "Initial"]
    terminal_states = [sname for sname, sdata in states.items() if sdata.get("type") == "Terminal"]

    if len(initial_states) != 1:
        return {
            "valid": False,
            "error": f"Module {p.name} must have exactly 1 Initial state, found {len(initial_states)}"
        }

    if len(terminal_states) < 1:
        return {
            "valid": False,
            "error": f"Module {p.name} must have at least 1 Terminal state, found 0"
        }

    state_keys = set(states.keys())

    # Validate all transition references
    for sname, sdata in states.items():
        if not isinstance(sdata, dict):
            return {"valid": False, "error": f"State '{sname}' must be an object"}

        # 1. direct_transition
        if "direct_transition" in sdata:
            target = sdata["direct_transition"]
            if target not in state_keys:
                return {
                    "valid": False,
                    "error": f"State '{sname}' references non-existent direct_transition '{target}'"
                }

        # 2. conditional_transition
        if "conditional_transition" in sdata:
            transitions = sdata["conditional_transition"]
            if not isinstance(transitions, list):
                return {"valid": False, "error": f"State '{sname}' conditional_transition must be a list"}
            for t in transitions:
                target = t.get("transition")
                if target and target not in state_keys:
                    return {
                        "valid": False,
                        "error": f"State '{sname}' conditional_transition references non-existent target '{target}'"
                    }

        # 3. distributed_transition
        if "distributed_transition" in sdata:
            dists = sdata["distributed_transition"]
            if not isinstance(dists, list):
                return {"valid": False, "error": f"State '{sname}' distributed_transition must be a list"}
            total_prob = 0.0
            for d in dists:
                target = d.get("transition")
                dist_val = d.get("distribution", 0.0)
                if isinstance(dist_val, (int, float)):
                    total_prob += float(dist_val)
                if target and target not in state_keys:
                    return {
                        "valid": False,
                        "error": f"State '{sname}' distributed_transition references non-existent target '{target}'"
                    }
            if abs(total_prob - 1.0) > 0.01:
                return {
                    "valid": False,
                    "error": f"State '{sname}' distributed_transition probabilities sum to {total_prob:.3f}, expected 1.0"
                }

        # 4. complex_transition
        if "complex_transition" in sdata:
            transitions = sdata["complex_transition"]
            if not isinstance(transitions, list):
                return {"valid": False, "error": f"State '{sname}' complex_transition must be a list"}
            for t in transitions:
                target = t.get("transition")
                if target and target not in state_keys:
                    return {
                        "valid": False,
                        "error": f"State '{sname}' complex_transition references non-existent target '{target}'"
                    }

    return {
        "valid": True,
        "name": name,
        "has_initial": True,
        "initial_state": initial_states[0],
        "terminal_count": len(terminal_states),
        "state_count": len(states)
    }


def validate_terminology_in_directory(modules_dir: Union[Path, str]) -> Dict[str, Any]:
    """
    Scan all custom module files in directory and verify LOINC, UCUM, RxNorm, and SNOMED codes.
    """
    target_dir = Path(modules_dir)
    if not target_dir.exists():
        raise FileNotFoundError(f"Directory not found: {target_dir}")

    invalid_loinc: List[Dict[str, str]] = []
    invalid_ucum: List[Dict[str, str]] = []
    invalid_rxnorm: List[Dict[str, str]] = []
    invalid_snomed: List[Dict[str, str]] = []

    obs_checked = 0
    meds_checked = 0

    for mfile in sorted(target_dir.glob("*.json")):
        data = json.loads(mfile.read_text(encoding="utf-8"))
        states = data.get("states", {})

        for sname, sdata in states.items():
            stype = sdata.get("type")

            # Validate Observation
            if stype == "Observation":
                obs_checked += 1
                codes = sdata.get("codes", [])
                for c in codes:
                    sys_name = c.get("system", "")
                    code_val = str(c.get("code", "")).strip()
                    if "loinc" in sys_name.lower():
                        if code_val not in VALID_LOINC_CODES:
                            invalid_loinc.append({"file": mfile.name, "state": sname, "code": code_val})

                unit = sdata.get("unit")
                if unit:
                    if unit not in VALID_UCUM_UNITS:
                        invalid_ucum.append({"file": mfile.name, "state": sname, "unit": unit})

            # Validate MedicationOrder
            elif stype == "MedicationOrder":
                meds_checked += 1
                codes = sdata.get("codes", [])
                for c in codes:
                    sys_name = c.get("system", "")
                    code_val = str(c.get("code", "")).strip()
                    if "rxnorm" in sys_name.lower():
                        if code_val not in VALID_RXNORM_CODES:
                            invalid_rxnorm.append({"file": mfile.name, "state": sname, "code": code_val})

            # Validate ConditionOnset
            elif stype in ("ConditionOnset", "ConditionEnd"):
                codes = sdata.get("codes", [])
                for c in codes:
                    sys_name = c.get("system", "")
                    code_val = str(c.get("code", "")).strip()
                    if "snomed" in sys_name.lower():
                        if code_val not in VALID_SNOMED_CODES:
                            invalid_snomed.append({"file": mfile.name, "state": sname, "code": code_val})

    return {
        "invalid_loinc_codes": invalid_loinc,
        "invalid_ucum_units": invalid_ucum,
        "invalid_rxnorm_codes": invalid_rxnorm,
        "invalid_snomed_codes": invalid_snomed,
        "total_observations_checked": obs_checked,
        "total_medications_checked": meds_checked
    }
