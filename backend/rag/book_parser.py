"""
Harrison's Internal Medicine Textbook Parser & Chunker
Extracts structured chunks with chapter, section, and page metadata for RAG.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("BookParser")

DEFAULT_BOOK_PATH = Path("Medical Books/Agent for (Internal-medicine)/Harrison's_Internal_Medicine_2022,_21th_Edition_Vol_1_&_Vol_2_.pdf")
CACHE_PATH = Path("data/knowledge/harrison_chunks.json")

# High-yield Internal Medicine topics & starting page approximations in Harrison's 21st Ed
CORE_CLINICAL_CHAPTERS = [
    {"topic": "Chest Discomfort", "sample_page": 115, "chapter": "Part 2: Cardinal Manifestations - Chest Pain"},
    {"topic": "Dyspnea & Pulmonary Edema", "sample_page": 128, "chapter": "Part 2: Cardinal Manifestations - Dyspnea"},
    {"topic": "Fever & Hyperthermia", "sample_page": 142, "chapter": "Part 2: Cardinal Manifestations - Fever"},
    {"topic": "Abdominal Pain", "sample_page": 158, "chapter": "Part 2: Cardinal Manifestations - Abdominal Pain"},
    {"topic": "Acute Coronary Syndromes & MI", "sample_page": 1820, "chapter": "Disorders of the Cardiovascular System - ACS"},
    {"topic": "Heart Failure", "sample_page": 1860, "chapter": "Disorders of the Cardiovascular System - Heart Failure"},
    {"topic": "Diabetic Ketoacidosis & Hyperglycemia", "sample_page": 2840, "chapter": "Endocrinology & Metabolism - Diabetes Mellitus"},
    {"topic": "Sepsis & Septic Shock", "sample_page": 2210, "chapter": "Infectious Diseases - Sepsis"},
    {"topic": "Acute Kidney Injury", "sample_page": 2350, "chapter": "Disorders of the Kidney - AKI"},
    {"topic": "Hypertensive Emergencies", "sample_page": 1940, "chapter": "Cardiovascular Disorders - Hypertension"},
]


class MedicalChunk:
    def __init__(self, text: str, page: int, chapter: str, topic: str, specialty: str = "Internal Medicine"):
        self.text = text.strip()
        self.page = page
        self.chapter = chapter
        self.topic = topic
        self.specialty = specialty
        self.id = f"HARRISON_P{page}_{abs(hash(text[:50])) % 100000}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "book": "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
            "chapter": self.chapter,
            "topic": self.topic,
            "page": self.page,
            "specialty": self.specialty,
            "text": self.text,
        }


class HarrisonParser:
    def __init__(self, pdf_path: Path = DEFAULT_BOOK_PATH, cache_path: Path = CACHE_PATH):
        self.pdf_path = pdf_path
        self.cache_path = cache_path

    def load_or_extract_chunks(self, max_pages_per_chapter: int = 4) -> List[Dict[str, Any]]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    logger.info(f"Loaded {len(cached)} medical chunks from cache: {self.cache_path}")
                    return cached
            except Exception as e:
                logger.warning(f"Failed to read cache ({e}), re-extracting from PDF...")

        return self.extract_core_chapters(max_pages_per_chapter=max_pages_per_chapter)

    def extract_core_chapters(self, max_pages_per_chapter: int = 4) -> List[Dict[str, Any]]:
        import pypdf

        if not self.pdf_path.exists():
            logger.error(f"Harrison PDF not found at {self.pdf_path}")
            return []

        logger.info(f"Extracting high-yield chapters from {self.pdf_path}...")
        reader = pypdf.PdfReader(str(self.pdf_path))
        total_pages = len(reader.pages)
        chunks: List[Dict[str, Any]] = []

        for ch in CORE_CLINICAL_CHAPTERS:
            start_p = min(ch["sample_page"], total_pages - 1)
            end_p = min(start_p + max_pages_per_chapter, total_pages)

            for p_num in range(start_p, end_p):
                try:
                    raw_text = reader.pages[p_num].extract_text() or ""
                    clean_text = self._clean_medical_text(raw_text)
                    if len(clean_text) < 150:
                        continue

                    # Split page into 800-1200 character paragraphs
                    paragraphs = self._split_paragraphs(clean_text)
                    for para in paragraphs:
                        chunk = MedicalChunk(
                            text=para,
                            page=p_num + 1,  # 1-indexed for medical citation
                            chapter=ch["chapter"],
                            topic=ch["topic"],
                        )
                        chunks.append(chunk.to_dict())
                except Exception as e:
                    logger.warning(f"Error extracting page {p_num}: {e}")

        # Save cache
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)
        logger.info(f"Cached {len(chunks)} Harrison's chunks to {self.cache_path}")
        return chunks

    def _clean_medical_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        # Remove standalone page numbers and header fragments
        text = re.sub(r"^\d+\s*\n", "", text, flags=re.MULTILINE)
        return text.strip()

    def _split_paragraphs(self, text: str, max_chars: int = 1000, overlap: int = 150) -> List[str]:
        raw_paras = text.split("\n\n")
        chunks = []
        current = ""

        for p in raw_paras:
            p_clean = p.replace("\n", " ").strip()
            if not p_clean:
                continue
            if len(current) + len(p_clean) < max_chars:
                current += (" " if current else "") + p_clean
            else:
                if current:
                    chunks.append(current)
                current = p_clean

        if current:
            chunks.append(current)

        return [c for c in chunks if len(c) > 100]
