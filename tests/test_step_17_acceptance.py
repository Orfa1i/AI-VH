"""
Acceptance criteria tests for STEP 17 (P2.4):
Unified hybrid retrieval API, RRF fusion, source diversity cap,
superseded exclusion, filtering, locator resolution, and API contract.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from vh.rag.sources.base import SourceDocument
from vh.rag.chunking import ChunkerConfig, StructureAwareChunker
from vh.rag.indexing import get_embedding_model, VersionedHybridIndex
from vh.rag.retrieval import (
    EvidenceItem,
    RetrievalFilters,
    RetrievalRequest,
    RetrievalResponse,
    UnifiedRetrievalService,
    RetrievalClient,
    resolve_locator,
)
from vh.common.tracing import get_recorded_spans, clear_recorded_spans

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDELINES_DIR = REPO_ROOT / "data" / "sources" / "guidelines"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "rag_sources"


@pytest.fixture
def populated_index(tmp_path):
    chunker = StructureAwareChunker(config=ChunkerConfig(target_chunk_tokens=50, max_chunk_tokens=100))

    # Guideline doc (Cardiology)
    doc_gl = SourceDocument(
        source_id="guidelines",
        doc_id="DOC-ACS-001",
        title="2023 AHA/ACC ACS Guideline",
        section_path=["Cardiology", "DAPT"],
        locator="data/sources/guidelines/aha_acc_acs_2023.md#antiplatelet",
        version="2023.1",
        published_or_updated_date="2023-11-01",
        evidence_level="guideline_class_1",
        licence="CC-BY-4.0",
        text="All patients with acute coronary syndrome without contraindications should receive chewable non-enteric-coated aspirin (162 to 325 mg) immediately upon presentation.",
    )

    # DailyMed label doc (Aspirin)
    doc_dm1 = SourceDocument(
        source_id="dailymed",
        doc_id="SPL-ASPIRIN-001",
        title="Aspirin Delayed Release Tablets",
        section_path=["SPL", "Indications and Usage"],
        locator="tests/fixtures/rag_sources/dailymed_aspirin.xml#INDICATIONS",
        version="4.0",
        published_or_updated_date="2023-08-15",
        evidence_level="fda_label",
        licence="US Government Work",
        text="Aspirin is indicated to reduce the risk of death and myocardial infarction in patients with acute coronary syndromes (unstable angina, non-ST elevation myocardial infarction, and ST elevation myocardial infarction) and suspected acute coronary syndromes.",
    )

    doc_dm2 = SourceDocument(
        source_id="dailymed",
        doc_id="SPL-ASPIRIN-001",
        title="Aspirin Delayed Release Tablets",
        section_path=["SPL", "Contraindications"],
        locator="tests/fixtures/rag_sources/dailymed_aspirin.xml#CONTRAINDICATIONS",
        version="4.0",
        published_or_updated_date="2023-08-15",
        evidence_level="fda_label",
        licence="US Government Work",
        text="Aspirin is contraindicated in patients with known hypersensitivity to nonsteroidal anti-inflammatory drugs (NSAIDs), active pathological bleeding, severe thrombocytopenia, or hemorrhagic diathesis.",
    )

    # PubMed doc (Trial)
    doc_pm = SourceDocument(
        source_id="pubmed",
        doc_id="PMID-34567890",
        title="Dual Antiplatelet Therapy Duration in ACS",
        section_path=["Abstract", "Conclusions"],
        locator="tests/fixtures/rag_sources/pubmed_sample.xml#conclusions",
        version="1.0",
        published_or_updated_date="2022-06-15",
        evidence_level="1b",
        licence="NLM Public Domain",
        text="Shortened 3-month DAPT followed by P2Y12 monotherapy reduced major bleeding without increasing ischemic events in stabilized ACS patients.",
    )

    chunks = chunker.chunk_documents([doc_gl, doc_dm1, doc_dm2, doc_pm])
    embedder = get_embedding_model("general")

    index = VersionedHybridIndex(index_id="test_retrieval_idx", storage_dir=tmp_path)
    index.build(chunks=chunks, embedding_model=embedder, index_version="v1.0")
    return index


@pytest.fixture
def retrieval_service(populated_index):
    return UnifiedRetrievalService(index=populated_index)


@pytest.mark.unit
def test_rrf_fusion_logic(retrieval_service):
    """Verify dense and BM25 search are fused via Reciprocal Rank Fusion (RRF)."""
    items = retrieval_service.retrieve(
        query="acute coronary syndrome aspirin indication",
        k=4,
    )
    assert len(items) > 0
    top_item = items[0]
    assert isinstance(top_item, EvidenceItem)
    assert "rrf" in top_item.scores
    assert "dense" in top_item.scores
    assert "bm25" in top_item.scores
    assert top_item.scores["rrf"] > 0.0


@pytest.mark.unit
def test_source_diversity_cap(retrieval_service):
    """Verify that no single source exceeds the configured maximum diversity share."""
    # We have 2 dailymed chunks, 1 guideline, 1 pubmed
    # When k=4 and max_source_share=0.5, dailymed can occupy at most ceil(4 * 0.5) = 2 items
    items = retrieval_service.retrieve(
        query="aspirin acute coronary syndrome",
        k=4,
        max_source_share=0.5,
    )
    sources = [it.source for it in items]
    dailymed_count = sources.count("dailymed")
    assert dailymed_count <= 2, f"DailyMed count {dailymed_count} exceeded diversity cap of 2"


@pytest.mark.unit
def test_superseded_exclusion_by_default(populated_index, tmp_path):
    """Verify superseded documents are excluded by default and only returned when requested."""
    chunker = StructureAwareChunker(config=ChunkerConfig(target_chunk_tokens=50, max_chunk_tokens=100))

    # Update DOC-ACS-001 with v2.0
    updated_doc = SourceDocument(
        source_id="guidelines",
        doc_id="DOC-ACS-001",
        title="2024 AHA/ACC ACS Guideline (Updated)",
        section_path=["Cardiology", "DAPT"],
        locator="data/sources/guidelines/aha_acc_acs_2023.md#antiplatelet",
        version="2024.1",
        published_or_updated_date="2024-06-01",
        evidence_level="guideline_class_1",
        licence="CC-BY-4.0",
        text="Aspirin monotherapy is recommended following 1 month of DAPT in select ACS patients.",
    )
    new_chunks = chunker.chunk_documents([updated_doc])
    populated_index.incremental_update(new_chunks, new_index_version="v2.0")

    service = UnifiedRetrievalService(index=populated_index)

    # Standard retrieve: old v1 chunk must NOT appear
    default_items = service.retrieve("aspirin immediately", k=5, include_superseded=False)
    for it in default_items:
        assert it.metadata.get("superseded_by") is None

    # Retrieve with include_superseded=True: old chunk appears
    all_items = service.retrieve("aspirin immediately", k=10, include_superseded=True)
    superseded_found = any(it.metadata.get("superseded_by") == "v2.0" for it in all_items)
    assert superseded_found is True


@pytest.mark.unit
def test_filters_source_date_and_evidence_level(retrieval_service):
    """Verify filtering by source, publication date range, and evidence hierarchy level."""
    # 1. Filter by source
    gl_items = retrieval_service.retrieve(
        query="aspirin",
        filters=RetrievalFilters(sources=["guidelines"]),
        k=5,
    )
    for it in gl_items:
        assert it.source == "guidelines"

    # 2. Filter by evidence level
    trial_items = retrieval_service.retrieve(
        query="aspirin",
        filters=RetrievalFilters(evidence_levels=["1b"]),
        k=5,
    )
    for it in trial_items:
        assert it.metadata["evidence_level"] == "1b"

    # 3. Filter by date range (only 2022 documents)
    date_items = retrieval_service.retrieve(
        query="aspirin",
        filters=RetrievalFilters(min_date="2022-01-01", max_date="2022-12-31"),
        k=5,
    )
    for it in date_items:
        assert it.metadata["published_or_updated_date"].startswith("2022")


@pytest.mark.unit
def test_every_evidence_item_resolves_through_locator_to_source_text(retrieval_service):
    """Verify that every returned EvidenceItem resolves through its locator directly to source text."""
    items = retrieval_service.retrieve(
        query="acute coronary syndrome aspirin",
        k=4,
    )
    assert len(items) > 0
    for it in items:
        resolved_text = resolve_locator(it.locator)
        assert len(resolved_text) > 0, f"Failed to resolve locator: {it.locator}"
        # The chunk text should be present in the resolved document or section
        assert it.text in resolved_text or resolved_text in it.text, (
            f"Resolved text mismatch for locator {it.locator}"
        )


@pytest.mark.unit
def test_tracing_spans_recorded_per_stage(retrieval_service):
    """Verify that OpenTelemetry tracing spans are emitted for each retrieval pipeline stage."""
    clear_recorded_spans()
    _ = retrieval_service.retrieve("aspirin DAPT", k=3)

    spans = get_recorded_spans()
    span_names = [s.name for s in spans]

    assert any("rag.retrieve" in n for n in span_names)
    assert any("rag.dense_search" in n for n in span_names)
    assert any("rag.bm25_search" in n for n in span_names)
    assert any("rag.fusion_rrf" in n for n in span_names)
    assert any("rag.filter_and_diversity" in n for n in span_names)


@pytest.mark.unit
def test_api_contract_and_python_client(retrieval_service):
    """Verify FastAPI endpoint schema contract and RetrievalClient functionality."""
    from backend.main import app

    # Attach retrieval service to app state or module
    app.state.retrieval_service = retrieval_service

    client = TestClient(app)
    response = client.post(
        "/api/rag/retrieve",
        json={
            "query": "aspirin acute coronary syndrome",
            "k": 3,
            "max_source_share": 0.67,
            "filters": {
                "sources": ["guidelines", "dailymed"]
            }
        }
    )
    assert response.status_code == 200, f"API error: {response.text}"
    data = response.json()

    assert data["query"] == "aspirin acute coronary syndrome"
    assert data["index_version"] == "v1.0"
    assert "latency_ms" in data
    assert len(data["evidence"]) > 0

    first_item = data["evidence"][0]
    assert "evidence_id" in first_item
    assert "text" in first_item
    assert "source" in first_item
    assert "locator" in first_item
    assert "scores" in first_item

    # Verify python client in direct service mode
    py_client = RetrievalClient(service=retrieval_service)
    client_items = py_client.retrieve("aspirin", k=2)
    assert len(client_items) <= 2
    assert isinstance(client_items[0], EvidenceItem)
