"""
Encounter pipeline and harness scorer for AI-VH (STEP 34 / P5.4).

Registers the multi-agent orchestrated encounter as a first-class harness
pipeline (``pipeline_name="encounter"``). The pipeline receives only the
sanitized ``CaseView`` from the harness runner, resolves the full ``CaseSpec``
from the frozen golden set for simulation, and returns a ``PipelineResult``.
The scorer evaluates encounter quality against ground truth without ever
exposing hidden data to the pipeline itself.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vh.agents.orchestrator import EncounterBudget, EncounterState, HospitalOrchestrator
from vh.agents.replay import RecordingAdapter
from vh.agents.scoring import EncounterScorer, aggregate_encounter_scores
from vh.cases.schema import CaseView, GoldenCase
from vh.cases.spec import CaseSpec

from .interfaces import PipelineResult

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class EncounterPipeline:
    """Harness pipeline driving the full multi-agent encounter per case."""

    def __init__(
        self,
        golden_dir: Optional[Path] = None,
        budget: Optional[EncounterBudget] = None,
        seed: int = 42,
    ) -> None:
        self.golden_dir: Path = golden_dir or (REPO_ROOT / "eval" / "golden" / "v1")
        self.budget: EncounterBudget = budget or EncounterBudget()
        self.seed: int = seed
        self._spec_cache: Dict[str, CaseSpec] = {}
        self._load_specs()

    def _load_specs(self) -> None:
        for path in sorted(self.golden_dir.glob("*.json")):
            if path.name == "manifest.json":
                continue
            try:
                golden = GoldenCase.model_validate(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
            self._spec_cache[golden.case_id] = CaseSpec.from_golden_case(golden)

    def _resolve_spec(self, case_view: CaseView) -> CaseSpec:
        spec = self._spec_cache.get(case_view.case_id)
        if spec is None:
            raise KeyError(f"Golden case '{case_view.case_id}' not found in {self.golden_dir}.")
        return spec

    def run_encounter_state(self, case_view: CaseView) -> EncounterState:
        """Execute the orchestrated encounter and return the terminal state."""
        spec = self._resolve_spec(case_view)
        adapter = RecordingAdapter()
        orchestrator = HospitalOrchestrator(budget=self.budget, adapter=adapter)
        return orchestrator.run_encounter(spec, run_id=f"harness-{spec.case_id}", seed=self.seed)

    def run(self, case_view: CaseView) -> PipelineResult:
        state = self.run_encounter_state(case_view)
        report = state.report or {}
        differential: List[str] = []
        raw_diff = report.get("differential") or []
        if isinstance(raw_diff, list):
            for item in raw_diff:
                if isinstance(item, dict) and item.get("dx"):
                    differential.append(str(item["dx"]))
                elif isinstance(item, str):
                    differential.append(item)
        ordered: List[str] = []
        for step in state.history:
            tests = (step.payload or {}).get("ordered_tests")
            if isinstance(tests, list):
                ordered.extend(str(t) for t in tests)
        diagnosis = differential[0] if differential else "Undifferentiated Inpatient Presentation"
        summary = (
            f"Encounter {state.status} after {state.step_count} steps "
            f"({state.sim_time_minutes} sim-min) for {case_view.case_id}"
        )
        return PipelineResult(
            case_id=case_view.case_id,
            diagnosis=diagnosis,
            differential=differential[:3],
            suggested_orders=ordered,
            clinical_summary=summary,
            metadata={
                "encounter_status": str(state.status),
                "sim_time_minutes": state.sim_time_minutes,
                "step_count": state.step_count,
            },
        )


class EncounterHarnessScorer:
    """Harness scorer computing encounter-quality metrics over golden cases."""

    def __init__(
        self,
        budget: Optional[EncounterBudget] = None,
        golden_dir: Optional[Path] = None,
    ) -> None:
        self.scorer = EncounterScorer(budget=budget)
        self.golden_dir: Path = golden_dir or (REPO_ROOT / "eval" / "golden" / "v1")

    def score(
        self,
        results: List[Tuple[CaseView, PipelineResult]],
        golden_cases: List[GoldenCase],
    ) -> Dict[str, float]:
        if not results:
            return {"encounter_score_mean": 0.0}
        golden_map = {g.case_id: g for g in golden_cases}
        pipeline = EncounterPipeline(golden_dir=self.golden_dir)
        scores = []
        for case_view, _result in results:
            golden = golden_map.get(case_view.case_id)
            if golden is None:
                continue
            spec = CaseSpec.from_golden_case(golden)
            state = pipeline.run_encounter_state(case_view)
            scores.append(self.scorer.score(state, spec))
        if not scores:
            return {"encounter_score_mean": 0.0}
        return aggregate_encounter_scores(scores)
