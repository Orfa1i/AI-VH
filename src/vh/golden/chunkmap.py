"""
Chunk-map sign-off importer for AI-VH (updated STEP-18).

`vh golden chunkmap-import` applies the corrections listed in the H2 sign-off
(`docs/signoffs/H2-chunkmap.md`) to the chunk map exactly as written -- no
other entries change. A sign-off listing no corrections is a byte-identical
no-op. Corrections matching nothing abort without writing (fail closed).

Machine-readable correction lines inside the sign-off:
    - CHUNGMAP-CORRECTION: <case_id> | <locator substring> | <field> = <value>
Editable fields: status, matched_doc_id, reason.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

CORRECTION_PREFIX = "CHUNGMAP-CORRECTION:"
EDITABLE_FIELDS = {"status", "matched_doc_id", "reason"}

_CORRECTION_RE = re.compile(
    r"^\s*-\s*CHUNGMAP-CORRECTION:\s*(?P<case>[^|]+?)\s*\|\s*(?P<locator>[^|]+?)\s*\|\s*"
    r"(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.+?)\s*$"
)


def _coerce_value(raw: str) -> Any:
    text = raw.strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def parse_chunkmap_corrections(signoff_text: str) -> List[Dict[str, Any]]:
    """Extract machine-readable correction directives from a sign-off document."""
    corrections: List[Dict[str, Any]] = []
    for line in signoff_text.splitlines():
        match = _CORRECTION_RE.match(line)
        if not match:
            continue
        field = match.group("field").strip()
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"Chunk-map field is not editable: {field!r}")
        corrections.append(
            {
                "case_id": match.group("case").strip(),
                "locator": match.group("locator").strip(),
                "field": field,
                "value": _coerce_value(match.group("value")),
            }
        )
    return corrections


def apply_chunkmap_corrections(signoff_path: str, chunkmap_path: str) -> Dict[str, Any]:
    """Apply listed corrections to the chunk map file. Returns a summary dict."""
    signoff_file = Path(signoff_path)
    map_file = Path(chunkmap_path)
    corrections = parse_chunkmap_corrections(signoff_file.read_text(encoding="utf-8"))
    if not corrections:
        return {
            "signoff_file": str(signoff_file),
            "chunkmap_file": str(map_file),
            "corrections_applied": 0,
        }

    doc = json.loads(map_file.read_text(encoding="utf-8"))
    mappings = doc.get("case_mappings", {})
    applied = 0
    for correction in corrections:
        case = mappings.get(correction["case_id"])
        if case is None:
            raise KeyError(f"Chunk-map case not found: {correction['case_id']!r}")
        matched = [
            ref
            for ref in case.get("supporting_references", [])
            if correction["locator"] in str(ref.get("locator", ""))
        ]
        if not matched:
            raise KeyError(
                f"No reference with locator {correction['locator']!r} in "
                f"case {correction['case_id']!r}"
            )
        for ref in matched:
            ref[correction["field"]] = correction["value"]
            applied += 1

    map_file.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "signoff_file": str(signoff_file),
        "chunkmap_file": str(map_file),
        "corrections_applied": applied,
    }
