"""
Generalized Multi-Specialty Medical Textbook Embedding Engine
Extracts, chunks, embeds with all-MiniLM-L6-v2 on GPU, and stores medical textbooks into the database.
Supports Harrison's, Braunwald's Heart Disease, and other specialty clinical literature.
"""

import os
import sys
import re
import json
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.vector_embedder import get_vector_embedder
from backend.database.repository import DatabaseRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SpecialtyBookEmbedder")

TARGET_CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
BATCH_PAGES = 100
EMBEDDING_BATCH_SIZE = 128


class SpecialtyBookEmbedder:
    def __init__(
        self,
        pdf_path: Path,
        book_title: str,
        specialty: str,
        collection_path: Path,
        embeddings_path: Path,
        checkpoint_path: Path,
        custom_page_map: Optional[List[Tuple[int, int, str]]] = None,
    ):
        self.pdf_path = Path(pdf_path)
        self.book_title = book_title
        self.specialty = specialty
        self.collection_path = Path(collection_path)
        self.embeddings_path = Path(embeddings_path)
        self.checkpoint_path = Path(checkpoint_path)
        self.custom_page_map = custom_page_map

        self.db_repo = DatabaseRepository()
        self.embedder = get_vector_embedder()
        self.doc = None
        self.page_map: List[Tuple[int, int, str]] = []
        self._init_pdf()

    def _init_pdf(self):
        import fitz
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {self.pdf_path}")

        logger.info(f"Opening {self.book_title} ({self.pdf_path.name})...")
        self.doc = fitz.open(str(self.pdf_path))
        self.total_pages = len(self.doc)
        logger.info(f"Loaded {self.book_title} with {self.total_pages} pages.")

        if self.custom_page_map:
            self.page_map = sorted(self.custom_page_map, key=lambda x: x[0])
            logger.info(f"Using provided custom page map with {len(self.page_map)} entries.")
        else:
            toc = self.doc.get_toc()
            logger.info(f"Found {len(toc)} Table of Contents entries.")
            for level, title, p in toc:
                self.page_map.append((p, level, title.strip()))
            self.page_map.sort(key=lambda x: x[0])

    def get_chapter_info(self, page_num_1based: int) -> Tuple[str, str]:
        curr_part = self.specialty
        curr_chap = self.book_title

        for p_start, level, title in self.page_map:
            if p_start <= page_num_1based:
                if level == 1:
                    curr_part = title
                elif level >= 2:
                    curr_chap = title
            else:
                break

        return curr_part, curr_chap

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"[A-Za-z0-9_]+_p\d+-p\d+\.indd[^\n]+", "", text)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def chunk_page_text(self, text: str, page_num_1based: int) -> List[Dict[str, Any]]:
        clean = self.clean_text(text)
        if len(clean) < 120:
            return []

        part_title, chapter_title = self.get_chapter_info(page_num_1based)
        chunks: List[Dict[str, Any]] = []

        start = 0
        chunk_idx = 0
        text_len = len(clean)

        # Prefix book abbreviation for chunk id
        book_prefix = "".join(w[0] for w in self.book_title.split()[:3]).upper()

        while start < text_len:
            end = min(start + TARGET_CHUNK_SIZE, text_len)
            if end < text_len:
                boundary = -1
                for punct in [". ", "; ", "?\n", "!\n", "\n\n"]:
                    pos = clean.rfind(punct, start + (TARGET_CHUNK_SIZE // 2), end)
                    if pos > boundary:
                        boundary = pos + len(punct)
                if boundary > 0:
                    end = boundary

            chunk_content = clean[start:end].strip()
            if len(chunk_content) >= 80:
                chunk_id = f"{book_prefix}_P{page_num_1based:04d}_C{chunk_idx:02d}"
                chunks.append({
                    "id": chunk_id,
                    "specialty": self.specialty,
                    "book": self.book_title,
                    "book_title": self.book_title,
                    "part": part_title,
                    "chapter": chapter_title,
                    "topic": chapter_title,
                    "page": page_num_1based,
                    "text": chunk_content,
                    "content": chunk_content,
                    "metadata": {
                        "page": page_num_1based,
                        "part": part_title,
                        "chapter": chapter_title,
                        "chunk_index": chunk_idx,
                        "char_length": len(chunk_content),
                    },
                })
                chunk_idx += 1

            start = end - CHUNK_OVERLAP if end < text_len else end

        return chunks

    def load_checkpoint(self) -> Dict[str, Any]:
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_completed_page": 0, "total_chunks": 0}

    def save_checkpoint(self, last_page: int, total_chunks: int, elapsed: float):
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump({
                "book": self.book_title,
                "specialty": self.specialty,
                "last_completed_page": last_page,
                "total_chunks": total_chunks,
                "total_pages": self.total_pages,
                "elapsed_seconds": round(elapsed, 1),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, f, indent=2)

    def run_ingestion(self, resume: bool = True):
        logger.info("=================================================================")
        logger.info(f"Ingesting & Embedding: {self.book_title} ({self.specialty})")
        logger.info(f"Target: {self.total_pages} pages | GPU: RTX 4060 | Model: all-MiniLM-L6-v2")
        logger.info("=================================================================")

        checkpoint = self.load_checkpoint() if resume else {"last_completed_page": 0, "total_chunks": 0}
        start_page = checkpoint.get("last_completed_page", 0)
        total_embedded_chunks = checkpoint.get("total_chunks", 0)

        all_chunks_collection: List[Dict[str, Any]] = []
        if resume and self.collection_path.exists():
            try:
                with open(self.collection_path, "r", encoding="utf-8") as f:
                    all_chunks_collection = json.load(f)
                    logger.info(f"Loaded {len(all_chunks_collection)} existing chunks from {self.collection_path}")
            except Exception:
                pass

        all_embeddings_list: List[List[float]] = []
        if resume and self.embeddings_path.exists():
            try:
                arr = np.load(str(self.embeddings_path))
                all_embeddings_list = arr.tolist()
                logger.info(f"Loaded {len(all_embeddings_list)} existing embeddings from {self.embeddings_path}")
            except Exception:
                pass

        t_start = time.time()

        for page_batch_start in range(start_page, self.total_pages, BATCH_PAGES):
            page_batch_end = min(page_batch_start + BATCH_PAGES, self.total_pages)
            t_batch_start = time.time()

            batch_chunks: List[Dict[str, Any]] = []
            for p in range(page_batch_start, page_batch_end):
                try:
                    raw_text = self.doc[p].get_text()
                    page_chunks = self.chunk_page_text(raw_text, page_num_1based=p + 1)
                    batch_chunks.extend(page_chunks)
                except Exception as e:
                    logger.warning(f"Error extracting page {p + 1}: {e}")

            if batch_chunks:
                texts_to_embed = [c["content"] for c in batch_chunks]
                t_embed_start = time.time()
                batch_embeddings = self.embedder.embed_texts(texts_to_embed, batch_size=EMBEDDING_BATCH_SIZE)
                embed_duration = time.time() - t_embed_start

                for chunk, emb in zip(batch_chunks, batch_embeddings):
                    chunk["embedding"] = emb

                t_db_start = time.time()
                self.db_repo.batch_save_knowledge_chunks(batch_chunks)
                db_duration = time.time() - t_db_start

                all_chunks_collection.extend([
                    {
                        "id": c["id"],
                        "specialty": c["specialty"],
                        "book": c["book"],
                        "chapter": c["chapter"],
                        "topic": c["topic"],
                        "page": c["page"],
                        "text": c["text"],
                    }
                    for c in batch_chunks
                ])
                all_embeddings_list.extend(batch_embeddings)
                total_embedded_chunks += len(batch_chunks)

                throughput = len(batch_chunks) / max(embed_duration, 0.001)

                logger.info(
                    f"[{self.specialty}] Pages [{page_batch_start + 1:4d}-{page_batch_end:4d}/{self.total_pages}] "
                    f"({(page_batch_end / self.total_pages) * 100:5.1f}%) | "
                    f"Batch Chunks: {len(batch_chunks):4d} | "
                    f"Total Chunks: {total_embedded_chunks:6d} | "
                    f"Embed: {embed_duration:.2f}s ({throughput:.0f} ch/s) | "
                    f"DB: {db_duration:.2f}s"
                )

            elapsed = time.time() - t_start
            self.save_checkpoint(page_batch_end, total_embedded_chunks, elapsed)

            if page_batch_end % 500 == 0 or page_batch_end == self.total_pages:
                self._persist(all_chunks_collection, all_embeddings_list)

        self._persist(all_chunks_collection, all_embeddings_list)
        total_time = time.time() - t_start
        logger.info("=================================================================")
        logger.info(f"SUCCESS: Fully Embedded {self.book_title}!")
        logger.info(f"Total Pages Processed: {self.total_pages}")
        logger.info(f"Total Chunks Generated & Stored: {total_embedded_chunks:,}")
        logger.info(f"Specialty: {self.specialty}")
        logger.info(f"Database Table: knowledge_chunks in data/aivh.db")
        logger.info(f"Total Elapsed Time: {total_time:.2f}s ({total_time / 60:.2f} min)")
        logger.info("=================================================================")

    def _persist(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        self.collection_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.collection_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2)
            emb_matrix = np.array(embeddings, dtype=np.float32)
            np.save(str(self.embeddings_path), emb_matrix)
        except Exception as e:
            logger.error(f"Error persisting {self.book_title}: {e}")


def ingest_braunwald(resume: bool = True):
    pdf = PROJECT_ROOT / "Medical Books/Agent for (Cardiology)/Braunwalds_Heart_Disease_Cardiovascular_Medicine.pdf"
    embedder = SpecialtyBookEmbedder(
        pdf_path=pdf,
        book_title="Braunwald's Heart Disease: A Textbook of Cardiovascular Medicine",
        specialty="Cardiology",
        collection_path=PROJECT_ROOT / "data/knowledge/braunwald_collection.json",
        embeddings_path=PROJECT_ROOT / "data/knowledge/braunwald_embeddings.npy",
        checkpoint_path=PROJECT_ROOT / "data/knowledge/braunwald_checkpoint.json",
    )
    embedder.run_ingestion(resume=resume)


if __name__ == "__main__":
    resume_mode = "--fresh" not in sys.argv
    ingest_braunwald(resume=resume_mode)
