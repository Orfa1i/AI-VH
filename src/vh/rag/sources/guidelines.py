"""
Local clinical guidelines source adapter with sidecar metadata and licence validation.
"""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import yaml

from vh.rag.sources.base import (
    SourceAdapter,
    SourceDocument,
    LicenceEnforcementError,
    assert_licence_permitted,
    is_licence_permitted,
    logger,
)


class LocalGuidelinesAdapter(SourceAdapter):
    """
    Adapter for ingesting local clinical guidelines stored with sidecar metadata files.
    """
    source_id = "guidelines"

    def __init__(self, guidelines_dir: Path):
        self.guidelines_dir = Path(guidelines_dir)

    def load_all(self) -> List[SourceDocument]:
        """
        Load all permitted guidelines in the guidelines directory.
        Unpermitted or licence-unknown guidelines are rejected and logged.
        """
        all_documents: List[SourceDocument] = []
        if not self.guidelines_dir.exists():
            return all_documents

        for doc_path in sorted(self.guidelines_dir.glob("*.*")):
            if doc_path.name.endswith(".meta.json") or doc_path.name.endswith(".meta.yaml") or doc_path.name.endswith(".meta.yml"):
                continue
            if doc_path.suffix.lower() not in {".md", ".txt", ".json"}:
                continue

            try:
                docs = self.load_file(doc_path)
                all_documents.extend(docs)
            except LicenceEnforcementError as e:
                logger.warning(f"Skipping guideline {doc_path.name}: {e}")
            except Exception as e:
                logger.error(f"Error loading guideline {doc_path.name}: {e}")

        return all_documents

    def load_file(self, file_path: Path) -> List[SourceDocument]:
        """
        Load and parse a single guideline file and its accompanying sidecar metadata.
        Raises LicenceEnforcementError if the sidecar licence is unpermitted or missing.
        """
        file_path = Path(file_path)
        content = file_path.read_text(encoding="utf-8")
        sidecar = self._load_sidecar(file_path)

        doc_id = sidecar.get("doc_id", file_path.stem)
        title = sidecar.get("title", file_path.stem.replace("_", " ").title())
        version = str(sidecar.get("version", "1.0"))
        date_str = sidecar.get("published_or_updated_date", "2024-01-01")
        evidence_level = sidecar.get("evidence_level", "guideline_class_1")
        licence = sidecar.get("licence", "")
        locator = sidecar.get("locator", str(file_path).replace("\\", "/"))

        # Enforce licence policy
        assert_licence_permitted(licence, doc_id=doc_id)

        # Parse sections based on file type
        return self.parse_sections(
            text=content,
            doc_id=doc_id,
            title=title,
            version=version,
            date_str=date_str,
            evidence_level=evidence_level,
            licence=licence,
            locator=locator,
            sidecar_meta=sidecar,
        )

    def parse(self, raw_content: Any, **kwargs: Any) -> List[SourceDocument]:
        """Parse raw markdown or text string with kwargs metadata."""
        text = str(raw_content)
        doc_id = kwargs.get("doc_id", "local-guideline")
        title = kwargs.get("title", "Clinical Practice Guideline")
        version = str(kwargs.get("version", "1.0"))
        date_str = kwargs.get("published_or_updated_date", "2024-01-01")
        evidence_level = kwargs.get("evidence_level", "guideline_class_1")
        licence = kwargs.get("licence", "")
        locator = kwargs.get("locator", f"guidelines/{doc_id}")

        assert_licence_permitted(licence, doc_id=doc_id)

        return self.parse_sections(
            text=text,
            doc_id=doc_id,
            title=title,
            version=version,
            date_str=date_str,
            evidence_level=evidence_level,
            licence=licence,
            locator=locator,
            sidecar_meta=kwargs,
        )

    def parse_sections(
        self,
        text: str,
        doc_id: str,
        title: str,
        version: str,
        date_str: str,
        evidence_level: str,
        licence: str,
        locator: str,
        sidecar_meta: Dict[str, Any],
    ) -> List[SourceDocument]:
        """Parse markdown heading structure into sections."""
        lines = text.splitlines()
        sections: List[SourceDocument] = []

        current_heading_path: List[str] = []
        current_lines: List[str] = []

        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s+(.*)$', line)
            if heading_match:
                # Flush previous section
                if current_lines:
                    sec_text = "\n".join(current_lines).strip()
                    if sec_text:
                        sec_name = current_heading_path[-1] if current_heading_path else "Overview"
                        sec_anchor = re.sub(r'[^a-zA-Z0-9_-]', '', sec_name.lower().replace(" ", "-"))
                        sec_loc = f"{locator}#{sec_anchor}"
                        sections.append(SourceDocument(
                            source_id=self.source_id,
                            doc_id=doc_id,
                            title=title,
                            section_path=list(current_heading_path) if current_heading_path else ["Overview"],
                            locator=sec_loc,
                            version=version,
                            published_or_updated_date=date_str,
                            evidence_level=evidence_level,
                            licence=licence,
                            text=sec_text,
                            metadata=dict(sidecar_meta),
                        ))
                    current_lines = []

                level = len(heading_match.group(1))
                h_title = heading_match.group(2).strip()

                # Adjust heading path based on depth
                if level == 1:
                    current_heading_path = [h_title]
                else:
                    current_heading_path = current_heading_path[:level - 1] + [h_title]
            else:
                current_lines.append(line)

        # Flush trailing section
        if current_lines:
            sec_text = "\n".join(current_lines).strip()
            if sec_text:
                sec_name = current_heading_path[-1] if current_heading_path else "Overview"
                sec_anchor = re.sub(r'[^a-zA-Z0-9_-]', '', sec_name.lower().replace(" ", "-"))
                sec_loc = f"{locator}#{sec_anchor}"
                sections.append(SourceDocument(
                    source_id=self.source_id,
                    doc_id=doc_id,
                    title=title,
                    section_path=list(current_heading_path) if current_heading_path else ["Overview"],
                    locator=sec_loc,
                    version=version,
                    published_or_updated_date=date_str,
                    evidence_level=evidence_level,
                    licence=licence,
                    text=sec_text,
                    metadata=dict(sidecar_meta),
                ))

        return sections

    def _load_sidecar(self, file_path: Path) -> Dict[str, Any]:
        """Locate and load .meta.json or .meta.yaml sidecar for a guideline file."""
        json_sidecar = file_path.with_name(f"{file_path.name}.meta.json")
        if json_sidecar.exists():
            return json.loads(json_sidecar.read_text(encoding="utf-8"))

        yaml_sidecar = file_path.with_name(f"{file_path.name}.meta.yaml")
        if yaml_sidecar.exists():
            return yaml.safe_load(yaml_sidecar.read_text(encoding="utf-8")) or {}

        # Also check stem.meta.json
        stem_json = file_path.with_name(f"{file_path.stem}.meta.json")
        if stem_json.exists():
            return json.loads(stem_json.read_text(encoding="utf-8"))

        return {}
