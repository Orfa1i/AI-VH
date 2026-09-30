"""
Claim grounding and citation verification module for AI Virtual Hospital (AI-VH).
Evaluates whether generated diagnostic and therapeutic claims are genuinely
supported, partially supported, or unsupported by cited retrieval evidence.
Enforces strict judge isolation and provides calibration scoring (Cohen's kappa).
"""

from enum import Enum
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from vh.common.logging import get_logger
from vh.generation.report import ClaimItem, ClinicalReport

logger = get_logger("vh.verification.grounding")
REPO_ROOT = Path(__file__).resolve().parents[3]


class GroundingVerdict(str, Enum):
    """Verdicts for claim-evidence entailment assessment."""
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


class ClaimGroundingJudgment(BaseModel):
    """Individual claim grounding judgment."""
    claim_id: str
    claim_text: str
    evidence_ids: List[str]
    citation_valid: bool = Field(description="True if all cited evidence_ids were retrieved in this encounter")
    verdict: GroundingVerdict
    rationale: str
    unsupported_spans: List[str] = Field(default_factory=list, description="Substrings in claim lacking evidence")


class ReportGroundingResult(BaseModel):
    """Aggregated grounding assessment across all claims in a clinical report."""
    report_id: Optional[str] = None
    total_claims: int
    supported_count: int
    partial_count: int
    unsupported_count: int
    invalid_citation_count: int
    grounding_ratio: float = Field(description="Weighted grounding score in [0.0, 1.0]")
    judgments: List[ClaimGroundingJudgment]
    passed: bool = Field(description="True if zero unsupported claims and zero invalid citations")


class JudgeResponseSchema(BaseModel):
    """Structured response schema expected from grounding judge model."""
    verdict: GroundingVerdict
    rationale: str
    unsupported_spans: List[str] = Field(default_factory=list)


class ClaimGroundingChecker:
    """
    Evaluates factual grounding of clinical claims against cited retrieval chunks.
    Ensures that the judge operates in strict isolation, seeing only the claim
    and its directly cited evidence chunks.
    """

    def __init__(
        self,
        model_id: str = "google/medgemma-4b",
        prompt_version: str = "1",
        temperature: float = 0.0,
        adapter: Optional[Any] = None,
    ):
        self.model_id = model_id
        self.prompt_version = prompt_version
        self.temperature = temperature
        self.adapter = adapter

    def build_judge_prompt_inputs(
        self,
        claim: ClaimItem,
        retrieved_chunks: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Constructs the isolated prompt payload for the grounding judge.
        STRICT ISOLATION GUARANTEE: Contains ONLY the claim text and cited chunk text.
        Never includes patient ground truth, other claims, or unreferenced chunks.
        """
        cited_texts = []
        for eid in claim.evidence_ids:
            if eid in retrieved_chunks:
                cited_texts.append(f"[{eid}]\n{retrieved_chunks[eid]}")

        combined_evidence = "\n\n".join(cited_texts) if cited_texts else "NO CITED EVIDENCE PROVIDED."
        return {
            "claim_text": claim.text.strip(),
            "evidence_text": combined_evidence.strip(),
        }

    def judge_claim(
        self,
        claim: ClaimItem,
        retrieved_chunks: Dict[str, str],
    ) -> ClaimGroundingJudgment:
        """
        Evaluates a single claim against cited retrieval chunks.
        Verifies citation validity first; if citations are invalid or missing,
        fails closed as 'unsupported'.
        """
        # Step 1: Citation Check
        missing_ids = [eid for eid in claim.evidence_ids if eid not in retrieved_chunks]
        if missing_ids or not claim.evidence_ids:
            missing_desc = ", ".join(missing_ids) if missing_ids else "empty citation list"
            return ClaimGroundingJudgment(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                evidence_ids=claim.evidence_ids,
                citation_valid=False,
                verdict=GroundingVerdict.UNSUPPORTED,
                rationale=f"Citation check failed: Evidence ID '{missing_desc}' was not retrieved in this encounter.",
                unsupported_spans=[claim.text],
            )

        # Step 2: Build isolated inputs
        inputs = self.build_judge_prompt_inputs(claim, retrieved_chunks)

        # Step 3: Run LLM judge if adapter available, otherwise run deterministic heuristic
        if self.adapter is not None:
            try:
                resp = self.adapter.generate(
                    prompt_name_version=f"grounding_judge@{self.prompt_version}",
                    inputs=inputs,
                    response_schema=JudgeResponseSchema,
                )
                return ClaimGroundingJudgment(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    evidence_ids=claim.evidence_ids,
                    citation_valid=True,
                    verdict=resp.verdict,
                    rationale=resp.rationale,
                    unsupported_spans=resp.unsupported_spans,
                )
            except Exception as exc:
                logger.warning(f"Adapter judge evaluation failed ({exc}), falling back to deterministic evaluator.")

        return self._evaluate_entailment_deterministic(claim, inputs["evidence_text"])

    def _evaluate_entailment_deterministic(
        self,
        claim: ClaimItem,
        evidence_text: str,
    ) -> ClaimGroundingJudgment:
        """
        Deterministic clinical entailment evaluator with zero LLM dependency.
        Audits semantic entailment, detects contradictions, and identifies ungrounded spans.
        """
        claim_norm = claim.text.lower()
        evidence_norm = evidence_text.lower()

        # Tokenize meaningful words (alphanumeric >= 3 chars)
        claim_words = set(re.findall(r"\b[a-z0-9]{3,}\b", claim_norm))
        # Remove common stopwords
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "should",
            "must", "are", "was", "were", "been", "have", "has", "had",
        }
        claim_content_words = claim_words - stopwords

        # 1. Contradiction Detection
        contradiction_markers = [
            ("contraindicated", ["recommend", "recommended", "indicated", "administer", "prescribe", "give"]),
            ("contraindication", ["recommend", "recommended", "indicated", "administer", "prescribe"]),
            ("harmful", ["beneficial", "indicated", "recommend"]),
            ("avoid", ["administer", "indicated", "recommend", "use"]),
            ("strictly contraindicated", ["indicated", "recommended"]),
        ]
        is_contradicted = False
        contradiction_reason = ""
        for neg_term, pos_terms in contradiction_markers:
            if neg_term in evidence_norm:
                for pos in pos_terms:
                    if pos in claim_norm:
                        is_contradicted = True
                        contradiction_reason = f"Evidence specifies '{neg_term}' while claim asserts '{pos}'."
                        break
            if is_contradicted:
                break

        if is_contradicted:
            return ClaimGroundingJudgment(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                evidence_ids=claim.evidence_ids,
                citation_valid=True,
                verdict=GroundingVerdict.UNSUPPORTED,
                rationale=f"Claim is contradicted by cited evidence: {contradiction_reason}",
                unsupported_spans=[claim.text],
            )

        # 2. Overlap and Entity Grounding
        synonyms = {
            "reduces": ["lowers", "decreases", "diminishes", "controls", "drops"],
            "lowers": ["reduces", "decreases", "diminishes"],
            "administer": ["give", "prescribe", "initiate", "provide"],
            "recommended": ["indicated", "preferred", "standard"],
        }
        matching_words = []
        for w in claim_content_words:
            if w in evidence_norm:
                matching_words.append(w)
            elif len(w) >= 5 and (w[:4] in evidence_norm or any(w[:4] in ew for ew in evidence_norm.split())):
                matching_words.append(w)
            elif w in synonyms and any(syn in evidence_norm for syn in synonyms[w]):
                matching_words.append(w)
        overlap_ratio = len(matching_words) / max(len(claim_content_words), 1)

        # 3. Unsubstantiated Extrapolation / Hyperbole Detection
        extrapolation_patterns = [
            "guarantees", "total reversal", "cures completely", "100% effective",
            "permanent cure", "zero risk", "guaranteed", "without fail",
        ]
        unsupported_spans = [p for p in extrapolation_patterns if p in claim_norm]

        if unsupported_spans:
            if overlap_ratio >= 0.20:
                return ClaimGroundingJudgment(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    evidence_ids=claim.evidence_ids,
                    citation_valid=True,
                    verdict=GroundingVerdict.PARTIAL,
                    rationale=f"Core premise supported ({overlap_ratio * 100:.0f}% overlap), but claim includes unverified extrapolations: {unsupported_spans}.",
                    unsupported_spans=unsupported_spans,
                )
            else:
                return ClaimGroundingJudgment(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    evidence_ids=claim.evidence_ids,
                    citation_valid=True,
                    verdict=GroundingVerdict.UNSUPPORTED,
                    rationale="Claim contains ungrounded clinical extrapolations not substantiated by evidence.",
                    unsupported_spans=unsupported_spans,
                )

        # 4. Standard Support vs Unsupported Decision
        if overlap_ratio >= 0.60:
            return ClaimGroundingJudgment(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                evidence_ids=claim.evidence_ids,
                citation_valid=True,
                verdict=GroundingVerdict.SUPPORTED,
                rationale=f"Claim is substantiated by cited evidence ({overlap_ratio * 100:.0f}% semantic concordance).",
                unsupported_spans=[],
            )
        elif overlap_ratio >= 0.35:
            missing_words = list(claim_content_words - set(matching_words))[:3]
            return ClaimGroundingJudgment(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                evidence_ids=claim.evidence_ids,
                citation_valid=True,
                verdict=GroundingVerdict.PARTIAL,
                rationale=f"Claim is partially substantiated ({overlap_ratio * 100:.0f}% overlap). Some details not explicitly found: {missing_words}.",
                unsupported_spans=missing_words,
            )
        else:
            return ClaimGroundingJudgment(
                claim_id=claim.claim_id,
                claim_text=claim.text,
                evidence_ids=claim.evidence_ids,
                citation_valid=True,
                verdict=GroundingVerdict.UNSUPPORTED,
                rationale=f"Insufficient evidence support ({overlap_ratio * 100:.0f}% overlap). Core claims are absent from cited text.",
                unsupported_spans=[claim.text],
            )

    def evaluate_report(
        self,
        report: ClinicalReport,
        retrieved_chunks: Dict[str, str],
    ) -> ReportGroundingResult:
        """Evaluates all claims in a clinical report and aggregates grounding metrics."""
        judgments: List[ClaimGroundingJudgment] = []
        for claim in report.claims:
            j = self.judge_claim(claim, retrieved_chunks)
            judgments.append(j)

        supp = sum(1 for j in judgments if j.verdict == GroundingVerdict.SUPPORTED)
        part = sum(1 for j in judgments if j.verdict == GroundingVerdict.PARTIAL)
        unsup = sum(1 for j in judgments if j.verdict == GroundingVerdict.UNSUPPORTED)
        invalid_cite = sum(1 for j in judgments if not j.citation_valid)

        total = len(judgments)
        ratio = (supp + 0.5 * part) / max(total, 1)
        passed = bool(unsup == 0 and invalid_cite == 0)

        return ReportGroundingResult(
            report_id=report.provenance.run_id if report.provenance else None,
            total_claims=total,
            supported_count=supp,
            partial_count=part,
            unsupported_count=unsup,
            invalid_citation_count=invalid_cite,
            grounding_ratio=round(ratio, 4),
            judgments=judgments,
            passed=passed,
        )


# -----------------------------------------------------------------------------
# Calibration Kit: Cohen's Kappa & Confusion Matrix
# -----------------------------------------------------------------------------

def compute_cohens_kappa(
    rater1: List[str],
    rater2: List[str],
    categories: Optional[List[str]] = None,
) -> float:
    """
    Computes Cohen's kappa coefficient measuring inter-rater reliability.
    Standard formula: kappa = (Po - Pe) / (1 - Pe)
    """
    if len(rater1) != len(rater2) or not rater1:
        return 0.0

    cats = categories or sorted(list(set(rater1) | set(rater2)))
    n = len(rater1)

    # Observed agreement
    agreed = sum(1 for a, b in zip(rater1, rater2) if a == b)
    po = agreed / n

    # Expected chance agreement
    pe = 0.0
    for cat in cats:
        count1 = sum(1 for a in rater1 if a == cat)
        count2 = sum(1 for b in rater2 if b == cat)
        pe += (count1 / n) * (count2 / n)

    if pe >= 1.0:
        return 1.0 if po == 1.0 else 0.0

    kappa = (po - pe) / (1.0 - pe)
    return round(float(kappa), 4)


def compute_confusion_matrix(
    y_true: List[str],
    y_pred: List[str],
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Computes a multi-class confusion matrix and per-category metrics."""
    cats = categories or sorted(list(set(y_true) | set(y_pred)))
    matrix: Dict[str, Dict[str, int]] = {true_cat: {pred_cat: 0 for pred_cat in cats} for true_cat in cats}

    for true_label, pred_label in zip(y_true, y_pred):
        if true_label in matrix and pred_label in matrix[true_label]:
            matrix[true_label][pred_label] += 1

    total = len(y_true)
    correct = sum(matrix[c][c] for c in cats)
    accuracy = correct / max(total, 1)

    return {
        "categories": cats,
        "matrix": matrix,
        "total": total,
        "accuracy": round(accuracy, 4),
    }


def evaluate_calibration(
    labels_csv_path: Path,
    checker: Optional[ClaimGroundingChecker] = None,
) -> Dict[str, Any]:
    """
    Evaluates judge calibration against physician labels in CSV.
    Computes Cohen's kappa and confusion matrix.
    """
    import csv

    if not labels_csv_path.exists():
        raise FileNotFoundError(f"Calibration labels file not found: {labels_csv_path}")

    checker = checker or ClaimGroundingChecker()
    physician_labels: List[str] = []
    predicted_labels: List[str] = []
    rows_evaluated = 0

    with labels_csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_label = (row.get("physician_label") or "").strip().lower()
            if not p_label:
                continue

            # If CSV already contains pre-computed predicted label, use it; otherwise evaluate with checker
            pred_label = (row.get("predicted_label") or "").strip().lower()
            if not pred_label:
                claim = ClaimItem(
                    claim_id=row.get("pair_id", "P-01"),
                    text=row.get("claim_text", ""),
                    type="therapeutic",
                    evidence_ids=[row.get("evidence_id", "E-01")],
                )
                chunks = {row.get("evidence_id", "E-01"): row.get("evidence_text", "")}
                judgment = checker.judge_claim(claim, chunks)
                pred_label = judgment.verdict.value

            physician_labels.append(p_label)
            predicted_labels.append(pred_label)
            rows_evaluated += 1

    cats = ["supported", "partial", "unsupported"]
    kappa = compute_cohens_kappa(physician_labels, predicted_labels, categories=cats)
    cm = compute_confusion_matrix(physician_labels, predicted_labels, categories=cats)

    return {
        "total_pairs": rows_evaluated,
        "cohens_kappa": kappa,
        "confusion_matrix": cm,
    }
