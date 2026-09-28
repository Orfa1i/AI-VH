"""
Pipeline and Scorer protocols, plugin interfaces, and test fixtures for AI-VH evaluation harness.
"""

from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable
from pydantic import BaseModel, Field

from vh.cases.schema import CaseView, GoldenCase


class PipelineResult(BaseModel):
    case_id: str
    diagnosis: str
    differential: List[str] = Field(default_factory=list)
    suggested_orders: List[str] = Field(default_factory=list)
    clinical_summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class Pipeline(Protocol):
    """Protocol implemented by all clinical reasoning, generation, and agent pipelines."""
    def run(self, case_view: CaseView) -> PipelineResult:
        ...


@runtime_checkable
class Scorer(Protocol):
    """Protocol implemented by metric scorers evaluating pipeline outputs against golden truth."""
    def score(
        self,
        results: List[Tuple[CaseView, PipelineResult]],
        golden_cases: List[GoldenCase]
    ) -> Dict[str, float]:
        ...


class DummyPipeline:
    """Deterministic dummy pipeline used to test harness execution and validation."""

    def run(self, case_view: CaseView) -> PipelineResult:
        # Generate predictable response based only on visible presentation
        chief = case_view.visible_presentation.get("chief_complaint", "").lower()
        if "chest pain" in chief:
            dx = "Acute Coronary Syndrome"
            diff = ["Myocardial Infarction", "Pericarditis"]
            orders = ["12-Lead ECG", "Troponin I"]
        elif "cough" in chief or "sputum" in chief:
            dx = "Community-Acquired Pneumonia"
            diff = ["COPD Exacerbation", "Bronchitis"]
            orders = ["Chest Radiograph", "Complete Blood Count"]
        elif "breathing" in chief or "glucose" in chief or "vomiting" in chief:
            dx = "Diabetic Ketoacidosis"
            diff = ["Hyperosmolar Hyperglycemic State", "Gastritis"]
            orders = ["Comprehensive Metabolic Panel", "Blood Gas"]
        else:
            dx = "Undifferentiated Inpatient Presentation"
            diff = ["Symptom Evaluation"]
            orders = ["Routine Vitals"]

        return PipelineResult(
            case_id=case_view.case_id,
            diagnosis=dx,
            differential=diff,
            suggested_orders=orders,
            clinical_summary=f"Automated evaluation for {case_view.case_id} ({case_view.specialty})"
        )


class DummyScorer:
    """Deterministic dummy scorer calculating baseline evaluation metrics."""

    def score(
        self,
        results: List[Tuple[CaseView, PipelineResult]],
        golden_cases: List[GoldenCase]
    ) -> Dict[str, float]:
        if not results:
            return {}

        total = len(results)
        schema_valid = sum(1 for _, res in results if res.diagnosis and res.clinical_summary)
        schema_valid_rate = schema_valid / total

        # Match primary dx against acceptable differentials or primary
        golden_map = {g.case_id: g for g in golden_cases}
        matched = 0
        for cv, res in results:
            g = golden_map.get(cv.case_id)
            if g:
                primary_lower = g.ground_truth.primary_dx.lower()
                res_dx_lower = res.diagnosis.lower()
                if (res_dx_lower in primary_lower or primary_lower in res_dx_lower or
                        any(res_dx_lower in d.lower() for d in g.ground_truth.acceptable_differential)):
                    matched += 1

        accuracy = matched / total

        return {
            "schema_valid_rate": schema_valid_rate,
            "recall_at_10": 0.90,
            "mrr_min": 0.80,
            "critical_fault_detection": 1.0,
            "faithfulness_min": 0.95,
            "contextual_relevancy_min": 0.85,
            "traceability_rate": 1.0,
        }


class SpyPipeline:
    """Test spy recording all input case objects to ensure ground truth isolation."""

    def __init__(self) -> None:
        self.received_cases: List[CaseView] = []

    def run(self, case_view: CaseView) -> PipelineResult:
        self.received_cases.append(case_view)
        return PipelineResult(
            case_id=case_view.case_id,
            diagnosis="Monitored Diagnosis",
            clinical_summary="Spy inspection pass"
        )
