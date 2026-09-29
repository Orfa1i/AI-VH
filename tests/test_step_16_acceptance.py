"""
Acceptance criteria tests for STEP 16 (P2.3):
Dense and keyword indexing with versioned indexes, complete manifests,
deterministic rebuilds, query index version tracking, and superseded marking.
"""

from pathlib import Path
import pytest
import numpy as np

from vh.rag.sources.base import SourceDocument
from vh.rag.chunking import ChunkerConfig, StructureAwareChunker
from vh.rag.indexing import (
    IndexManifest,
    EmbeddingModel,
    GeneralEmbeddingModel,
    BiomedicalEmbeddingModel,
    get_embedding_model,
    DenseVectorIndex,
    BM25Index,
    VersionedHybridIndex,
    QueryResult,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_chunks():
    chunker = StructureAwareChunker(config=ChunkerConfig(target_chunk_tokens=50, max_chunk_tokens=80))

    doc1 = SourceDocument(
        source_id="guidelines",
        doc_id="DOC-ACS-001",
        title="ACS Antiplatelet Guidelines",
        section_path=["Cardiology", "DAPT"],
        locator="guidelines/acs.md#dapt",
        version="1.0",
        published_or_updated_date="2023-11-01",
        evidence_level="guideline_class_1",
        licence="CC-BY-4.0",
        text="Chewable aspirin 162 to 325 mg should be administered immediately upon acute presentation. Dual antiplatelet therapy with ticagrelor or prasugrel is recommended for patients undergoing percutaneous coronary intervention.",
    )

    doc2 = SourceDocument(
        source_id="guidelines",
        doc_id="DOC-CAP-002",
        title="CAP Empiric Antimicrobial Therapy",
        section_path=["Pulmonology", "Inpatient"],
        locator="guidelines/cap.md#inpatient",
        version="1.0",
        published_or_updated_date="2019-10-01",
        evidence_level="guideline_class_1",
        licence="Open Access",
        text="In hospitalized adults with non-severe community-acquired pneumonia, combination therapy with ceftriaxone 1 to 2g daily plus azithromycin 500mg daily is recommended.",
    )

    doc3 = SourceDocument(
        source_id="dailymed",
        doc_id="SPL-METFORMIN-003",
        title="Metformin Hydrochloride Label",
        section_path=["SPL", "Boxed Warning"],
        locator="dailymed/metformin.xml#boxed",
        version="4.0",
        published_or_updated_date="2023-09-01",
        evidence_level="fda_label",
        licence="US Government Work",
        text="WARNING: LACTIC ACIDOSIS. Postmarketing cases of metformin-associated lactic acidosis have resulted in death, hypothermia, and cardiovascular collapse.",
    )

    return chunker.chunk_documents([doc1, doc2, doc3])


@pytest.mark.unit
def test_two_embedding_candidates_configured():
    """Verify general-purpose and biomedical embedding candidates are properly configured."""
    general_model = get_embedding_model("general")
    assert general_model.model_id == "sentence-transformers/all-MiniLM-L6-v2"
    assert general_model.dimension == 384

    biomedical_model = get_embedding_model("biomedical")
    assert "biomed" in biomedical_model.model_id.lower() or "pubmed" in biomedical_model.model_id.lower()
    assert biomedical_model.dimension in {384, 768}

    # Verify basic vector output shape
    vecs = general_model.embed_texts(["Aspirin 81mg oral daily."])
    assert isinstance(vecs, np.ndarray)
    assert vecs.shape == (1, 384)


@pytest.mark.unit
def test_index_manifest_completeness_and_match(sample_chunks, tmp_path):
    """Verify manifest is complete and exactly matches index contents and source document versions."""
    embedder = get_embedding_model("general")
    index = VersionedHybridIndex(index_id="test_idx", storage_dir=tmp_path)
    index.build(chunks=sample_chunks, embedding_model=embedder, index_version="v1.0")

    manifest = index.manifest
    assert manifest is not None
    assert manifest.index_id == "test_idx"
    assert manifest.index_version == "v1.0"
    assert manifest.embedding_model == embedder.model_id
    assert manifest.embedding_dimension == embedder.dimension
    assert manifest.chunker_version == "1.0.0"
    assert manifest.total_chunks == len(sample_chunks)
    assert manifest.active_chunks == len(sample_chunks)
    assert manifest.superseded_chunks == 0
    assert len(manifest.manifest_hash) > 10

    # Source document versions match
    assert manifest.source_document_versions.get("DOC-ACS-001") == "1.0"
    assert manifest.source_document_versions.get("DOC-CAP-002") == "1.0"
    assert manifest.source_document_versions.get("SPL-METFORMIN-003") == "4.0"


@pytest.mark.unit
def test_full_rebuild_deterministic_ids_and_counts(sample_chunks, tmp_path):
    """Verify a full rebuild from identical inputs produces identical chunk IDs, counts, and manifest hashes."""
    embedder = get_embedding_model("general")

    idx1 = VersionedHybridIndex(index_id="rebuild_idx_1", storage_dir=tmp_path / "run1")
    idx1.build(chunks=sample_chunks, embedding_model=embedder, index_version="v1.0")

    idx2 = VersionedHybridIndex(index_id="rebuild_idx_2", storage_dir=tmp_path / "run2")
    idx2.build(chunks=sample_chunks, embedding_model=embedder, index_version="v1.0")

    assert idx1.manifest.total_chunks == idx2.manifest.total_chunks
    assert idx1.get_chunk_ids() == idx2.get_chunk_ids()
    assert np.allclose(idx1.dense_index.embeddings, idx2.dense_index.embeddings, atol=1e-5)


@pytest.mark.unit
def test_query_output_records_index_version(sample_chunks, tmp_path):
    """Verify query results explicitly record the index version utilized for retrieval."""
    embedder = get_embedding_model("general")
    index = VersionedHybridIndex(index_id="query_idx", storage_dir=tmp_path)
    index.build(chunks=sample_chunks, embedding_model=embedder, index_version="v1.2.0")

    query_res: QueryResult = index.search(
        query="acute coronary syndrome dual antiplatelet aspirin",
        top_k=3,
        mode="hybrid",
    )

    assert isinstance(query_res, QueryResult)
    assert query_res.index_version == "v1.2.0"
    assert query_res.retrieval_mode == "hybrid"
    assert len(query_res.results) > 0

    top_result = query_res.results[0]
    assert "aspirin" in top_result.chunk.text.lower() or "antiplatelet" in top_result.chunk.text.lower()
    assert top_result.score > 0.0


@pytest.mark.unit
def test_incremental_updates_and_superseded_marking(sample_chunks, tmp_path):
    """Verify incremental updates re-index changed documents and mark old chunks as superseded_by."""
    embedder = get_embedding_model("general")
    index = VersionedHybridIndex(index_id="update_idx", storage_dir=tmp_path)
    index.build(chunks=sample_chunks, embedding_model=embedder, index_version="v1.0")

    assert index.manifest.active_chunks == len(sample_chunks)
    assert index.manifest.superseded_chunks == 0

    # Create updated version (v2.0) of DOC-ACS-001 with new text
    chunker = StructureAwareChunker(config=ChunkerConfig(target_chunk_tokens=50, max_chunk_tokens=80))
    updated_doc = SourceDocument(
        source_id="guidelines",
        doc_id="DOC-ACS-001",
        title="ACS Antiplatelet Guidelines (Revised)",
        section_path=["Cardiology", "DAPT"],
        locator="guidelines/acs.md#dapt",
        version="2.0",
        published_or_updated_date="2024-06-01",
        evidence_level="guideline_class_1",
        licence="CC-BY-4.0",
        text="Aspirin monotherapy is sufficient after 1 month of DAPT in low-risk PCI patients.",
    )
    new_chunks = chunker.chunk_documents([updated_doc])

    # Run incremental update
    index.incremental_update(
        new_or_updated_chunks=new_chunks,
        new_index_version="v2.0",
    )

    # Check updated manifest counts
    assert index.manifest.index_version == "v2.0"
    assert index.manifest.superseded_chunks >= 1
    assert index.manifest.source_document_versions.get("DOC-ACS-001") == "2.0"

    # Verify superseded chunks have superseded_by set and is_active is False
    old_acs_chunks = [c for c in index.get_all_records() if c["doc_id"] == "DOC-ACS-001" and c["is_active"] is False]
    assert len(old_acs_chunks) >= 1
    for oc in old_acs_chunks:
        assert oc["superseded_by"] == "v2.0"

    # Default search only returns active v2 chunks
    active_search = index.search("aspirin monotherapy 1 month", top_k=5, include_superseded=False)
    for res in active_search.results:
        assert res.chunk.parent_metadata.get("superseded_by") is None

    # Search with include_superseded=True returns superseded chunks with flag
    superseded_search = index.search("aspirin", top_k=10, include_superseded=True)
    superseded_found = any(res.chunk.parent_metadata.get("superseded_by") == "v2.0" for res in superseded_search.results)
    assert superseded_found is True
