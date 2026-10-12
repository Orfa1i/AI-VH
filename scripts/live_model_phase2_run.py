"""
Live-model evidence run for Phase 2 condition 1 (and Phase 3/6 acceptance input).

Runs run_grounded_assessment with the REAL MedGemma (never the offline
heuristic) on >=20 cases including Charles Brown. Appends one JSON record per
case to eval/reports/live_model_phase2.jsonl (resume-safe: skips done case_ids).

Metrics per case: status, diagnosis, parse_stats (attempts/retries), box_2d
occurrences across raw attempts, repetition flag, latencies, model source
(live vs heuristic fallback — heuristic only if the live model is unavailable).

Usage:
    py -3.13 scripts/live_model_phase2_run.py [--max-cases N]

Owner: AI Engineer.
"""

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

OUT_PATH = REPO_ROOT / "eval" / "reports" / "live_model_phase2.jsonl"


def max_sentence_repeat(text: str) -> int:
    """Highest repeat count of any normalized sentence-like line."""
    lines = [re.sub(r"\s+", " ", s).strip().lower() for s in re.split(r"[.\n]+", text or "")]
    lines = [s for s in lines if len(s) > 20]
    if not lines:
        return 0
    return max(Counter(lines).values())


def build_cases() -> list:
    """Charles Brown + 19 deterministic CaseBuilder cases (7 ACS / 6 CAP / 6 DKA)."""
    from vh.cases.builder import CaseBuilder, CaseBuilderConfig
    from vh.cases.structured_case import extract_structured_case, structured_case_to_agentview_dict

    builder = CaseBuilder(config=CaseBuilderConfig(batch_size=19, seed=20261004))
    cohorts = (
        ["acute_coronary_syndrome"] * 7
        + ["community_acquired_pneumonia"] * 6
        + ["diabetic_ketoacidosis"] * 6
    )
    cases = []

    brown = json.loads((REPO_ROOT / "tests" / "fixtures" / "phase1" / "charles_brown_realistic.json").read_text())
    brown_structured = structured_case_to_agentview_dict(extract_structured_case(brown["raw_case"]))
    cases.append({"case_id": "LIVE-BROWN-001", "specialty": "Pulmonology",
                  "cohort": "community_acquired_pneumonia", "structured": brown_structured})

    for i, slug in enumerate(cohorts):
        spec = builder.build_single_case(specialty_slug=slug, seed=4242 + i)
        vis = spec.visible
        # Complaint = the case's own presentation clause (deterministic parse, no invention).
        first_sentence = (vis.presentation or "").split(".")[0]
        complaint = first_sentence.split(" with ", 1)[1] if " with " in first_sentence else first_sentence
        labs, imaging = {}, {}
        for h in spec.hidden:
            target = imaging if (h.category or "") == "imaging" else labs
            target[h.order_name] = h.result
        raw = {
            "age": (vis.demographics or {}).get("age"),
            "sex": (vis.demographics or {}).get("gender"),
            "presenting_symptoms": [complaint] if complaint else [],
            "vitals": dict(vis.initial_vitals or {}),
            "examination_findings": vis.exam,
            "comorbidities": [vis.history] if vis.history else [],
            "current_medications": list(vis.current_medications or []),
            "allergies": list(vis.allergies or []),
            "labs": labs,
            "imaging": imaging,
        }
        structured = structured_case_to_agentview_dict(extract_structured_case(raw))
        cases.append({"case_id": f"LIVE-{slug[:3].upper()}-{i:03d}", "specialty": spec.specialty,
                      "cohort": slug, "structured": structured})
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-cases", type=int, default=100)
    args = parser.parse_args()

    from backend.llm.medgemma_service import medgemma_service
    from vh.generation.medgemma import MedGemmaAdapter, Phase2GenerationConfig
    from vh.generation.pipeline import GroundedGenerationPipeline

    medgemma_service.load_model()
    live = medgemma_service.model is not None
    print(f"live_model_available={live}", flush=True)
    if not live:
        print("ABORT: live MedGemma unavailable; heuristic results would mislabel the run.", flush=True)
        return 2

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if OUT_PATH.exists():
        for line in OUT_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line).get("case_id"))

    cases = [c for c in build_cases() if c["case_id"] not in done][: args.max_cases]
    print(f"cases_to_run={len(cases)} already_done={len(done)}", flush=True)

    pipe = GroundedGenerationPipeline(adapter=MedGemmaAdapter())
    cfg = Phase2GenerationConfig(timeout_s=900)
    with open(OUT_PATH, "a", encoding="utf-8") as f:
        for case in cases:
            t0 = time.perf_counter()
            try:
                res = pipe.run_grounded_assessment(
                    case_id=case["case_id"], specialty=case["specialty"],
                    structured_case=case["structured"], phase2_config=cfg,
                )
            except Exception as exc:  # never lose the row: record runner-level failure
                res = None
                error = f"runner exception: {exc}"
            dt = time.perf_counter() - t0
            md = (res.metadata if res else {}) or {}
            raws = md.get("raw_model_output", []) or []
            reasoning = ((md.get("assessment_report", {}) or {}).get("clinical_reasoning")) or ""
            record = {
                "case_id": case["case_id"],
                "cohort": case["cohort"],
                "model_source": "live-medgemma-4b",
                "status": md.get("generation_status", "runner_exception"),
                "diagnosis": res.diagnosis if res else "Runner Exception",
                "attempts": (md.get("parse_stats", {}) or {}).get("attempts", 0),
                "json_failures": (md.get("parse_stats", {}) or {}).get("json_failures", 0),
                "schema_failures": (md.get("parse_stats", {}) or {}).get("schema_failures", 0),
                "grounding_failures": (md.get("parse_stats", {}) or {}).get("grounding_failures", 0),
                "box2d_occurrences": sum(r.count("box_2d") for r in raws),
                "fence_occurrences": sum(r.count("```") for r in raws),
                "repetition_max_sentence_repeat": max_sentence_repeat(reasoning),
                "n_raw_attempts": len(raws),
                "n_evidence": len(md.get("active_evidence_ids", []) or []),
                "latency_s": round(dt, 1),
                "prompt_version": md.get("prompt_version"),
                "error": md.get("error") if md.get("generation_status") == "generation_failed" else locals().get("error"),
            }
            f.write(json.dumps(record) + "\n")
            f.flush()
            print(f"{record['case_id']} {record['status']} attempts={record['attempts']} "
                  f"box2d={record['box2d_occurrences']} rep={record['repetition_max_sentence_repeat']} "
                  f"s={record['latency_s']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
