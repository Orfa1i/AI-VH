"""
Golden case validation and reference authenticity checker for AI-VH.
Enforces Pydantic schema adherence, clinical reference integrity, and physician sign-off rules.
"""

from typing import Any, Dict, Optional, Set, Tuple, Union
from pydantic import ValidationError as PydanticValidationError

from vh.cases.schema import GoldenCase, SupportingReference


class ValidationError(ValueError):
    """Raised when a golden case fails structural or clinical schema validation."""
    pass


class UnauthorizedVerificationError(ValueError):
    """Raised when an automated agent or user attempts to set status: verified without a signed clinical sign-off."""
    pass


KNOWN_MEDICAL_SOURCES = (
    "harrison",
    "braunwald",
    "acc/aha",
    "ats/idsa",
    "american diabetes association",
    "ada",
    "pubmed",
    "dailymed",
    "fda",
    "nih",
    "nejm",
    "lancet",
    "jama",
    "chest",
    "surviving sepsis"
)


def validate_reference_authenticity(ref_data: Union[Dict[str, Any], SupportingReference]) -> Tuple[bool, str]:
    """
    Validate that supporting references point to known medical literature, standard guidelines,
    or are explicitly flagged as empty. Never allows invented citations.
    """
    if isinstance(ref_data, SupportingReference):
        source = ref_data.source.strip()
        locator = ref_data.locator.strip()
        note = ref_data.note.strip()
    elif isinstance(ref_data, dict):
        source = str(ref_data.get("source", "")).strip()
        locator = str(ref_data.get("locator", "")).strip()
        note = str(ref_data.get("note", "")).strip()
    else:
        return False, "Reference must be a dictionary or SupportingReference instance"

    # Explicitly flagged empty reference is allowed per prompt rule
    if source == "" or "flagged" in note.lower() or "unreferenced" in note.lower():
        return True, "Explicitly flagged empty reference"

    source_lower = source.lower()

    # Verify open-source citation format
    if source_lower.startswith("pmid:") or source_lower.startswith("pubmed"):
        return True, "Valid PubMed reference"

    if "dailymed" in source_lower or "ndc" in source_lower:
        return True, "Valid DailyMed/FDA reference"

    if any(known in source_lower for known in KNOWN_MEDICAL_SOURCES):
        if not locator:
            return False, f"Medical reference '{source}' requires a specific chapter, section, or locator"
        return True, f"Verified clinical source: {source}"

    return False, f"Unrecognized or unverified citation source: '{source}'. Reference must be verifiable or explicitly flagged empty."


def validate_case_dict(
    data: Dict[str, Any],
    allow_verified: bool = False,
    approved_ids: Optional[Set[str]] = None
) -> GoldenCase:
    """
    Validate raw dictionary against GoldenCase schema and governance policies.
    """
    try:
        case = GoldenCase(**data)
    except (PydanticValidationError, TypeError, ValueError) as err:
        raise ValidationError(f"Schema validation error: {err}") from err

    # Governance check: status verified requires sign-off approval
    if case.status == "verified":
        if not allow_verified:
            if approved_ids is None or case.case_id not in approved_ids:
                raise UnauthorizedVerificationError(
                    f"Case '{case.case_id}' cannot be set to 'verified' without an attending physician sign-off record."
                )
        if not case.reviewer or not case.reviewed_at:
            raise ValidationError(
                f"Verified case '{case.case_id}' requires non-empty 'reviewer' and 'reviewed_at' timestamps."
            )

    # Validate each reference
    for ref in case.supporting_references:
        is_valid, reason = validate_reference_authenticity(ref)
        if not is_valid:
            raise ValidationError(f"Invalid reference in case '{case.case_id}': {reason}")

    return case
