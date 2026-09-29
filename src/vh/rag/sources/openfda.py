"""
openFDA source adapter for drug label endpoints and regulatory safety data.
"""

import json
from typing import Any, Dict, List, Optional
from vh.rag.sources.base import (
    SourceAdapter,
    SourceDocument,
    assert_licence_permitted,
)

LABEL_SECTIONS = [
    ("boxed_warning", "Boxed Warning"),
    ("indications_and_usage", "Indications and Usage"),
    ("contraindications", "Contraindications"),
    ("warnings_and_cautions", "Warnings and Precautions"),
    ("warnings", "Warnings"),
    ("drug_interactions", "Drug Interactions"),
    ("adverse_reactions", "Adverse Reactions"),
    ("dosage_and_administration", "Dosage and Administration"),
    ("information_for_patients", "Patient Counseling Information"),
]


class OpenFDAAdapter(SourceAdapter):
    """
    Adapter for openFDA drug label JSON records.
    """
    source_id = "openfda"

    def __init__(self, default_licence: str = "CC0 / US Government Work"):
        self.default_licence = default_licence

    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """
        Parse openFDA JSON string, dict, or bytes into SourceDocuments.
        """
        if isinstance(raw_content, bytes):
            raw_content = raw_content.decode("utf-8", errors="replace")
        if isinstance(raw_content, str):
            data = json.loads(raw_content)
        elif isinstance(raw_content, dict):
            data = raw_content
        else:
            raise ValueError(f"OpenFDAAdapter expects str, bytes, or dict, got {type(raw_content)}")

        documents: List[SourceDocument] = []

        # Determine licence
        meta_licence = data.get("meta", {}).get("license", "")
        licence = self.default_licence if not meta_licence else meta_licence
        if kwargs.get("licence"):
            licence = kwargs["licence"]

        assert_licence_permitted(licence, doc_id="openfda-dataset")

        results = data.get("results", [])
        if not results and "openfda" in data:
            results = [data]

        for item in results:
            doc_id = item.get("id") or item.get("set_id") or "openfda-label"
            openfda_meta = item.get("openfda", {})

            # Determine title
            brand_names = openfda_meta.get("brand_name", [])
            generic_names = openfda_meta.get("generic_name", [])
            if brand_names:
                title = f"{brand_names[0]} ({generic_names[0] if generic_names else ''})".strip()
            elif generic_names:
                title = generic_names[0]
            else:
                title = f"FDA Drug Label: {doc_id}"

            # Effective date
            eff_time = item.get("effective_time", "20240101")
            date_str = f"{eff_time[0:4]}-{eff_time[4:6]}-{eff_time[6:8]}" if len(eff_time) >= 8 else "2024-01-01"
            version = str(item.get("version", "1.0"))

            # Iterate label sections
            for field_key, section_display in LABEL_SECTIONS:
                sec_content = item.get(field_key)
                if not sec_content:
                    continue

                if isinstance(sec_content, list):
                    text = "\n\n".join(str(s).strip() for s in sec_content if s)
                else:
                    text = str(sec_content).strip()

                if not text:
                    continue

                locator = f"https://api.fda.gov/drug/label.json?search=id:{doc_id}#{field_key}"

                doc = SourceDocument(
                    source_id=self.source_id,
                    doc_id=doc_id,
                    title=title,
                    section_path=["Label", section_display],
                    locator=locator,
                    version=version,
                    published_or_updated_date=date_str,
                    evidence_level="fda_label",
                    licence=licence,
                    text=text,
                    metadata={
                        "openfda": openfda_meta,
                        "section_field": field_key,
                    },
                )
                documents.append(doc)

        return documents
