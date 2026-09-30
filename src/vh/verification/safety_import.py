"""
Safety-table sign-off importer for AI-VH (updated STEP-25).

`vh safety import-signoff` reads the H4 sign-off (`docs/signoffs/H4-*.md`) and,
exactly as listed there:
- sets `status: reviewed` (plus reviewer/date) on tables whose section ends
  with `Verdict: APPROVED` -- every other table stays draft;
- updates corrected rows exactly as written.

Machine-readable row corrections inside the sign-off:
    - SAFETY-CORRECTION: <table-file> | <id-field>=<id-value> | <field> = <value>

Edits are surgical line replacements so curated file comments and formatting
survive. Everything is validated before anything is written (fail closed).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

CORRECTION_PREFIX = "SAFETY-CORRECTION:"

_CORRECTION_RE = re.compile(
    r"^\s*-\s*SAFETY-CORRECTION:\s*(?P<file>[A-Za-z0-9_.-]+\.yaml)\s*\|\s*"
    r"(?P<idfield>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<idvalue>[^|]+?)\s*\|\s*"
    r"(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.+?)\s*$"
)
_TABLE_REF_RE = re.compile(r"(?:configs/safety/|`)([A-Za-z0-9_.-]+\.yaml)`?")
_APPROVAL_RE = re.compile(r"verdict:\W*approved\b", re.IGNORECASE)
_REVIEWER_RE = re.compile(r"\*\*Reviewer:\*\*\s*(.+?)\s*$", re.MULTILINE)
_DATE_RE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


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


def _yaml_scalar(value: Any) -> str:
    return yaml.safe_dump(value, default_flow_style=False).strip().splitlines()[0]


def parse_safety_corrections(signoff_text: str) -> List[Dict[str, Any]]:
    """Extract machine-readable row corrections from a sign-off document."""
    corrections: List[Dict[str, Any]] = []
    for line in signoff_text.splitlines():
        match = _CORRECTION_RE.match(line)
        if not match:
            continue
        corrections.append(
            {
                "file": match.group("file"),
                "id_field": match.group("idfield"),
                "id_value": match.group("idvalue").strip(),
                "field": match.group("field").strip(),
                "value": _coerce_value(match.group("value")),
            }
        )
    return corrections


def _split_sections(signoff_text: str) -> List[str]:
    """Split into `##`-heading blocks and numbered-item blocks.

    Verdicts bind to their own block, so a mixed-verdict section (like the
    real H4 audit, with one numbered item per table) cannot cross-approve.
    """
    parts = re.split(r"(?m)^(?=##\s+|\d+\.\s+)", signoff_text)
    return [part for part in parts if part.strip()]


def parse_table_approvals(signoff_text: str, known_files: List[str]) -> List[str]:
    """Table files whose section carries a `Verdict: APPROVED` marker."""
    known = set(known_files)
    approved: List[str] = []
    for section in _split_sections(signoff_text):
        if not _APPROVAL_RE.search(section):
            continue
        for hit in _TABLE_REF_RE.findall(section):
            if hit in known and hit not in approved:
                approved.append(hit)
    return approved


def _parse_header(signoff_text: str) -> Tuple[str, str]:
    reviewer_match = _REVIEWER_RE.search(signoff_text)
    date_match = _DATE_RE.search(signoff_text)
    reviewer = reviewer_match.group(1).strip() if reviewer_match else "unknown"
    reviewed_at = date_match.group(1) if date_match else "unknown"
    return reviewer, reviewed_at


def _metadata_block(lines: List[str]) -> Tuple[int, int]:
    """(start, end) line indices of the top-level `metadata:` mapping."""
    start = next(i for i, line in enumerate(lines) if line.startswith("metadata:"))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if not lines[i].startswith((" ", "\t")):
            end = i
            break
    return start, end


def _set_mapping_scalar(lines: List[str], start: int, end: int, key: str, value: str) -> None:
    """Replace or insert `key: value` inside lines[start:end] (in place)."""
    end = min(end, len(lines))
    pattern = re.compile(rf"^(\s*){re.escape(key)}\s*:.*$")
    for i in range(start, end):
        match = pattern.match(lines[i])
        if match:
            lines[i] = f"{match.group(1)}{key}: {value}"
            return
    indent = "  "
    for i in range(start + 1, end):
        stripped = lines[i].strip()
        if stripped != "" and not stripped.startswith("#"):
            indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
            break
    lines.insert(start + 1, f"{indent}{key}: {value}")


def _apply_metadata_approval(text: str, reviewer: str, reviewed_at: str) -> str:
    lines = text.split("\n")
    start, end = _metadata_block(lines)
    _set_mapping_scalar(lines, start, end, "status", '"reviewed"')
    _set_mapping_scalar(lines, start, end + 2, "reviewer", _yaml_scalar(reviewer))
    _set_mapping_scalar(lines, start, end + 3, "reviewed_at", _yaml_scalar(reviewed_at))
    return "\n".join(lines)


def _strip_quotes(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def _apply_row_correction(text: str, id_field: str, id_value: str, field: str, value: Any) -> str:
    """Surgically set one row scalar; raises KeyError when the row is absent."""
    lines = text.split("\n")
    dash_index: Optional[int] = None
    dash_indent = ""
    id_pattern = re.compile(rf"^(\s*)-\s+{re.escape(id_field)}\s*:(.*)$")
    for i, line in enumerate(lines):
        match = id_pattern.match(line)
        if match and _strip_quotes(match.group(2)) == id_value:
            dash_index, dash_indent = i, match.group(1)
            break
    if dash_index is None:
        raise KeyError(f"Row {id_field}={id_value!r} not found.")
    content_indent = dash_indent + "  "
    field_pattern = re.compile(rf"^{re.escape(content_indent)}{re.escape(field)}\s*:.*$")
    i = dash_index + 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "" or line.strip().startswith("#"):
            i += 1
            continue
        if not line.startswith(content_indent) or re.match(r"^\s*-\s+", line):
            break
        if field_pattern.match(line):
            lines[i] = f"{content_indent}{field}: {_yaml_scalar(value)}"
            return "\n".join(lines)
        i += 1
    lines.insert(dash_index + 1, f"{content_indent}{field}: {_yaml_scalar(value)}")
    return "\n".join(lines)


def apply_safety_signoff(signoff_path: str, safety_dir: str) -> Dict[str, Any]:
    """Apply table approvals and row corrections. All-or-nothing on failure."""
    signoff_file = Path(signoff_path)
    safety_path = Path(safety_dir)
    signoff_text = signoff_file.read_text(encoding="utf-8")
    known_files = sorted(p.name for p in safety_path.glob("*.yaml"))

    approvals = parse_table_approvals(signoff_text, known_files)
    corrections = parse_safety_corrections(signoff_text)
    reviewer, reviewed_at = _parse_header(signoff_text)

    for table in approvals:
        if table not in known_files:
            raise KeyError(f"Approved table not found: {table!r}")
    for correction in corrections:
        if correction["file"] not in known_files:
            raise KeyError(f"Correction target not found: {correction['file']!r}")

    # Validate row targets before writing anything.
    originals: Dict[str, str] = {}
    for table in sorted(set(approvals + [c["file"] for c in corrections])):
        originals[table] = (safety_path / table).read_text(encoding="utf-8")
    for correction in corrections:
        _apply_row_correction(
            originals[correction["file"]],
            correction["id_field"],
            correction["id_value"],
            correction["field"],
            correction["value"],
        )

    rows_corrected = 0
    for table, text in originals.items():
        updated = text
        if table in approvals:
            updated = _apply_metadata_approval(updated, reviewer, reviewed_at)
        for correction in corrections:
            if correction["file"] == table:
                updated = _apply_row_correction(
                    updated,
                    correction["id_field"],
                    correction["id_value"],
                    correction["field"],
                    correction["value"],
                )
                rows_corrected += 1
        if updated != text:
            (safety_path / table).write_text(updated, encoding="utf-8")

    return {
        "signoff_file": str(signoff_file),
        "safety_dir": str(safety_path),
        "tables_approved": sorted(approvals),
        "rows_corrected": rows_corrected,
    }
