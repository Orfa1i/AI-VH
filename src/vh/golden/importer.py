"""
Sign-off importer for AI-VH Golden Cases.
Reads physician sign-off records matching plan/prompts/_templates/SIGNOFF.md
and promotes approved draft cases to status: verified.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from vh.cases.schema import GoldenCase
from .validator import validate_case_dict


def parse_signoff_document(signoff_path: Path) -> Dict[str, Any]:
    """Parse structured markdown sign-off document."""
    content = signoff_path.read_text(encoding="utf-8")

    reviewer = ""
    role = ""
    date = ""
    result = "PASS"
    approved_ids: List[str] = []

    m_rev = re.search(r"-\s+\*\*Reviewer:\*\*\s*(.+)", content)
    if m_rev:
        reviewer = m_rev.group(1).strip()

    m_role = re.search(r"-\s+\*\*Role\s*/\s*credentials:\*\*\s*(.+)", content)
    if m_role:
        role = m_role.group(1).strip()

    m_date = re.search(r"-\s+\*\*Date:\*\*\s*(.+)", content)
    if m_date:
        date = m_date.group(1).strip()

    m_res = re.search(r"-\s+\*\*Result:\*\*\s*(.+)", content)
    if m_res:
        result = m_res.group(1).strip()

    # Look for approved items section
    lines = content.splitlines()
    in_approved = False
    for line in lines:
        line_clean = line.strip()
        if line_clean.startswith("## Approved items"):
            in_approved = True
            continue
        elif in_approved and line_clean.startswith("##"):
            in_approved = False
            continue

        if in_approved:
            # Extract bullet items or case ids
            items = re.findall(r"(?:GOLDEN-[A-Z]+-\d+|[A-Z0-9_-]+)", line_clean)
            for itm in items:
                if itm and itm not in approved_ids and not itm.startswith("-"):
                    approved_ids.append(itm)

    return {
        "reviewer": reviewer,
        "role": role,
        "date": date,
        "result": result,
        "approved_ids": approved_ids
    }


def import_signoff(
    signoff_path: Path,
    drafts_dir: Path
) -> Dict[str, Any]:
    """
    Read signoff markdown, promote approved cases in drafts_dir to status: verified.
    """
    parsed = parse_signoff_document(signoff_path)
    approved_set = set(parsed["approved_ids"])
    reviewer_str = f"{parsed['reviewer']}" + (f" ({parsed['role']})" if parsed['role'] else "")
    reviewed_at = parsed["date"]

    promoted_cases = 0

    for file_path in sorted(drafts_dir.glob("*.json")):
        if file_path.name == "manifest.json":
            continue

        data = json.loads(file_path.read_text(encoding="utf-8"))
        case_id = data.get("case_id")

        if case_id in approved_set:
            data["status"] = "verified"
            data["reviewer"] = reviewer_str
            data["reviewed_at"] = reviewed_at
            # Validate with approved_ids check
            case = validate_case_dict(data, allow_verified=True)
            file_path.write_text(json.dumps(case.model_dump(), indent=2), encoding="utf-8")
            promoted_cases += 1

    return {
        "signoff_file": str(signoff_path),
        "reviewer": reviewer_str,
        "reviewed_at": reviewed_at,
        "approved_cases_found": len(approved_set),
        "promoted_cases_count": promoted_cases
    }
