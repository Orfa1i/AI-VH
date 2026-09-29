"""
DailyMed Structured Product Labeling (SPL) source adapter.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from vh.rag.sources.base import (
    SourceAdapter,
    SourceDocument,
    assert_licence_permitted,
)

LOINC_SECTION_NAMES: Dict[str, str] = {
    "34066-1": "Boxed Warning",
    "34067-9": "Indications and Usage",
    "34068-7": "Dosage and Administration",
    "34070-3": "Contraindications",
    "43685-7": "Warnings and Precautions",
    "34084-4": "Adverse Reactions",
    "34073-7": "Drug Interactions",
    "34076-0": "Use in Specific Populations",
    "34090-1": "Clinical Pharmacology",
    "34089-3": "Description",
    "34069-5": "How Supplied/Storage and Handling",
    "42229-5": "Spl Unclassified Section",
}


class DailyMedAdapter(SourceAdapter):
    """
    Adapter for DailyMed FDA Structured Product Labeling (SPL) XML drug labels.
    """
    source_id = "dailymed"

    def __init__(self, default_licence: str = "US Government Work"):
        self.default_licence = default_licence

    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """
        Parse SPL XML into section-aware SourceDocuments.
        """
        if isinstance(raw_content, bytes):
            text_content = raw_content.decode("utf-8", errors="replace")
        elif isinstance(raw_content, str):
            text_content = raw_content
        else:
            raise ValueError(f"DailyMedAdapter expects str or bytes, got {type(raw_content)}")

        # Strip default XML namespace for straightforward element navigation
        clean_xml = self._strip_namespaces(text_content)
        root = ET.fromstring(clean_xml)

        documents: List[SourceDocument] = []

        # Document identifiers
        set_id_el = root.find(".//setId")
        set_id = set_id_el.attrib.get("root", "unknown_setid") if set_id_el is not None else "unknown_setid"

        title_el = root.find(".//title")
        doc_title = "".join(title_el.itertext()).strip() if title_el is not None else "DailyMed Drug Label"

        ver_el = root.find(".//versionNumber")
        version = ver_el.attrib.get("value", "1.0") if ver_el is not None else "1.0"

        date_el = root.find(".//effectiveTime")
        raw_date = date_el.attrib.get("value", "20240101") if date_el is not None else "20240101"
        date_str = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) >= 8 else "2024-01-01"

        licence = kwargs.get("licence", self.default_licence)
        assert_licence_permitted(licence, doc_id=f"DailyMed:{set_id}")

        # Iterate sections in structuredBody
        sections = root.findall(".//structuredBody//section")
        for sec in sections:
            code_el = sec.find("./code")
            loinc_code = code_el.attrib.get("code", "") if code_el is not None else ""
            loinc_name = LOINC_SECTION_NAMES.get(loinc_code, "")

            title_node = sec.find("./title")
            sec_title = "".join(title_node.itertext()).strip() if title_node is not None else ""

            if not sec_title and not loinc_name:
                continue

            if loinc_name:
                if sec_title and loinc_name.lower() not in sec_title.lower():
                    display_section = f"{loinc_name}: {sec_title}"
                else:
                    display_section = sec_title or loinc_name
            else:
                display_section = sec_title

            # Extract paragraphs and list items
            text_parts: List[str] = []
            for p in sec.findall(".//paragraph"):
                ptxt = "".join(p.itertext()).strip()
                if ptxt:
                    text_parts.append(ptxt)

            for item in sec.findall(".//item"):
                itxt = "".join(item.itertext()).strip()
                if itxt:
                    text_parts.append(f"- {itxt}")

            if not text_parts:
                # Direct text node inside text
                text_el = sec.find("./text")
                if text_el is not None:
                    raw_sec_text = "".join(text_el.itertext()).strip()
                    if raw_sec_text:
                        text_parts.append(raw_sec_text)

            if not text_parts:
                continue

            sec_id = sec.attrib.get("ID", loinc_code or "sec")
            locator = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}#{sec_id}"

            doc = SourceDocument(
                source_id=self.source_id,
                doc_id=set_id,
                title=doc_title,
                section_path=["SPL", display_section],
                locator=locator,
                version=version,
                published_or_updated_date=date_str,
                evidence_level="fda_label",
                licence=licence,
                text="\n\n".join(text_parts),
                metadata={
                    "set_id": set_id,
                    "loinc_code": loinc_code,
                    "section_id": sec_id,
                },
            )
            documents.append(doc)

        return documents

    def _strip_namespaces(self, xml_string: str) -> str:
        # Regex to strip xmlns declarations
        import re
        return re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', xml_string)
