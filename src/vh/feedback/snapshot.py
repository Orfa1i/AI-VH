"""
Versioned feedback snapshot export for AI-VH (STEP 39 / P6.4).

`vh feedback snapshot` exports originals, evidence, edits, finals, ratings,
and agreement flags as canonical JSONL/JSON plus a manifest, and registers
the bundle as a versioned `dataset` artifact with recorded lineage. Phase 7
trains on these snapshots, never on the live database. Snapshots of one
store are byte-identical across runs (only the manifest timestamp varies).
"""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from vh.common.artifacts import ArtifactRegistry
from vh.feedback.agreement import agreement_report, per_taxonomy_error_rates
from vh.feedback.models import FeedbackStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_FILES = ("originals.jsonl", "evidence.jsonl", "edits.jsonl", "finals.jsonl", "ratings.jsonl")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _code_version() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and sha else "unknown"
    except Exception:
        return "unknown"


def _dump_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_snapshot(
    store: FeedbackStore,
    output_dir: str,
    version: str,
    registry_db: Optional[str] = None,
) -> Dict[str, Any]:
    """Export a versioned, reproducible snapshot bundle from the store."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    original_rows = store.list_originals()
    originals: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    for row in original_rows:
        report = json.loads(row["report_json"])
        verification = json.loads(row.get("verification_json") or "{}")
        originals.append(
            {
                "id": row["id"],
                "case_id": row["case_id"],
                "report": report,
                "model_id": row["model_id"],
                "prompt_version": row["prompt_version"],
                "verification": verification,
                "flagged": bool(row.get("flagged")),
                "created_at": row["created_at"],
            }
        )
        for claim in report.get("claims", []) if isinstance(report, dict) else []:
            if not isinstance(claim, dict):
                continue
            evidence.append(
                {
                    "original_id": row["id"],
                    "claim_id": claim.get("claim_id"),
                    "text": claim.get("text"),
                    "evidence_ids": claim.get("evidence_ids", []),
                    "source": claim.get("source"),
                }
            )

    edits: List[Dict[str, Any]] = []
    finals: List[Dict[str, Any]] = []
    for row in original_rows:
        for assignment in store.assignments_for_original(row["id"]):
            sessions = store._conn.execute(
                "SELECT * FROM review_sessions WHERE assignment_id = ? ORDER BY started_at, id",
                (assignment["id"],),
            ).fetchall()
            for session in sessions:
                session_dict = dict(session)
                for edit in store.get_edits(session_dict["id"]):
                    edits.append({"session_id": session_dict["id"], **edit})
                final_rows = store._conn.execute(
                    "SELECT * FROM final_reports WHERE session_id = ?", (session_dict["id"],)
                ).fetchall()
                for final_row in final_rows:
                    final_dict = dict(final_row)
                    final_dict["report"] = json.loads(final_dict.pop("report_json"))
                    finals.append(final_dict)

    ratings = [
        {
            "session_id": row["session_id"],
            "claim_id": row["claim_id"],
            "rating": row["rating"],
            "taxonomy_code": row["taxonomy_code"],
            "created_at": row["created_at"],
        }
        for row in store.all_claim_ratings()
    ]

    agreement = agreement_report(store)
    agreement["taxonomy_error_rates"] = per_taxonomy_error_rates(store)
    agreement["originals"] = []
    for row in original_rows:
        decided = [s["decision"] for s in store.decided_sessions_for_original(row["id"])]
        agreement["originals"].append(
            {
                "original_id": row["id"],
                "n_decided_sessions": len(decided),
                "overlap": len(decided) >= 2,
                "decisions_agree": (len(set(decided)) == 1) if decided else None,
            }
        )

    _dump_jsonl(out / "originals.jsonl", originals)
    _dump_jsonl(out / "evidence.jsonl", evidence)
    _dump_jsonl(out / "edits.jsonl", edits)
    _dump_jsonl(out / "finals.jsonl", finals)
    _dump_jsonl(out / "ratings.jsonl", ratings)
    (out / "agreement.json").write_text(json.dumps(agreement, indent=2, sort_keys=True), encoding="utf-8")

    dataset_sha = hashlib.sha256(
        "\n".join(f"{name}:{_sha_file(out / name)}" for name in (*DATA_FILES, "agreement.json")).encode(
            "utf-8"
        )
    ).hexdigest()

    lineage = {"golden_version": "v1", "code_version": _code_version()}
    counts = {
        "originals": len(originals),
        "evidence": len(evidence),
        "edits": len(edits),
        "finals": len(finals),
        "ratings": len(ratings),
    }

    artifact_id = ""
    if registry_db is not None:
        registry = ArtifactRegistry(
            db_path=registry_db,
            storage_dir=str(Path(registry_db).parent / "artifact_store"),
        )
        record = registry.register_artifact(
            kind="dataset",
            name="feedback-snapshot",
            version=version,
            content=dataset_sha.encode("utf-8"),
            parent_ids=["golden-v1"],
            metadata={"version": version, "counts": counts, "dataset_sha256": dataset_sha},
        )
        artifact_id = record.id
        lineage["artifact_id"] = artifact_id

    manifest = {
        "version": version,
        "created_at": _utcnow(),
        "counts": counts,
        "dataset_sha256": dataset_sha,
        "lineage": lineage,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "version": version,
        "output_dir": str(out),
        "dataset_sha256": dataset_sha,
        "artifact_id": artifact_id,
        "counts": counts,
    }
