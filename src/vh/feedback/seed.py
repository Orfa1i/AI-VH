"""
Demo data seeder for the doctor-review API (STEP 38 / P6.3).

Creates one demo reviewer (fixed dev-only token) and three demo reports (one
flagged, two plain) for local development and the Playwright end-to-end suite.
Idempotent: existing rows are reused. NEVER run against production data.
"""

from typing import Any, Dict, List, Optional

from vh.feedback.models import FeedbackStore

DEMO_REVIEWER_NAME = "Demo Doctor"
DEMO_TOKEN_DEFAULT = "e2e-demo-token-001"

DEMO_REPORT: Dict[str, Any] = {
    "patient_summary": "E2E patient summary.",
    "differential": [{"dx": "E2E differential diagnosis", "likelihood": "high"}],
    "recommendations": [{"text": "E2E recommendation."}],
    "claims": [{"claim_id": "CLM-E2E-01", "text": "Troponin rise confirms ACS."}],
}

DEMO_CASES: List[Dict[str, Any]] = [
    {
        "case_id": "CASE-E2E-FLAGGED",
        "verification": {
            "status": "flagged",
            "critical_count": 1,
            "reason": "Troponin claim unverified.",
        },
    },
    {"case_id": "CASE-E2E-PLAIN-1", "verification": None},
    {"case_id": "CASE-E2E-PLAIN-2", "verification": None},
]


def seed_demo(db_path: str, token: str = DEMO_TOKEN_DEFAULT) -> Dict[str, Any]:
    """Seed demo reviewer + reports. Returns token, reviewer and original ids."""
    store = FeedbackStore(db_path)
    try:
        reviewer = store.get_reviewer_by_name(DEMO_REVIEWER_NAME)
        if reviewer is None:
            reviewer_id, _ = store.register_reviewer(DEMO_REVIEWER_NAME, "attending", token=token)
        else:
            reviewer_id = reviewer["id"]
        original_ids: List[str] = []
        for case in DEMO_CASES:
            existing: Optional[Dict[str, Any]] = store.get_original_by_case(case["case_id"])
            if existing is not None:
                original_ids.append(existing["id"])
                continue
            original_ids.append(
                store.store_original(
                    case["case_id"],
                    dict(DEMO_REPORT),
                    model_id="demo-model",
                    prompt_version="clinical_report@1.0.0",
                    verification=case["verification"],
                )
            )
        return {"token": token, "reviewer_id": reviewer_id, "original_ids": original_ids}
    finally:
        store.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed demo review data (dev-only).")
    parser.add_argument("--db", default="data/feedback-review.db")
    parser.add_argument("--token", default=DEMO_TOKEN_DEFAULT)
    args = parser.parse_args()
    print(seed_demo(args.db, token=args.token))
