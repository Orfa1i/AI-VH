"""
Acceptance criteria tests for STEP 15 (P2.2):
Structure-aware chunking, section boundary isolation, offset property verification,
bounded table handling, and deterministic chunk ID hashing.
"""

from pathlib import Path
import pytest

from vh.rag.sources.base import SourceDocument
from vh.rag.sources.dailymed import DailyMedAdapter
from vh.rag.sources.guidelines import LocalGuidelinesAdapter
from vh.rag.sources.pmc import PMCAdapter
from vh.rag.sources.pubmed import PubMedAdapter
from vh.rag.chunking import (
    Chunk,
    ChunkerConfig,
    StructureAwareChunker,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "rag_sources"
GUIDELINES_DIR = REPO_ROOT / "data" / "sources" / "guidelines"


@pytest.fixture
def chunker() -> StructureAwareChunker:
    config = ChunkerConfig(
        target_chunk_tokens=100,
        max_chunk_tokens=150,
        overlap_tokens=20,
        chunker_version="1.0.0",
        preserve_tables=True,
    )
    return StructureAwareChunker(config=config)


@pytest.mark.unit
def test_no_chunk_crosses_section_boundary(chunker: StructureAwareChunker):
    """Verify that chunks never merge content across different document section paths."""
    guideline_adapter = LocalGuidelinesAdapter(guidelines_dir=GUIDELINES_DIR)
    guideline_path = GUIDELINES_DIR / "aha_acc_acs_2023.md"
    docs = guideline_adapter.load_file(guideline_path)

    # Chunk the multiple sections of the guideline
    all_chunks = chunker.chunk_documents(docs)

    assert len(all_chunks) >= len(docs), "Should produce at least one chunk per section"

    # Verify each chunk belongs strictly to one section
    for c in all_chunks:
        assert len(c.section_path) >= 1
        # Check that chunk text only exists within its declared parent doc
        parent_doc = next(d for d in docs if d.doc_id == c.parent_metadata["doc_id"] and d.section_path == c.section_path)
        assert c.text in parent_doc.text


@pytest.mark.unit
def test_property_chunk_text_equals_normalized_source_at_offsets(chunker: StructureAwareChunker):
    """Property test: chunk.text MUST exactly equal doc.text[start_char_offset:end_char_offset]."""
    dailymed_path = FIXTURES_DIR / "dailymed_aspirin.xml"
    dailymed_docs = DailyMedAdapter().parse(dailymed_path.read_text(encoding="utf-8"))

    pmc_path = FIXTURES_DIR / "pmc_sample.xml"
    pmc_docs = PMCAdapter().parse(pmc_path.read_text(encoding="utf-8"))

    pubmed_path = FIXTURES_DIR / "pubmed_sample.xml"
    pubmed_docs = PubMedAdapter().parse(pubmed_path.read_text(encoding="utf-8"))

    test_docs = dailymed_docs + pmc_docs + pubmed_docs

    for doc in test_docs:
        chunks = chunker.chunk_document(doc)
        for chunk in chunks:
            expected_slice = doc.text[chunk.start_char_offset:chunk.end_char_offset]
            assert chunk.text == expected_slice, (
                f"Offset mismatch for chunk {chunk.chunk_id}: "
                f"'{chunk.text[:40]}' != '{expected_slice[:40]}'"
            )


@pytest.mark.unit
def test_chunk_sizes_stay_within_bounds_and_tables_flagged(chunker: StructureAwareChunker):
    """Verify chunk sizes stay within configured bounds, and oversized atomic tables are kept intact and flagged."""
    # Create long text document
    long_paragraphs = [
        f"Paragraph {i}: Rapid clinical assessment of ST-elevation myocardial infarction requires immediate diagnostic electrocardiography within 10 minutes of initial patient presentation to the emergency department, followed by prompt initiation of primary percutaneous coronary intervention or fibrinolytic therapy when indicated."
        for i in range(10)
    ]
    long_doc = SourceDocument(
        source_id="test",
        doc_id="long-doc-1",
        title="Emergency Cardiac Protocols",
        section_path=["Emergency", "Protocols"],
        locator="https://hospital.local/protocols/1",
        version="1.0",
        published_or_updated_date="2024-01-01",
        evidence_level="guideline",
        licence="Public Domain",
        text="\n\n".join(long_paragraphs),
    )

    chunks = chunker.chunk_document(long_doc)
    assert len(chunks) > 1, "Long document should be split into multiple chunks"
    for c in chunks:
        assert c.token_count <= chunker.config.max_chunk_tokens, f"Chunk {c.chunk_id} exceeded max token bound"
        assert c.exceeds_bounds is False

    # Now create a document with an atomic markdown table that exceeds target bounds
    table_rows = ["| Drug | Dose | Route | Frequency | Indication | Elimination | Adverse Effects |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
    for i in range(25):
        table_rows.append(f"| Antibiotic_{i} | {100 + i * 50}mg | IV | q8h | Severe Nosocomial Infection | Renal clearance 80% | Nephrotoxicity, ototoxicity, electrolyte wasting, hypersensitivity rash |")
    table_text = "\n".join(table_rows)

    table_doc = SourceDocument(
        source_id="test",
        doc_id="table-doc-1",
        title="Antimicrobial Dosing Table",
        section_path=["Pharmacy", "Antimicrobial Formulary"],
        locator="https://hospital.local/formulary/antimicrobial",
        version="1.0",
        published_or_updated_date="2024-01-01",
        evidence_level="guideline",
        licence="Public Domain",
        text=table_text,
    )

    table_chunks = chunker.chunk_document(table_doc)
    assert len(table_chunks) >= 1
    # Check that the oversized table is flagged with exceeds_bounds=True while remaining intact
    oversized_chunk = next((c for c in table_chunks if c.exceeds_bounds), None)
    assert oversized_chunk is not None, "Oversized table should be flagged as exceeds_bounds"
    assert "| Antibiotic_0 |" in oversized_chunk.text
    assert oversized_chunk.parent_metadata["doc_id"] == "table-doc-1"


@pytest.mark.unit
def test_chunk_ids_are_deterministic(chunker: StructureAwareChunker):
    """Verify that identical inputs produce bit-for-bit identical chunk IDs, and alterations modify the ID."""
    doc = SourceDocument(
        source_id="guidelines",
        doc_id="GUIDELINE-DKA-2024",
        title="2024 ADA DKA Consensus",
        section_path=["Resuscitation", "Potassium"],
        locator="data/sources/guidelines/ada_dka_2024.md#potassium",
        version="2024.1",
        published_or_updated_date="2024-01-15",
        evidence_level="guideline_class_1",
        licence="CC-BY",
        text="Insulin therapy drives extracellular potassium into cells. Regular insulin must be held if serum potassium < 3.3 mEq/L.",
    )

    chunks_run1 = chunker.chunk_document(doc)
    chunks_run2 = chunker.chunk_document(doc)

    assert len(chunks_run1) == len(chunks_run2)
    for c1, c2 in zip(chunks_run1, chunks_run2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.start_char_offset == c2.start_char_offset
        assert c1.end_char_offset == c2.end_char_offset
        assert c1.text == c2.text
        assert c1.chunker_version == "1.0.0"

    # Changing version or locator changes the chunk_id
    doc_v2 = doc.model_copy(update={"version": "2024.2"})
    chunks_v2 = chunker.chunk_document(doc_v2)
    assert chunks_v2[0].chunk_id != chunks_run1[0].chunk_id


@pytest.mark.unit
def test_parent_metadata_and_chunker_version(chunker: StructureAwareChunker):
    """Verify chunk preserves all parent document metadata and records chunker version."""
    doc = SourceDocument(
        source_id="pubmed",
        doc_id="34567890",
        title="Dual Antiplatelet Therapy Duration in Patients with Acute Coronary Syndrome",
        section_path=["Abstract", "Conclusions"],
        locator="https://pubmed.ncbi.nlm.nih.gov/34567890/#conclusions",
        version="1.0",
        published_or_updated_date="2023-06-15",
        evidence_level="systematic_review",
        licence="Public Domain",
        text="Shortened 3-month DAPT followed by P2Y12 monotherapy reduced major bleeding.",
        metadata={"study_type": "RCT", "sample_size": 4000},
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.chunker_version == "1.0.0"
    assert c.parent_metadata["source_id"] == "pubmed"
    assert c.parent_metadata["doc_id"] == "34567890"
    assert c.parent_metadata["evidence_level"] == "systematic_review"
    assert c.parent_metadata["licence"] == "Public Domain"
    assert c.parent_metadata["custom_meta"]["study_type"] == "RCT"
