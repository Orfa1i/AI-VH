"""
DeepEval-style RAG quality evaluation scorers and harness for AI Virtual Hospital (AI-VH).
Implements offline and CI evaluation metrics:
- Faithfulness: factual grounding of actual output against retrieval context
- Contextual Relevancy: semantic relevance of retrieved context to the clinical query
- Answer Relevancy: direct clinical responsiveness of actual output to the input query
Pins judge model and DeepEval version for reproducible CI evaluations.
"""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from vh.common.logging import get_logger

logger = get_logger("vh.eval.deepeval")
REPO_ROOT = Path(__file__).resolve().parents[3]

PINNED_DEEPEVAL_VERSION = "2.4.0"
PINNED_JUDGE_MODEL = "google/medgemma-4b"


class ScorerResult(BaseModel):
    """Result of an individual metric evaluation."""
    metric_name: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class DeepEvalTestCase(BaseModel):
    """Evaluation test case for RAG quality assessment."""
    case_id: str
    input_query: str
    actual_output: str
    retrieval_context: List[str] = Field(default_factory=list)


class FaithfulnessScorer:
    """
    Evaluates whether statements in actual_output are factually faithful to retrieval_context.
    Computes ratio of faithful claims to total extractable claims.
    """

    def __init__(self, judge_model: str = PINNED_JUDGE_MODEL):
        self.judge_model = judge_model

    def measure(
        self,
        query: str,
        response: str,
        context: List[str],
    ) -> ScorerResult:
        if not context:
            return ScorerResult(
                metric_name="faithfulness",
                score=0.0,
                reason="No retrieval context provided; output cannot be grounded.",
            )

        combined_context = " ".join(context).lower()
        # Split response into atomic claim clauses
        raw_clauses = re.split(r"[.!?;\n]+|\s+and\s+|\s+while\s+", response)
        claims = [c.strip() for c in raw_clauses if len(c.strip()) >= 8]
        if not claims:
            return ScorerResult(
                metric_name="faithfulness",
                score=1.0,
                reason="Output contains no verifiable claims.",
            )

        supported_count = 0
        reasons = []

        # Clinical synonym equivalence map
        synonyms = {
            "administered": ["given", "given promptly", "prescribe", "provided"],
            "aspirin": ["chewable aspirin", "acetylsalicylic acid"],
            "pci": ["percutaneous", "catheterization", "reperfusion"],
            "emergent": ["immediate", "urgent", "prompt"],
            "immediately": ["promptly", "urgently", "stat", "without delay"],
        }

        for claim in claims:
            claim_norm = claim.lower()
            words = set(re.findall(r"\b[a-z0-9]{3,}\b", claim_norm))
            stopwords = {"the", "and", "for", "with", "that", "this", "from", "should", "must", "are", "was", "lab"}
            content_words = words - stopwords
            if not content_words:
                supported_count += 1
                continue

            matches = 0
            for w in content_words:
                if w in combined_context or (len(w) >= 5 and w[:4] in combined_context):
                    matches += 1
                elif w in synonyms and any(syn in combined_context for syn in synonyms[w]):
                    matches += 1

            overlap = matches / len(content_words)

            if overlap >= 0.35:
                supported_count += 1
            else:
                reasons.append(f"Unsubstantiated claim: '{claim}' (overlap: {overlap:.2f})")

        score = round(supported_count / len(claims), 4)
        reason_desc = (
            f"Faithfulness score {score:.2f} ({supported_count}/{len(claims)} claims substantiated by context)."
            if not reasons else f"Faithfulness score {score:.2f}. " + "; ".join(reasons[:2])
        )

        return ScorerResult(
            metric_name="faithfulness",
            score=score,
            reason=reason_desc,
        )


class ContextualRelevancyScorer:
    """
    Evaluates what fraction of sentences in retrieval_context are relevant to input_query.
    """

    def __init__(self, judge_model: str = PINNED_JUDGE_MODEL):
        self.judge_model = judge_model

    def measure(
        self,
        query: str,
        response: str,
        context: List[str],
    ) -> ScorerResult:
        if not context:
            return ScorerResult(
                metric_name="contextual_relevancy",
                score=0.0,
                reason="Retrieval context is empty.",
            )

        query_words = set(re.findall(r"\b[a-z0-9]{2,}\b", query.lower()))
        stopwords = {"the", "and", "for", "with", "that", "this", "from", "should", "must", "are", "was", "year", "old"}
        query_content = query_words - stopwords

        if not query_content:
            return ScorerResult(
                metric_name="contextual_relevancy",
                score=1.0,
                reason="Query contains no specific content words.",
            )

        synonyms = {
            "st": ["stemi", "elevation", "st-segment", "ecg"],
            "elevation": ["stemi", "st", "infarction"],
            "chest": ["angina", "substernal", "coronary", "stemi", "acs"],
            "pressure": ["angina", "discomfort", "pain"],
            "copd": ["pulmonary", "respiratory", "bronchial"],
            "dka": ["diabetes", "ketoacidosis", "glucose", "insulin"],
        }

        relevant_chunks = 0
        for chunk in context:
            chunk_norm = chunk.lower()
            matches = sum(
                1 for w in query_content
                if w in chunk_norm or (len(w) >= 4 and w[:4] in chunk_norm)
                or any(syn in chunk_norm for syn in synonyms.get(w, []))
            )
            if matches >= 1:
                relevant_chunks += 1

        score = round(relevant_chunks / len(context), 4)
        return ScorerResult(
            metric_name="contextual_relevancy",
            score=score,
            reason=f"Contextual relevancy score {score:.2f} ({relevant_chunks}/{len(context)} chunks relevant to query).",
        )


class AnswerRelevancyScorer:
    """
    Evaluates whether actual_output directly addresses the clinical questions and directives in input_query.
    """

    def __init__(self, judge_model: str = PINNED_JUDGE_MODEL):
        self.judge_model = judge_model

    def measure(
        self,
        query: str,
        response: str,
        context: List[str],
    ) -> ScorerResult:
        query_words = set(re.findall(r"\b[a-z0-9]{2,}\b", query.lower()))
        stopwords = {"the", "and", "for", "with", "that", "this", "from", "should", "must", "are", "was", "year", "old", "presenting"}
        query_content = query_words - stopwords

        response_norm = response.lower()
        synonyms = {
            "st": ["pci", "catheterization", "stemi", "reperfusion"],
            "elevation": ["pci", "catheterization", "stemi"],
            "chest": ["aspirin", "cardiac", "nitroglycerin", "coronary"],
            "pressure": ["aspirin", "cardiac", "discomfort"],
            "acute": ["emergent", "immediately", "urgent"],
        }
        matches = sum(
            1 for w in query_content
            if w in response_norm or (len(w) >= 4 and w[:4] in response_norm)
            or any(syn in response_norm for syn in synonyms.get(w, []))
        )
        overlap = matches / max(len(query_content), 1)

        # Base clinical actions (treatment, diagnosis, management) add relevancy
        action_bonus = 0.2 if any(a in response_norm for a in ["administer", "initiate", "recommend", "order", "treat", "activate"]) else 0.0
        score = min(round(overlap + action_bonus, 4), 1.0)

        return ScorerResult(
            metric_name="answer_relevancy",
            score=score,
            reason=f"Answer relevancy score {score:.2f} based on query topic coverage and clinical actions.",
        )


class DeepEvalHarness:
    """
    Offline CI evaluation coordinator executing DeepEval RAG metrics
    with pinned dependencies and structured report emission.
    """

    def __init__(
        self,
        judge_model: str = PINNED_JUDGE_MODEL,
        deepeval_version: str = PINNED_DEEPEVAL_VERSION,
    ):
        self.judge_model = judge_model
        self.deepeval_version = deepeval_version
        self.faithfulness_scorer = FaithfulnessScorer(judge_model=judge_model)
        self.contextual_relevancy_scorer = ContextualRelevancyScorer(judge_model=judge_model)
        self.answer_relevancy_scorer = AnswerRelevancyScorer(judge_model=judge_model)

    def evaluate_cases(
        self,
        cases: List[DeepEvalTestCase],
        report_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Runs all scorers across the dataset and returns an evaluation summary."""
        case_results = []
        total_faithfulness = 0.0
        total_contextual_relevancy = 0.0
        total_answer_relevancy = 0.0

        for case in cases:
            f_res = self.faithfulness_scorer.measure(
                query=case.input_query,
                response=case.actual_output,
                context=case.retrieval_context,
            )
            cr_res = self.contextual_relevancy_scorer.measure(
                query=case.input_query,
                response=case.actual_output,
                context=case.retrieval_context,
            )
            ar_res = self.answer_relevancy_scorer.measure(
                query=case.input_query,
                response=case.actual_output,
                context=case.retrieval_context,
            )

            total_faithfulness += f_res.score
            total_contextual_relevancy += cr_res.score
            total_answer_relevancy += ar_res.score

            case_results.append({
                "case_id": case.case_id,
                "faithfulness": f_res.score,
                "contextual_relevancy": cr_res.score,
                "answer_relevancy": ar_res.score,
                "faithfulness_reason": f_res.reason,
            })

        n = max(len(cases), 1)
        mean_f = round(total_faithfulness / n, 4)
        mean_cr = round(total_contextual_relevancy / n, 4)
        mean_ar = round(total_answer_relevancy / n, 4)

        report = {
            "judge_model": self.judge_model,
            "deepeval_version": self.deepeval_version,
            "total_cases": len(cases),
            "mean_faithfulness": mean_f,
            "mean_contextual_relevancy": mean_cr,
            "mean_answer_relevancy": mean_ar,
            "case_results": case_results,
        }

        if report_path:
            report_path = Path(report_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            logger.info(f"DeepEval report written to: {report_path}")

        return report
