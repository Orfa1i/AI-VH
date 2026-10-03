"""
Grounded Clinical Generation Pipeline for AI Virtual Hospital (AI-VH).
Implements the evaluation harness Pipeline protocol:
  AgentView -> QueryPlanner -> Multi-Source Retrieval -> Context Assembly ->
  MedGemmaAdapter (clinical_report@1) -> Referential Integrity Validation -> PipelineResult
Enforces pre-generation and post-generation abstention, token budget constraints,
and fail-closed error reporting with zero silent drops.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from vh.cases.schema import CaseView
from vh.common.logging import get_logger
from vh.cases.retrieval_log import RetrievalLog, assert_retrieval_log_present, MissingRetrievalLogError
from vh.rag.retrieval import TwoPassRetrievalConfig
from vh.rag.sources.base import SourceDocument
from vh.rag.chunking import StructureAwareChunker, ChunkerConfig, Chunk
from vh.rag.indexing import VersionedHybridIndex, get_embedding_model
from vh.rag.retrieval import (
    UnifiedRetrievalService,
    RetrievalRequest,
    RetrievalFilters,
    EvidenceItem,
)
from vh.rag.sources.guidelines import LocalGuidelinesAdapter
from vh.generation.report import (
    ClinicalReport,
    DifferentialItem,
    RecommendationItem,
    ClaimItem,
    AbstentionItem,
    ReportProvenance,
    validate_clinical_report,
    IntegrityValidationError,
)
from vh.generation.medgemma import (
    MedGemmaAdapter,
    MedGemmaConfig,
    GenerationFailed,
    GenerationTimeoutError,
)
from eval.harness.interfaces import Pipeline, PipelineResult

logger = get_logger("vh.generation.pipeline")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Phase 1 mandatory-retrieval guard + grounding status.
# Legacy run() is preserved for backward compatibility (existing tests/endpoints).
# New code must use run_with_log() / require_retrieval_log(): no retrieval_log
# means the generation call is refused. INSUFFICIENT_GROUNDING reports may be
# shown to a physician but must never be exported as training data (Phase 5).
# Owner: AI Engineer.
INSUFFICIENT_GROUNDING = "insufficient_grounding"


def require_retrieval_log(log: RetrievalLog | None) -> RetrievalLog:
    """Hard guard: refuse generation when no (or empty) retrieval_log is given."""
    return assert_retrieval_log_present(log)


class QueryPlanner:
    """Plans targeted clinical sub-queries across distinct diagnostic and therapeutic dimensions."""

    def plan_queries(self, case_view: CaseView) -> Dict[str, str]:
        pres = case_view.visible_presentation
        chief = pres.get("chief_complaint", "")
        hpi = pres.get("history") or pres.get("history_of_present_illness", "")
        labs = pres.get("initial_labs") or pres.get("labs", {})
        vitals = pres.get("vitals", {})

        labs_str = " ".join(f"{k}: {v}" for k, v in labs.items()) if isinstance(labs, dict) else str(labs)
        vitals_str = " ".join(f"{k}: {v}" for k, v in vitals.items()) if isinstance(vitals, dict) else str(vitals)

        return {
            "presentation": f"{chief}. {hpi}".strip(),
            "differential": f"differential diagnosis guidelines for {chief} abnormal findings {labs_str}".strip(),
            "workup": f"diagnostic workup laboratory evaluation imaging for {chief} {vitals_str}".strip(),
            "management": f"clinical practice guideline acute management therapy medications for {chief}".strip(),
        }


_CACHED_RETRIEVAL_SERVICE: Optional[UnifiedRetrievalService] = None


def get_default_retrieval_service(repo_root: Optional[Path] = None) -> UnifiedRetrievalService:
    """Lazily builds and caches default UnifiedRetrievalService from local guidelines."""
    global _CACHED_RETRIEVAL_SERVICE
    if _CACHED_RETRIEVAL_SERVICE is not None:
        return _CACHED_RETRIEVAL_SERVICE

    root = Path(repo_root or REPO_ROOT)
    guidelines_dir = root / "data" / "sources" / "guidelines"

    adapter = LocalGuidelinesAdapter(guidelines_dir=guidelines_dir)
    docs = adapter.load_all()

    chunker = StructureAwareChunker(config=ChunkerConfig(target_chunk_tokens=256, max_chunk_tokens=384))
    chunks: List[Chunk] = []
    for d in docs:
        chunks.extend(chunker.chunk_document(d))

    embedder = get_embedding_model("general")
    index = VersionedHybridIndex(
        index_id="default_pipeline_index",
        storage_dir=root / "data" / "cache" / "pipeline_index_general",
    )
    index.build(chunks=chunks, embedding_model=embedder, index_version="v1.0")

    _CACHED_RETRIEVAL_SERVICE = UnifiedRetrievalService(index=index)
    return _CACHED_RETRIEVAL_SERVICE


class GroundedGenerationPipeline(Pipeline):
    """
    Evidence-grounded generation pipeline implementing the evaluation harness Pipeline protocol.
    Coordinates sub-query retrieval, context assembly within token budget, MedGemma generation,
    pre-generation abstention detection, and post-generation referential integrity verification.
    """

    def __init__(
        self,
        retrieval_service: Optional[UnifiedRetrievalService] = None,
        adapter: Optional[MedGemmaAdapter] = None,
        runner: Optional[Callable[..., str]] = None,
        token_budget: int = 2000,
        min_retrieval_score: float = 0.01,
        suppress_management_evidence: bool = False,
    ):
        self.retrieval_service = retrieval_service
        self.runner = runner
        self.token_budget = token_budget
        self.min_retrieval_score = min_retrieval_score
        self.suppress_management_evidence = suppress_management_evidence

        if adapter is not None:
            self.adapter = adapter
        else:
            config = MedGemmaConfig(model_id="google/medgemma-4b", temperature=0.0)
            self.adapter = MedGemmaAdapter(config=config, runner=runner)

        self.query_planner = QueryPlanner()

    def _get_retrieval_service(self) -> UnifiedRetrievalService:
        if self.retrieval_service is None:
            self.retrieval_service = get_default_retrieval_service()
        return self.retrieval_service

    def run(self, case_view: CaseView) -> PipelineResult:
        """
        Executes end-to-end grounded generation on a single patient CaseView.
        Returns a PipelineResult containing the report, active evidence citations, and execution status.
        """
        case_id = case_view.case_id
        logger.info(f"Executing GroundedGenerationPipeline for case {case_id}")

        # 1. AgentView extraction: assemble presentation string and findings
        pres = case_view.visible_presentation
        chief = pres.get("chief_complaint", "")
        hpi = pres.get("history") or pres.get("history_of_present_illness", "")
        vitals = pres.get("vitals", {})
        exam = pres.get("exam") or pres.get("physical_exam", {})
        labs = pres.get("initial_labs") or pres.get("labs", {})

        patient_summary = f"Patient presentation: {chief}. HPI: {hpi}."
        findings: List[str] = []
        if isinstance(vitals, dict):
            for k, v in vitals.items():
                findings.append(f"Vital {k}: {v}")
        if isinstance(exam, dict):
            for k, v in exam.items():
                findings.append(f"Physical Exam ({k}): {v}")
        if isinstance(labs, dict):
            for k, v in labs.items():
                findings.append(f"Investigation ({k}): {v}")

        # 2. Query planning: sub-queries across clinical dimensions
        sub_queries = self.query_planner.plan_queries(case_view)

        # 3. Retrieval across sub-queries
        service = self._get_retrieval_service()
        collected_evidence: Dict[str, EvidenceItem] = {}
        section_evidence_counts: Dict[str, int] = {sec: 0 for sec in sub_queries}

        for sec_name, query_text in sub_queries.items():
            if not query_text:
                continue
            retrieved = service.retrieve(
                query=query_text,
                k=5,
                max_source_share=0.5,
                rerank=False,
                include_superseded=False,
            )

            # Optional suppression for testing abstention behavior
            if self.suppress_management_evidence and sec_name == "management":
                retrieved = []

            for item in retrieved:
                score = item.rrf_score
                if score >= self.min_retrieval_score or score == 0.0:
                    section_evidence_counts[sec_name] += 1
                    cid = item.chunk_id or item.evidence_id
                    if cid not in collected_evidence:
                        collected_evidence[cid] = item

        # 4. Pre-generation abstention detection
        pre_abstentions: List[AbstentionItem] = []
        if section_evidence_counts.get("management", 0) == 0:
            pre_abstentions.append(
                AbstentionItem(
                    question="Evidence-based acute management and pharmacotherapy",
                    reason="No clinical guideline evidence retrieved above confidence threshold for management recommendations.",
                )
            )
        if section_evidence_counts.get("workup", 0) == 0 and len(labs) == 0:
            pre_abstentions.append(
                AbstentionItem(
                    question="Comprehensive diagnostic laboratory workup protocol",
                    reason="Insufficient evidence retrieved to recommend specialized tertiary diagnostic workup.",
                )
            )

        # 5. Context assembly: token budget enforcement
        ranked_items = sorted(collected_evidence.values(), key=lambda x: x.rrf_score, reverse=True)
        assembled_items: List[EvidenceItem] = []
        token_count = 0

        for item in ranked_items:
            approx_tokens = max(1, len(item.text.split()) * 4 // 3)
            if token_count + approx_tokens <= self.token_budget:
                assembled_items.append(item)
                token_count += approx_tokens
            else:
                break

        active_evidence_ids = [item.chunk_id or item.evidence_id for item in assembled_items]

        # 6. Format generation inputs
        evidence_payload = [
            {
                "chunk_id": item.chunk_id or item.evidence_id,
                "source": item.source,
                "title": getattr(item, "document_title", "") or item.metadata.get("title", "Clinical Guideline"),
                "text": item.text,
            }
            for item in assembled_items
        ]

        generation_inputs: Dict[str, Any] = {
            "case_id": case_id,
            "specialty": case_view.specialty,
            "patient_summary": patient_summary,
            "findings": findings,
            "retrieved_evidence": evidence_payload,
            "active_evidence_ids": active_evidence_ids,
            "pre_abstentions": [a.model_dump() for a in pre_abstentions],
        }

        # 7. Model Generation via MedGemmaAdapter
        try:
            raw_report = self.adapter.generate(
                prompt_name_version="clinical_report@1",
                inputs=generation_inputs,
                response_schema=ClinicalReport,
            )

            # Ensure report object
            if isinstance(raw_report, dict):
                report = ClinicalReport.model_validate(raw_report)
            else:
                report = raw_report

            # Merge pre-generation abstentions if model omitted them
            existing_questions = {a.question for a in report.abstentions}
            for pre_abs in pre_abstentions:
                if pre_abs.question not in existing_questions:
                    report.abstentions.append(pre_abs)

            # If management was suppressed, prune ungrounded management recommendations
            if self.suppress_management_evidence:
                report.recommendations = [
                    r for r in report.recommendations
                    if any(cid in {c.claim_id for c in report.claims if any(eid in active_evidence_ids for eid in c.evidence_ids)} for cid in r.claim_ids)
                ]

            # Validate referential integrity
            validate_clinical_report(report, valid_evidence_ids=active_evidence_ids)

            status = "abstained_partial" if pre_abstentions else "success"
            primary_dx = report.differential[0].dx if report.differential else "Abstained"

            return PipelineResult(
                case_id=case_id,
                diagnosis=primary_dx,
                differential=[d.dx for d in report.differential],
                suggested_orders=[r.text for r in report.recommendations],
                clinical_summary=report.patient_summary,
                metadata={
                    "clinical_report": report.model_dump(),
                    "active_evidence_ids": active_evidence_ids,
                    "abstentions": [a.model_dump() for a in report.abstentions],
                    "claims": [c.model_dump() for c in report.claims],
                    "generation_status": status,
                },
            )

        except (GenerationFailed, GenerationTimeoutError, IntegrityValidationError, Exception) as exc:
            logger.error(f"Generation failed for case {case_id}: {exc}")
            return PipelineResult(
                case_id=case_id,
                diagnosis="Generation Failed",
                differential=[],
                suggested_orders=[],
                clinical_summary="Clinical generation failed validation constraints after retry exhaustion.",
                metadata={
                    "generation_status": "generation_failed",
                    "error": str(exc),
                    "active_evidence_ids": active_evidence_ids,
                },
            )

    def run_with_log(self, case_view: CaseView, retrieval_log: RetrievalLog | None) -> PipelineResult:
        """
        Phase 1 guarded entry point: retrieval_log is mandatory.

        Raises MissingRetrievalLogError when the log is missing/empty (the
        generation call is refused). Returns an INSUFFICIENT_GROUNDING result
        when the log carries no chunk above threshold: reviewable by a
        physician but never exportable as training data.
        """
        require_retrieval_log(retrieval_log)
        assert retrieval_log is not None
        if not retrieval_log.chunks:
            logger.warning(f"No grounding chunks for case {case_view.case_id}: INSUFFICIENT_GROUNDING")
            return PipelineResult(
                case_id=case_view.case_id,
                diagnosis="Insufficient Grounding",
                differential=[],
                suggested_orders=[],
                clinical_summary="Insufficient Harrison grounding: no chunk passed the retrieval threshold.",
                metadata={
                    "generation_status": INSUFFICIENT_GROUNDING,
                    "active_evidence_ids": [],
                    "retrieval_log": retrieval_log.model_dump(),
                },
            )
        result = self.run(case_view)
        metadata = dict(result.metadata or {})
        metadata["retrieval_log"] = retrieval_log.model_dump()
        return PipelineResult(
            case_id=result.case_id,
            diagnosis=result.diagnosis,
            differential=list(result.differential or []),
            suggested_orders=list(result.suggested_orders or []),
            clinical_summary=result.clinical_summary,
            metadata=metadata,
        )

    def run_grounded_assessment(
        self,
        case_id: str,
        specialty: str,
        structured_case: Dict[str, Any],
        candidate_differentials: Optional[List[str]] = None,
        report_id: Optional[str] = None,
        search_fn: Optional[Callable[..., Any]] = None,
        phase2_config: Optional[Any] = None,
    ) -> PipelineResult:
        """
        Phase 2 grounded path: structured case -> two-pass Harrison retrieval
        (mandatory guard) -> v2 assessment -> raw outputs stored alongside.

        Does not touch the legacy run() path. Legacy callers are unaffected.
        """
        import uuid

        from vh.cases.retrieval_log import new_retrieval_log, record_query
        from vh.rag.retrieval import (
            TwoPassRetrievalConfig,
            build_pass1_query,
            format_harrison_context,
            two_pass_retrieve,
        )
        from vh.generation.medgemma import (
            GenerationFailed,
            MedGemmaAdapter,
            Phase2GenerationConfig,
            heuristic_assessment,
        )

        cfg = phase2_config or Phase2GenerationConfig()
        rid = report_id or f"REP-{uuid.uuid4().hex[:6].upper()}"
        log = new_retrieval_log(case_id)

        if search_fn is None:
            from vh.rag.sources.harrison import HarrisonAdapter

            _harrison = HarrisonAdapter()
            search_fn = _harrison.search

        # Wrap search to retain every fetched hit (full text) for the retrieval log,
        # including chunks that later fall outside the context cap.
        seen_hits: Dict[str, Any] = {}
        _inner_search = search_fn

        def _recording_search(query: str, top_k: int = 6) -> List[Any]:
            fetched = _inner_search(query, top_k=top_k) or []
            for hit in fetched:
                cid = str(getattr(hit, "chunk_id", "") or "")
                if cid and cid not in seen_hits:
                    seen_hits[cid] = hit
            return fetched

        adapter = self.adapter if isinstance(self.adapter, MedGemmaAdapter) else MedGemmaAdapter()

        # Pass 1: symptoms + findings query (recorded even when empty).
        pass1_query = build_pass1_query(structured_case)
        pass1_hits: List[Any] = []
        if pass1_query:
            pass1_hits = _recording_search(pass1_query, top_k=6) or []
            record_query(log, pass1_query, 6, pass1_hits)

        # Candidate differential (LLM micro-call, heuristic fallback inside).
        candidates = list(candidate_differentials or [])
        if not candidates:
            pass1_context = format_harrison_context(pass1_hits[:3])
            try:
                candidates = adapter.generate_candidates(structured_case, pass1_context, cfg)
            except GenerationFailed:
                from vh.generation.medgemma import heuristic_candidates

                candidates = heuristic_candidates(structured_case)

        # Pass 2: targeted per-candidate queries with threshold, dedup and cap.
        tp_config = TwoPassRetrievalConfig(top_k_per_query=6, max_total_chunks=24)
        hits, records = two_pass_retrieve(_recording_search, structured_case, candidates, tp_config)
        for record in records:
            record_hits = [seen_hits[cid] for cid in record.returned_chunk_ids if cid in seen_hits]
            record_query(log, record.query, record.top_k, record_hits)

        active_ids = [str(getattr(h, "chunk_id", "")) for h in hits if getattr(h, "chunk_id", "")]
        if not active_ids:
            logger.warning(f"No grounding chunks for case {case_id}: INSUFFICIENT_GROUNDING")
            return PipelineResult(
                case_id=case_id,
                diagnosis="Insufficient Grounding",
                differential=[],
                suggested_orders=[],
                clinical_summary="Insufficient Harrison grounding: no chunk passed the retrieval threshold.",
                metadata={
                    "generation_status": INSUFFICIENT_GROUNDING,
                    "active_evidence_ids": [],
                    "retrieval_log": log.model_dump(),
                    "prompt_version": cfg.prompt_version,
                },
            )

        harrison_context = format_harrison_context(hits)
        try:
            assessment_result = adapter.generate_assessment(
                structured_case=structured_case,
                harrison_context=harrison_context,
                retrieval_chunk_ids=active_ids,
                report_id=rid,
                case_id=case_id,
                candidates=candidates,
                config=cfg,
            )
            report = assessment_result.report
            raw_attempts = list(assessment_result.raw_attempts)
            parse_stats = assessment_result.parse_stats.model_dump()
        except GenerationFailed as exc:
            logger.error(f"Grounded assessment failed for case {case_id}: {exc}")
            return PipelineResult(
                case_id=case_id,
                diagnosis="Generation Failed",
                differential=[],
                suggested_orders=[],
                clinical_summary="Grounded assessment failed validation constraints after retry exhaustion.",
                metadata={
                    "generation_status": "generation_failed",
                    "error": str(exc),
                    "active_evidence_ids": active_ids,
                    "retrieval_log": log.model_dump(),
                    "prompt_version": cfg.prompt_version,
                },
            )

        return PipelineResult(
            case_id=case_id,
            diagnosis=report.final_diagnosis.diagnosis,
            differential=[d.diagnosis for d in report.differential_diagnosis],
            suggested_orders=[w.test for w in report.workup] + [t.item for t in report.treatment],
            clinical_summary=report.case_summary,
            metadata={
                "generation_status": "success",
                "assessment_report": report.model_dump(),
                "raw_model_output": raw_attempts,
                "parse_stats": parse_stats,
                "active_evidence_ids": active_ids,
                "retrieval_log": log.model_dump(),
                "prompt_version": cfg.prompt_version,
            },
        )
