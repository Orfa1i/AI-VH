"""
Acceptance criteria tests for STEP 14 (P2.1):
Source adapters, SourceDocument normalization, licence enforcement,
RxNorm terminology service, and NABD drug search regression.
"""

import json
from pathlib import Path
import pytest

from vh.rag.sources.base import (
    SourceDocument,
    LicenceEnforcementError,
    is_licence_permitted,
    RateLimiter,
    RetryHandler,
)
from vh.rag.sources.pubmed import PubMedAdapter
from vh.rag.sources.pmc import PMCAdapter
from vh.rag.sources.dailymed import DailyMedAdapter
from vh.rag.sources.openfda import OpenFDAAdapter
from vh.rag.sources.guidelines import LocalGuidelinesAdapter
from vh.rag.sources.rxnorm import RxNormService
from vh.rag.sources.nabd import NABDService, nabd_drug_search

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "rag_sources"
GUIDELINES_DIR = REPO_ROOT / "data" / "sources" / "guidelines"


@pytest.mark.unit
def test_source_document_validation():
    """Verify SourceDocument schema fields, validation, and serialization."""
    doc = SourceDocument(
        source_id="pubmed",
        doc_id="34567890",
        title="Dual Antiplatelet Therapy Duration in Patients with Acute Coronary Syndrome",
        section_path=["Abstract", "Conclusions"],
        locator="https://pubmed.ncbi.nlm.nih.gov/34567890/#conclusions",
        version="1",
        published_or_updated_date="2023-06-15",
        evidence_level="systematic_review",
        licence="Public Domain",
        text="Shortened 3-month DAPT followed by P2Y12 monotherapy reduced major bleeding.",
    )
    assert doc.source_id == "pubmed"
    assert doc.doc_id == "34567890"
    assert doc.section_path == ["Abstract", "Conclusions"]
    assert doc.evidence_level == "systematic_review"
    assert doc.licence == "Public Domain"

    # Missing required field raises validation error
    with pytest.raises(Exception):
        SourceDocument(  # type: ignore
            source_id="pubmed",
            doc_id="123",
            title="Incomplete Doc",
            # missing text, licence, locator, etc.
        )


@pytest.mark.unit
def test_licence_enforcement_policy():
    """Verify that permitted licences pass and unpermitted/unknown licences are rejected."""
    permitted_examples = [
        "CC0",
        "CC-BY",
        "CC-BY-4.0",
        "CC-BY-3.0",
        "CC-BY-SA",
        "Open Access",
        "US Government Work",
        "Public Domain",
        "FDA Public Domain",
    ]
    for lic in permitted_examples:
        assert is_licence_permitted(lic) is True, f"Licence {lic} should be permitted"

    unpermitted_examples = [
        None,
        "",
        "Unknown",
        "All Rights Reserved",
        "Proprietary Commercial Licence",
        "Copyright 2024 Private Corp",
    ]
    for lic in unpermitted_examples:
        assert is_licence_permitted(lic) is False, f"Licence {lic} should not be permitted"


@pytest.mark.unit
def test_pubmed_adapter_fixture_parsing():
    """Verify PubMedAdapter parses recorded XML fixtures to validated SourceDocuments."""
    xml_path = FIXTURES_DIR / "pubmed_sample.xml"
    assert xml_path.exists(), "PubMed fixture must exist"
    xml_content = xml_path.read_text(encoding="utf-8")

    adapter = PubMedAdapter()
    docs = adapter.parse(xml_content)

    assert len(docs) >= 2, "Expected at least 2 PubMed documents or sections parsed"
    # Check first article (PMID 34567890 with structured abstract)
    pmid_34_docs = [d for d in docs if d.doc_id == "34567890"]
    assert len(pmid_34_docs) >= 1
    sample_doc = pmid_34_docs[0]
    assert sample_doc.source_id == "pubmed"
    assert "Dual Antiplatelet Therapy" in sample_doc.title
    assert sample_doc.published_or_updated_date.startswith("2023")
    assert is_licence_permitted(sample_doc.licence)
    assert len(sample_doc.text) > 20


@pytest.mark.unit
def test_pmc_adapter_fixture_and_licence_enforcement():
    """Verify PMCAdapter extracts full text hierarchy and enforces article-level licence."""
    pmc_valid_path = FIXTURES_DIR / "pmc_sample.xml"
    pmc_restricted_path = FIXTURES_DIR / "pmc_restricted.xml"

    adapter = PMCAdapter()
    valid_xml = pmc_valid_path.read_text(encoding="utf-8")
    docs = adapter.parse(valid_xml)

    assert len(docs) >= 4, "Expected multiple structured sections from PMC article"
    for d in docs:
        assert d.source_id == "pmc"
        assert d.doc_id == "PMC8812345"
        assert "Fluid Resuscitation" in d.title
        assert "CC-BY" in d.licence
        assert len(d.section_path) >= 1
        assert len(d.text) > 0

    # Ensure sections contain Introduction, Methods, Results, Discussion
    all_sections = [d.section_path[-1] for d in docs]
    assert "Introduction" in all_sections
    assert "Results" in all_sections

    # Now verify restricted licence article is rejected
    restricted_xml = pmc_restricted_path.read_text(encoding="utf-8")
    with pytest.raises(LicenceEnforcementError):
        adapter.parse(restricted_xml)


@pytest.mark.unit
def test_dailymed_adapter_spl_sections():
    """Verify DailyMedAdapter extracts section-aware SPL documents."""
    spl_path = FIXTURES_DIR / "dailymed_aspirin.xml"
    spl_content = spl_path.read_text(encoding="utf-8")

    adapter = DailyMedAdapter()
    docs = adapter.parse(spl_content)

    assert len(docs) >= 4, "Expected multiple LOINC-coded SPL sections"
    section_names = [d.section_path[-1] for d in docs]

    assert any("BOXED WARNING" in s.upper() for s in section_names)
    assert any("INDICATIONS" in s.upper() for s in section_names)
    assert any("CONTRAINDICATIONS" in s.upper() for s in section_names)
    assert any("INTERACTIONS" in s.upper() for s in section_names)

    boxed_doc = next(d for d in docs if "BOXED WARNING" in d.section_path[-1].upper())
    assert "Reye syndrome" in boxed_doc.text
    assert boxed_doc.evidence_level == "fda_label"
    assert is_licence_permitted(boxed_doc.licence)


@pytest.mark.unit
def test_openfda_adapter_label_sections():
    """Verify OpenFDAAdapter extracts structured drug label sections."""
    json_path = FIXTURES_DIR / "openfda_metformin.json"
    json_content = json_path.read_text(encoding="utf-8")

    adapter = OpenFDAAdapter()
    docs = adapter.parse(json_content)

    assert len(docs) >= 3, "Expected openFDA sections for metformin"
    for d in docs:
        assert d.source_id == "openfda"
        assert is_licence_permitted(d.licence)
        assert d.evidence_level == "fda_label"

    # Find boxed warning section
    boxed = next(d for d in docs if "BOXED_WARNING" in d.section_path[-1].upper() or "BOXED WARNING" in d.section_path[-1].upper())
    assert "LACTIC ACIDOSIS" in boxed.text


@pytest.mark.unit
def test_local_guidelines_adapter_with_sidecar():
    """Verify LocalGuidelinesAdapter parses local guidelines with sidecars and rejects unpermitted licences."""
    adapter = LocalGuidelinesAdapter(guidelines_dir=GUIDELINES_DIR)
    docs = adapter.load_all()

    assert len(docs) >= 3, "Should have loaded at least 3 permitted guidelines"
    titles = [d.title for d in docs]
    assert any("Acute Coronary Syndromes" in t for t in titles)
    assert any("Community-Acquired Pneumonia" in t for t in titles)
    assert any("Diabetic Ketoacidosis" in t for t in titles)

    # Verify that restricted_test_guideline was rejected and omitted
    assert not any("Proprietary Corporate Treatment Recommendation" in t for t in titles)

    # Verify direct load of restricted guideline raises LicenceEnforcementError
    restricted_file = GUIDELINES_DIR / "restricted_test_guideline.md"
    with pytest.raises(LicenceEnforcementError):
        adapter.load_file(restricted_file)


@pytest.mark.unit
def test_rxnorm_service_terminology_only():
    """Verify RxNorm is exposed as a normalisation/lookup service and NOT chunked text."""
    fixtures_path = FIXTURES_DIR / "rxnorm_fixtures.json"
    service = RxNormService(fixture_file=fixtures_path)

    # Name normalization and RxCUI resolution
    cui_aspirin = service.lookup_rxcui("Aspirin")
    assert cui_aspirin == "1191"

    cui_metformin = service.lookup_rxcui("Glucophage")
    assert cui_metformin == "6809"

    cui_lisinopril = service.lookup_rxcui("Prinivil")
    assert cui_lisinopril == "29046"

    # Active ingredients
    ingredients = service.get_ingredients("1191")
    assert "Aspirin" in ingredients

    # Drug classes
    classes = service.get_drug_classes("1191")
    assert "Antiplatelet Agents" in classes

    # Drug interaction risk check
    interaction = service.check_interaction_risk("1191", "5640")  # Aspirin + Ibuprofen
    assert interaction is not None
    assert interaction["severity"] == "High"
    assert "COX-1" in interaction["description"]


@pytest.mark.unit
def test_nabd_drug_search_regression():
    """Verify NABD drug search regression integrating RxNorm, label warnings, and literature."""
    fixtures_path = FIXTURES_DIR / "rxnorm_fixtures.json"
    rx_service = RxNormService(fixture_file=fixtures_path)
    nabd = NABDService(rxnorm_service=rx_service)

    # Pre-populate sample adapter docs for NABD search
    spl_content = (FIXTURES_DIR / "dailymed_aspirin.xml").read_text(encoding="utf-8")
    openfda_content = (FIXTURES_DIR / "openfda_metformin.json").read_text(encoding="utf-8")
    pubmed_content = (FIXTURES_DIR / "pubmed_sample.xml").read_text(encoding="utf-8")

    nabd.index_documents(DailyMedAdapter().parse(spl_content))
    nabd.index_documents(OpenFDAAdapter().parse(openfda_content))
    nabd.index_documents(PubMedAdapter().parse(pubmed_content))

    # Search for Aspirin
    profile = nabd.search_drug("Aspirin")
    assert profile.drug_name.lower() == "aspirin"
    assert profile.rxcui == "1191"
    assert "Antiplatelet Agents" in profile.drug_classes
    assert len(profile.contraindications) >= 1
    assert any("hypersensitivity" in c.lower() or "bleeding" in c.lower() for c in profile.contraindications)
    assert len(profile.boxed_warnings) >= 1
    assert any("reye syndrome" in bw.lower() for bw in profile.boxed_warnings)
    assert len(profile.citations) >= 1
    assert any("Dual Antiplatelet Therapy" in c.title for c in profile.citations)

    # Also test convenience helper nabd_drug_search
    profile2 = nabd_drug_search("Metformin", nabd_service=nabd)
    assert profile2.rxcui == "6809"
    assert any("lactic acidosis" in bw.lower() for bw in profile2.boxed_warnings)


@pytest.mark.unit
def test_offline_network_guard_blocks_live_network():
    """Verify that any live network request is intercepted and forbidden during test execution."""
    import socket
    import urllib.request

    # Direct socket connect to external IP should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_sock:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53))
        s.close()
    assert "Live network call blocked" in str(exc_sock.value)

    # Urllib request to external domain should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_url:
        urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov", timeout=1)
    assert "Live network call blocked" in str(exc_url.value)


@pytest.mark.unit
def test_rate_limiter_and_retry_handler():
    """Verify rate limiter token-bucket throttling and retry handler with backoff."""
    limiter = RateLimiter(requests_per_second=10)
    # 5 quick acquires should be permitted immediately under burst limit
    for _ in range(5):
        assert limiter.acquire(timeout=1.0) is True

    # Retry handler with exponential backoff on retryable exceptions
    attempts = 0

    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Simulated transient connection failure")
        return "success"

    retry = RetryHandler(max_retries=3, backoff_base=0.01)
    result = retry.execute(flaky_func)
    assert result == "success"
    assert attempts == 3
