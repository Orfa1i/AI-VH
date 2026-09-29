"""
PubMed source adapter for parsing MEDLINE and PubMed XML abstract records.
"""

import xml.etree.ElementTree as ET
from typing import Any, List, Optional
from vh.rag.sources.base import (
    SourceAdapter,
    SourceDocument,
    assert_licence_permitted,
)


class PubMedAdapter(SourceAdapter):
    """
    Adapter for PubMed and MEDLINE abstract retrieval and parsing.
    """
    source_id = "pubmed"

    def __init__(self, default_licence: str = "NLM Public Domain"):
        self.default_licence = default_licence

    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """
        Parse PubMed XML string or bytes into a list of SourceDocument objects.
        """
        if isinstance(raw_content, bytes):
            text_content = raw_content.decode("utf-8", errors="replace")
        elif isinstance(raw_content, str):
            text_content = raw_content
        else:
            raise ValueError(f"PubMedAdapter expects str or bytes, got {type(raw_content)}")

        root = ET.fromstring(text_content)
        documents: List[SourceDocument] = []

        # Check for PubmedArticle elements
        articles = root.findall(".//PubmedArticle")
        if not articles and root.tag == "PubmedArticle":
            articles = [root]

        for article in articles:
            pmid_el = article.find(".//MedlineCitation/PMID")
            pmid = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else "unknown_pmid"

            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else "Untitled PubMed Article"

            # Parse date
            pub_date = self._extract_date(article)

            # Determine evidence level from publication types
            evidence_level = self._determine_evidence_level(article)

            # Licence validation
            licence = kwargs.get("licence", self.default_licence)
            assert_licence_permitted(licence, doc_id=f"PMID:{pmid}")

            # Abstract sections
            abstract_texts = article.findall(".//Abstract/AbstractText")
            if not abstract_texts:
                # If no abstract, capture title as minimal record
                continue

            has_labels = any("Label" in ab.attrib for ab in abstract_texts)

            if has_labels:
                for ab in abstract_texts:
                    label = ab.attrib.get("Label", "Summary").title()
                    sec_text = "".join(ab.itertext()).strip()
                    if not sec_text:
                        continue
                    doc = SourceDocument(
                        source_id=self.source_id,
                        doc_id=pmid,
                        title=title,
                        section_path=["Abstract", label],
                        locator=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/#{label.lower()}",
                        version="1.0",
                        published_or_updated_date=pub_date,
                        evidence_level=evidence_level,
                        licence=licence,
                        text=sec_text,
                        metadata={"pmid": pmid, "section_label": label},
                    )
                    documents.append(doc)
            else:
                full_abstract = " ".join("".join(ab.itertext()).strip() for ab in abstract_texts).strip()
                if full_abstract:
                    doc = SourceDocument(
                        source_id=self.source_id,
                        doc_id=pmid,
                        title=title,
                        section_path=["Abstract"],
                        locator=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        version="1.0",
                        published_or_updated_date=pub_date,
                        evidence_level=evidence_level,
                        licence=licence,
                        text=full_abstract,
                        metadata={"pmid": pmid},
                    )
                    documents.append(doc)

        return documents

    def _extract_date(self, article: ET.Element) -> str:
        # Check DateCompleted first
        dc = article.find(".//DateCompleted")
        if dc is not None:
            year = dc.findtext("Year") or "2024"
            month = dc.findtext("Month") or "01"
            day = dc.findtext("Day") or "01"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Check PubDate
        pd = article.find(".//JournalIssue/PubDate")
        if pd is not None:
            year = pd.findtext("Year") or "2024"
            month = pd.findtext("Month") or "01"
            day = pd.findtext("Day") or "01"
            # Handle month abbreviation if present
            month_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                         "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
            month_num = month_map.get(month, month.zfill(2))
            return f"{year}-{month_num}-{day.zfill(2)}"

        return "2024-01-01"

    def _determine_evidence_level(self, article: ET.Element) -> str:
        pub_types = [pt.text.strip().lower() for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
        if any("systematic review" in pt or "meta-analysis" in pt for pt in pub_types):
            return "1a"
        if any("randomized controlled trial" in pt for pt in pub_types):
            return "1b"
        if any("clinical trial" in pt for pt in pub_types):
            return "2b"
        if any("guideline" in pt or "practice guideline" in pt for pt in pub_types):
            return "guideline"
        return "peer_reviewed"
