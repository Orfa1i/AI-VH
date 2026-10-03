"""
Phase 1 acceptance tests: structured case extraction + mandatory Harrison retrieval.

Covers prompt FOR UPDATE/01_Phase1 plus owner amendments:
- structured extractor never invents values (amendment 2)
- hard guard: no retrieval_log -> generation refused
- two-pass retrieval shape (top_k 5-8, dedup, cap)
- INSUFFICIENT_GROUNDING when nothing passes threshold
- Harrison metadata backfill (ids/text preserved, JSON only, .npy untouched)
- SourceAdapter.search() interface
- /api/rl/train 503 latch + status 200 (amendment 6)

Owner: QA Engineer. Fixture content spec: Medical Expert.
Markers: unit + integration (no live network; see tests/conftest.py).
"""

import json
from pathlib import Path

import pytest

from vh.cases.structured_case import extract_structured_case
from vh.cases.retrieval_log import (
    RetrievalLog,
    new_retrieval_log,
    record_query,
    assert_retrieval_log_present,
    MissingRetrievalLogError,
)
from vh.rag.sources.base import SourceSearchHit
from vh.rag.sources.harrison import HarrisonAdapter, enrich_harrison_metadata
from vh.rag.retrieval import (
    TwoPassRetrievalConfig,
    build_pass1_query,
    build_pass2_queries,
    dedupe_and_cap,
    two_pass_retrieve,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "phase1" / "charles_brown_realistic.json"


def _hit(cid: str, score: float, text: str = "chunk text") -> SourceSearchHit:
    return SourceSearchHit(
        source_name="harrison",
        chunk_id=cid,
        metadata={"chunk_id": cid},
        text=text,
        score=score,
    )


# --- Structured extraction -------------------------------------------------

@pytest.mark.unit
def test_charles_brown_fixture_is_synthetic_and_complete() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["_meta"]["is_synthetic"] is True
    case = extract_structured_case(payload["raw_case"])
    assert case.age == 68
    assert case.sex == "male"
    assert "pneumonia" not in case.chief_complaint.lower(), "chief complaint must be symptoms only"
    assert "fever" in case.chief_complaint.lower()
    assert case.vitals.spo2 == 89
    assert case.missing_data == [], f"complete fixture must have no missing_data, got {case.missing_data}"


@pytest.mark.unit
def test_structured_extractor_never_invents_values() -> None:
    """Amendment 2: sparse input -> everything None/empty + listed in missing_data."""
    case = extract_structured_case({})
    assert case.age is None
    assert case.sex is None
    assert case.presenting_symptoms == []
    assert case.symptom_duration is None
    assert case.chief_complaint == ""
    assert case.vitals.temp is None
    assert case.vitals.hr is None
    assert case.vitals.rr is None
    assert case.vitals.bp is None
    assert case.vitals.spo2 is None
    assert case.examination_findings is None
    assert case.comorbidities == []
    assert case.current_medications == []
    assert case.allergies == []
    assert case.labs == {}
    assert case.imaging == {}
    for label in (
        "age", "sex", "presenting_symptoms", "symptom_duration",
        "vitals.temp", "vitals.hr", "vitals.rr", "vitals.bp", "vitals.spo2",
        "examination_findings", "comorbidities", "current_medications",
        "allergies", "labs", "imaging",
    ):
        assert label in case.missing_data


@pytest.mark.unit
def test_structured_extractor_partial_input_lists_only_absent() -> None:
    case = extract_structured_case({"age": 55, "sex": "female", "presenting_symptoms": ["cough"]})
    assert case.age == 55
    assert "age" not in case.missing_data
    assert "vitals.hr" in case.missing_data
    assert "labs" in case.missing_data


# --- Mandatory guard + retrieval log ----------------------------------------

@pytest.mark.unit
def test_generation_refused_without_retrieval_log() -> None:
    with pytest.raises(MissingRetrievalLogError):
        assert_retrieval_log_present(None)
    with pytest.raises(MissingRetrievalLogError):
        assert_retrieval_log_present(new_retrieval_log("CASE-X"))


@pytest.mark.unit
def test_retrieval_log_records_queries_scores_and_full_text() -> None:
    log = new_retrieval_log("CASE-1")
    record_query(log, "fever cough", 6, [_hit("H-1", 0.8, "full text one"), _hit("H-2", 0.5, "full text two")])
    assert len(log.queries) == 1
    assert log.queries[0].returned_chunk_ids == ["H-1", "H-2"]
    assert log.chunks["H-1"].text == "full text one"
    assert log.chunks["H-1"].score == 0.8
    assert_retrieval_log_present(log)


@pytest.mark.unit
def test_pipeline_run_with_log_refuses_without_log() -> None:
    from vh.cases.schema import CaseView
    from vh.generation.pipeline import GroundedGenerationPipeline

    pipeline = GroundedGenerationPipeline.__new__(GroundedGenerationPipeline)
    view = CaseView(case_id="C1", specialty="Pulmonology", patient_ref="P1", visible_presentation={})
    with pytest.raises(MissingRetrievalLogError):
        pipeline.run_with_log(view, None)


@pytest.mark.unit
def test_pipeline_run_with_log_insufficient_grounding() -> None:
    from vh.cases.schema import CaseView
    from vh.generation.pipeline import GroundedGenerationPipeline, INSUFFICIENT_GROUNDING

    pipeline = GroundedGenerationPipeline.__new__(GroundedGenerationPipeline)
    view = CaseView(case_id="C1", specialty="Pulmonology", patient_ref="P1", visible_presentation={})
    log = new_retrieval_log("C1")
    record_query(log, "fever cough", 6, [])
    # queries recorded but zero passing chunks -> INSUFFICIENT_GROUNDING, not generation
    log.queries.append(log.queries.pop())  # keep single query record
    result = pipeline.run_with_log(view, log)
    assert result.metadata["generation_status"] == INSUFFICIENT_GROUNDING


# --- Two-pass retrieval -------------------------------------------------------

@pytest.mark.unit
def test_two_pass_queries_dedup_and_cap() -> None:
    calls: list = []

    def fake_search(query: str, top_k: int = 6) -> list:
        calls.append((query, top_k))
        assert 5 <= top_k <= 8
        if "fever" in query:
            return [_hit("H-1", 0.9), _hit("H-2", 0.4)]
        return [_hit("H-2", 0.7), _hit("H-3", 0.6)]

    structured = {"presenting_symptoms": ["fever", "cough"], "examination_findings": "crackles"}
    hits, records = two_pass_retrieve(
        fake_search, structured, ["Community-acquired pneumonia"], TwoPassRetrievalConfig(top_k_per_query=6)
    )
    assert build_pass1_query(structured) != ""
    assert len(records) == 1 + 4  # pass1 + 4 targeted queries per candidate
    ids = [h.chunk_id for h in hits]
    assert len(ids) == len(set(ids)), "duplicates must be collapsed"
    assert "H-1" in ids and "H-3" in ids


@pytest.mark.unit
def test_pass2_query_targets() -> None:
    queries = build_pass2_queries("Community-acquired pneumonia")
    assert set(queries) == {"diagnostic_criteria", "severity_scoring", "workup", "management"}


@pytest.mark.unit
def test_dedupe_keeps_highest_score_and_caps() -> None:
    hits = [_hit("H-1", 0.2), _hit("H-1", 0.9), _hit("H-2", 0.5)]
    out = dedupe_and_cap(hits, 2)
    assert [h.chunk_id for h in out] == ["H-1", "H-2"]
    assert out[0].score == 0.9


# --- Harrison metadata + adapter ---------------------------------------------

@pytest.mark.unit
def test_harrison_metadata_never_fabricates() -> None:
    meta = enrich_harrison_metadata({"id": "X", "book": "", "chapter": "", "topic": "", "page": None})
    assert meta["edition"] is None
    assert meta["chapter_number"] is None
    assert meta["page"] is None
    meta2 = enrich_harrison_metadata(
        {"id": "Y", "book": "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
         "chapter": "121 Pneumonia", "topic": "Clinical Features", "page": 321}
    )
    assert meta2["edition"] == "21st Edition (2022)"
    assert meta2["chapter_number"] == "121"
    assert meta2["page"] == 321


@pytest.mark.unit
def test_harrison_backfill_preserves_ids_and_text() -> None:
    backup = REPO_ROOT / "data" / "knowledge" / "backup_phase1_20261004_002547" / "harrison_full_collection.json"
    current = REPO_ROOT / "data" / "knowledge" / "harrison_full_collection.json"
    if not backup.exists():
        pytest.skip("phase 1 backup not present")
    old = json.loads(backup.read_text(encoding="utf-8"))
    new = json.loads(current.read_text(encoding="utf-8"))
    assert len(old) == len(new)
    assert [e["id"] for e in old] == [e["id"] for e in new]
    assert all(a.get("text") == b.get("text") for a, b in zip(old, new))
    sample = new[0]
    for key in ("edition", "chapter_number", "chapter_title", "section_heading"):
        assert key in sample, f"backfilled key missing: {key}"


@pytest.mark.unit
def test_harrison_npy_untouched() -> None:
    npy = REPO_ROOT / "data" / "knowledge" / "harrison_embeddings.npy"
    assert npy.exists()
    assert npy.stat().st_size == 48272000


@pytest.mark.unit
def test_harrison_adapter_search_interface(tmp_path: Path) -> None:
    collection = [
        {"id": "H-1", "book": "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
         "chapter": "121 Pneumonia", "topic": "Treatment", "page": 321,
         "specialty": "Internal Medicine", "text": "Empiric antibiotic therapy for community-acquired pneumonia."},
        {"id": "H-2", "book": "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
         "chapter": "269 ACS", "topic": "Management", "page": 1820,
         "specialty": "Internal Medicine", "text": "Aspirin and heparin for acute coronary syndrome."},
    ]
    path = tmp_path / "harrison_mini.json"
    path.write_text(json.dumps(collection), encoding="utf-8")
    adapter = HarrisonAdapter(collection_path=path)
    hits = adapter.search("pneumonia antibiotic therapy", top_k=6)
    assert hits, "expected at least one Harrison hit"
    first = hits[0]
    assert first.source_name == "harrison"
    assert first.chunk_id in ("H-1", "H-2")
    assert set(first.metadata) >= {"chunk_id", "edition", "chapter_title", "page"}
    assert first.text != ""
    assert first.metadata.get("retrieval_mode") == "lexical-fallback"


@pytest.mark.integration
def test_harrison_semantic_search_uses_embeddings() -> None:
    """BLOCKER fix: semantic retrieval over harrison_embeddings.npy (cosine [0, 1])."""
    adapter = HarrisonAdapter()
    hits = adapter.search("fever productive cough consolidation pneumonia antibiotic", top_k=6)
    assert len(hits) == 6
    assert all(h.metadata.get("retrieval_mode") == "semantic-hybrid" for h in hits)
    assert all(0.0 <= h.score <= 1.0 for h in hits), "score scale is cosine similarity clipped to [0, 1]"
    chapters = " ".join(str(h.metadata.get("chapter_title") or "") for h in hits).lower()
    respiratory = {"pneumonia", "pneumococcal", "mycoplasma", "respiratory", "pertussis", "bronchi"}
    assert sum(1 for term in respiratory if term in chapters) >= 3, f"expected respiratory theme, got: {chapters}"


# --- RL train 503 latch --------------------------------------------------------

@pytest.mark.integration
def test_rl_train_blocked_until_phase5(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VH_ALLOW_RL_TRAIN", raising=False)
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.post("/api/rl/train", json={"epochs": 1, "dry_run": True})
    assert resp.status_code == 503, f"expected 503 latch, got {resp.status_code}: {resp.text}"
    assert "Phase 5" in resp.json().get("detail", "")
    status = client.get("/api/rl/train/status")
    assert status.status_code == 200
