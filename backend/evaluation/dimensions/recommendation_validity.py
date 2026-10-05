"""
Dimension 5: Recommendation Validity Evaluator
Verifies whether investigations, management suggestions, and treatment orders
are clinically valid and appropriate for the identified condition.
Flags unsupported, harmful, or explicitly contraindicated recommendations.
"""

from typing import Dict, Any, Optional, List
import re
from .base import BaseDimensionEvaluator
from ..models import DimensionEvaluationResult, EvaluationSeverity


class RecommendationValidityEvaluator(BaseDimensionEvaluator):
    dimension_id = "recommendation_validity"
    display_name = "Recommendation Validity"
    weight = 1.3  # Clinical safety critical

    SEVERITY_ORDER = {
        EvaluationSeverity.INFO: 0,
        EvaluationSeverity.LOW: 1,
        EvaluationSeverity.MEDIUM: 2,
        EvaluationSeverity.HIGH: 3,
        EvaluationSeverity.CRITICAL: 4,
    }

    DRUG_CLASSES = {
        "nsaid": ["nsaid", "nsaids", "ibuprofen", "naproxen", "ketorolac", "indomethacin", "meloxicam", "celecoxib", "diclofenac"],
        "beta_blocker": ["beta-blocker", "beta-blockers", "beta blocker", "beta blockers", "metoprolol", "atenolol", "carvedilol", "propranolol", "bisoprolol", "labetalol"],
        "acei": ["ace inhibitor", "ace-inhibitor", "acei", "lisinopril", "enalapril", "ramipril", "captopril"],
        "arb": ["arb", "losartan", "valsartan", "candesartan"],
        "anticoagulant": ["anticoagulant", "anticoagulation", "blood thinner", "heparin", "enoxaparin", "warfarin", "apixaban", "rivaroxaban", "dabigatran"],
        "antiplatelet": ["antiplatelet", "aspirin", "clopidogrel", "ticagrelor", "prasugrel"],
    }

    # Universal clinical safety contraindications rules
    SAFETY_CONTRAINDICATION_RULES = [
        {
            "trigger_condition": ["cardiogenic shock", "decompensated heart failure", "bradycardia", "heart block"],
            "prohibited_agents": ["beta-blocker", "metoprolol", "atenolol", "carvedilol", "propranolol"],
            "rationale": "Beta-blocker administration is contraindicated in acute decompensated shock/bradycardia.",
            "severity": EvaluationSeverity.CRITICAL,
        },
        {
            "trigger_condition": ["diabetic ketoacidosis", "dka", "lactic acidosis", "severe metabolic acidosis", "acute kidney injury"],
            "prohibited_agents": ["metformin"],
            "rationale": "Metformin is strictly contraindicated in severe acute acidosis and acute kidney injury.",
            "severity": EvaluationSeverity.HIGH,
        },
        {
            "trigger_condition": ["active bleeding", "gastrointestinal bleed", "peptic ulcer", "aortic dissection", "hemorrhag"],
            "prohibited_agents": ["aspirin", "heparin", "enoxaparin", "ticagrelor", "clopidogrel", "warfarin", "tpa", "alteplase"],
            "rationale": "Anticoagulation/thrombolysis is strictly contraindicated in active hemorrhage or aortic dissection.",
            "severity": EvaluationSeverity.CRITICAL,
        },
        {
            "trigger_condition": ["acute kidney injury", "renal failure", "hyperkalemia"],
            "prohibited_agents": ["nsaid", "ibuprofen", "naproxen", "ketorolac", "indomethacin"],
            "rationale": "NSAIDs are contraindicated in acute kidney injury due to nephrotoxicity and worsening renal perfusion.",
            "severity": EvaluationSeverity.HIGH,
        },
    ]

    def _evaluate_internal(
        self,
        report: Dict[str, Any],
        patient_presentation: Dict[str, Any],
        retrieved_evidence: Optional[Dict[str, Any]] = None,
        ground_truth: Optional[Dict[str, Any]] = None,
    ) -> DimensionEvaluationResult:
        detected_issues: List[str] = []
        evidence_records: List[Dict[str, Any]] = []
        deductions = 0.0
        max_severity = EvaluationSeverity.INFO

        treatment_plan = report.get("treatment_plan") or []
        recommended_next_steps = report.get("recommended_next_steps") or []
        primary_dx = str(report.get("primary_diagnosis", "")).lower()
        clinical_summary = str(report.get("clinical_summary", "")).lower()
        treatment_corpus = (" ".join(treatment_plan) + " " + " ".join(recommended_next_steps)).lower()

        # 1. Actionability and length check of treatment plan
        if not treatment_plan:
            detected_issues.append("Treatment plan is completely empty.")
            deductions += 0.50
            max_severity = max(max_severity, EvaluationSeverity.HIGH, key=lambda s: self.SEVERITY_ORDER.get(s, 0))
        else:
            for idx, item in enumerate(treatment_plan):
                if len(str(item).strip()) < 5:
                    detected_issues.append(f"Treatment item #{idx + 1} ('{item}') is too short or non-actionable.")
                    deductions += 0.10

        # 2. General Clinical Safety Contraindication Rules
        context_corpus = f"{primary_dx} {clinical_summary}"
        for rule in self.SAFETY_CONTRAINDICATION_RULES:
            condition_triggered = any(cond in context_corpus for cond in rule["trigger_condition"])
            if condition_triggered:
                for agent in rule["prohibited_agents"]:
                    # Match whole word to avoid false positives like 'heparin' in 'non-heparin'
                    if re.search(rf"\b{agent}\b", treatment_corpus):
                        issue_msg = f"Safety contraindication violation: {rule['rationale']} Found: '{agent}'."
                        detected_issues.append(issue_msg)
                        deductions += 0.40
                        max_severity = max(max_severity, rule["severity"], key=lambda s: self.SEVERITY_ORDER.get(s, 0))
                        evidence_records.append({
                            "type": "safety_contraindication",
                            "agent": agent,
                            "rule_rationale": rule["rationale"],
                        })

        # 3. Case Ground Truth Contraindication Validation (when explicitly available to evaluator)
        if ground_truth:
            gt_contraindications = ground_truth.get("contraindications") or []
            for ci in gt_contraindications:
                ci_str = str(ci).lower()
                matched_agents_in_plan = set()
                # Check known drug classes mentioned in contraindication
                for cls_key, drug_list in self.DRUG_CLASSES.items():
                    class_mentioned = any(re.search(rf"\b{re.escape(drug)}\b", ci_str) for drug in drug_list[:4])
                    if class_mentioned:
                        for drug in drug_list:
                            if re.search(rf"\b{re.escape(drug)}\b", treatment_corpus):
                                matched_agents_in_plan.add(drug)

                # Also extract specific medication tokens from contraindication text
                ci_tokens = [tok for tok in re.findall(r"\b[a-z]{4,}\b", ci_str) if tok not in {"avoid", "with", "patient", "history", "severe", "acute", "due"}]
                for tok in ci_tokens:
                    if re.search(rf"\b{re.escape(tok)}\b", treatment_corpus):
                        matched_agents_in_plan.add(tok)

                for agent in matched_agents_in_plan:
                    detected_issues.append(
                        f"Ground-truth contraindicated therapy: Plan includes '{agent}', which violates case contraindication ('{ci}')."
                    )
                    deductions += 0.45
                    max_severity = max(max_severity, EvaluationSeverity.CRITICAL, key=lambda s: self.SEVERITY_ORDER.get(s, 0))
                    evidence_records.append({
                        "type": "ground_truth_contraindication_breach",
                        "contraindication": ci,
                        "detected_agent": agent,
                    })

        final_score = max(0.0, min(1.0, 1.0 - deductions))
        passed = len(detected_issues) == 0 and final_score >= 0.80

        if final_score < 0.40 or self.SEVERITY_ORDER.get(max_severity, 0) >= self.SEVERITY_ORDER[EvaluationSeverity.HIGH]:
            severity = max_severity if max_severity != EvaluationSeverity.INFO else EvaluationSeverity.HIGH
        elif detected_issues:
            severity = max_severity if max_severity != EvaluationSeverity.INFO else EvaluationSeverity.MEDIUM
        else:
            severity = EvaluationSeverity.INFO

        explanation = (
            "Recommendation validity confirmed: treatment plan and next steps are clinically appropriate with zero safety contraindications."
            if passed
            else f"Recommendation validity issues: {'; '.join(detected_issues)}"
        )

        return DimensionEvaluationResult(
            dimension=self.dimension_id,
            display_name=self.display_name,
            passed=passed,
            score=round(final_score, 2),
            explanation=explanation,
            detected_issues=detected_issues,
            severity=severity,
            evidence=evidence_records,
        )
