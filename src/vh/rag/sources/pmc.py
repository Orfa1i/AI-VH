"""
PMC Open Access source adapter for parsing JATS XML full-text articles with licence checking.
"""

import xml.etree.ElementTree as ET
from typing import Any, List, Optional
from vh.rag.sources.base import (
    SourceAdapter,
    SourceDocument,
    assert_licence_permitted,
)


class PMCAdapter(SourceAdapter):
    """
    Adapter for PubMed Central (PMC) Open Access full-text article extraction.
    """
    source_id = "pmc"

    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """
        Parse PMC JATS XML into hierarchical section SourceDocuments.
        """
        if isinstance(raw_content, bytes):
            text_content = raw_content.decode("utf-8", errors="replace")
        elif isinstance(raw_content, str):
            text_content = raw_content
        else:
            raise ValueError(f"PMCAdapter expects str or bytes, got {type(raw_content)}")

        if "xlink:" in text_content and "xmlns:xlink" not in text_content:
            text_content = text_content.replace("<article", '<article xmlns:xlink="http://www.w3.org/1999/xlink"')

        root = ET.fromstring(text_content)
        documents: List[SourceDocument] = []

        # Find PMC ID and PMID
        pmc_id_el = root.find(".//article-id[@pub-id-type='pmc']")
        pmc_id = pmc_id_el.text.strip() if pmc_id_el is not None and pmc_id_el.text else "unknown_pmc"

        pmid_el = root.find(".//article-id[@pub-id-type='pmid']")
        pmid = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else ""

        # Title
        title_el = root.find(".//title-group/article-title")
        title = "".join(title_el.itertext()).strip() if title_el is not None else "Untitled PMC Article"

        # Date
        pub_date = self._extract_date(root)

        # Licence extraction
        licence = self._extract_licence(root)
        assert_licence_permitted(licence, doc_id=f"PMC:{pmc_id}")

        # Section extraction from body
        body = root.find(".//body")
        if body is not None:
            self._extract_sections_recursive(
                body,
                current_path=[],
                pmc_id=pmc_id,
                title=title,
                pub_date=pub_date,
                licence=licence,
                documents=documents,
            )

        return documents

    def _extract_licence(self, root: ET.Element) -> str:
        # Check permissions block
        lic_el = root.find(".//permissions/license")
        if lic_el is not None:
            # Check license-type attribute
            lic_type = lic_el.attrib.get("license-type", "")
            if lic_type and lic_type.lower() == "open-access":
                # Check for specific text like CC-BY in license-p
                lic_p = lic_el.find(".//license-p")
                p_text = "".join(lic_p.itertext()) if lic_p is not None else ""
                if "CC-BY 4.0" in p_text or "Attribution 4.0" in p_text:
                    return "CC-BY-4.0"
                if "CC-BY" in p_text:
                    return "CC-BY"
                if "CC0" in p_text:
                    return "CC0"
                return "Open Access"
            if lic_type:
                return lic_type

        # Check copyright statement
        cr_el = root.find(".//permissions/copyright-statement")
        if cr_el is not None and cr_el.text:
            text = cr_el.text.strip()
            if "All Rights Reserved" in text or "all rights reserved" in text:
                return "All Rights Reserved"
            return text

        return "Unknown"

    def _extract_date(self, root: ET.Element) -> str:
        pub_date = root.find(".//pub-date")
        if pub_date is not None:
            year = pub_date.findtext("year") or "2024"
            month = pub_date.findtext("month") or "01"
            day = pub_date.findtext("day") or "01"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return "2024-01-01"

    def _extract_sections_recursive(
        self,
        element: ET.Element,
        current_path: List[str],
        pmc_id: str,
        title: str,
        pub_date: str,
        licence: str,
        documents: List[SourceDocument],
    ) -> None:
        secs = element.findall("./sec")
        if not secs:
            # Leaf element, extract paragraphs
            paragraphs = ["".join(p.itertext()).strip() for p in element.findall("./p")]
            valid_p = [p for p in paragraphs if p]
            if valid_p and current_path:
                text = "\n\n".join(valid_p)
                sec_id = element.attrib.get("id", "")
                locator = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/#{sec_id}" if sec_id else f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
                doc = SourceDocument(
                    source_id=self.source_id,
                    doc_id=pmc_id,
                    title=title,
                    section_path=list(current_path),
                    locator=locator,
                    version="1.0",
                    published_or_updated_date=pub_date,
                    evidence_level="peer_reviewed",
                    licence=licence,
                    text=text,
                    metadata={"pmc_id": pmc_id, "section_id": sec_id},
                )
                documents.append(doc)
            return

        for sec in secs:
            title_el = sec.find("./title")
            sec_title = "".join(title_el.itertext()).strip() if title_el is not None else "Section"
            new_path = current_path + [sec_title]

            # Collect immediate paragraphs in this section
            immediate_p = ["".join(p.itertext()).strip() for p in sec.findall("./p")]
            valid_p = [p for p in immediate_p if p]
            if valid_p:
                sec_id = sec.attrib.get("id", "")
                locator = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/#{sec_id}" if sec_id else f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
                doc = SourceDocument(
                    source_id=self.source_id,
                    doc_id=pmc_id,
                    title=title,
                    section_path=new_path,
                    locator=locator,
                    version="1.0",
                    published_or_updated_date=pub_date,
                    evidence_level="peer_reviewed",
                    licence=licence,
                    text="\n\n".join(valid_p),
                    metadata={"pmc_id": pmc_id, "section_id": sec_id},
                )
                documents.append(doc)

            # Recurse into child sections
            child_secs = sec.findall("./sec")
            if child_secs:
                self._extract_sections_recursive(
                    sec,
                    current_path=new_path,
                    pmc_id=pmc_id,
                    title=title,
                    pub_date=pub_date,
                    licence=licence,
                    documents=documents,
                )
