"""
Harrison's Principles of Internal Medicine (21st Edition) Full Book Ingestion & Embedding Engine
Extracts, chunks, embeds with all-MiniLM-L6-v2 on GPU, and stores all 4,132 pages into the database.
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

# Adjust path for standalone execution
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
logger = logging.getLogger("FullBookEmbedder")

PDF_PATH = PROJECT_ROOT / "Medical Books/Agent for (Internal-medicine)/Harrison's_Internal_Medicine_2022,_21th_Edition_Vol_1_&_Vol_2_.pdf"
COLLECTION_PATH = PROJECT_ROOT / "data/knowledge/harrison_full_collection.json"
EMBEDDINGS_PATH = PROJECT_ROOT / "data/knowledge/harrison_embeddings.npy"
CHECKPOINT_PATH = PROJECT_ROOT / "data/knowledge/harrison_checkpoint.json"

TARGET_CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
BATCH_PAGES = 100
EMBEDDING_BATCH_SIZE = 128


class HarrisonFullBookIngestor:
    def __init__(self, pdf_path: Path = PDF_PATH):
        self.pdf_path = pdf_path
        self.db_repo = DatabaseRepository()
        self.embedder = get_vector_embedder()
        self.doc = None
        self.page_map: List[Tuple[int, int, str]] = []
        self._init_pdf()

    def _init_pdf(self):
        import fitz  # PyMuPDF
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Harrison's PDF not found at {self.pdf_path}")

        logger.info(f"Opening {self.pdf_path.name}...")
        self.doc = fitz.open(str(self.pdf_path))
        self.total_pages = len(self.doc)
        logger.info(f"Loaded PDF with {self.total_pages} pages.")

        # Build TOC mapping
        toc = self.doc.get_toc()
        logger.info(f"Found {len(toc)} Table of Contents entries.")
        for level, title, p in toc:
            self.page_map.append((p, level, title.strip()))
        self.page_map.sort(key=lambda x: x[0])

    def get_chapter_info(self, page_num_1based: int) -> Tuple[str, str]:
        """Maps 1-indexed page number to (Part Title, Chapter Title)."""
        curr_part = "General Internal Medicine"
        curr_chap = "Harrison's Principles of Internal Medicine"

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
        """Removes printer codes, header lines, and excessive whitespaces."""
        if not text:
            return ""
        # Remove publisher headers / footer tags (e.g., HPIM21e_Part1_p001-p090.indd 88 19/01/22 1:52 PM)
        text = re.sub(r"HPIM21e_[^\n]+\.indd[^\n]+", "", text)
        # Remove standalone page numbers or headers
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
        # Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def chunk_page_text(self, text: str, page_num_1based: int) -> List[Dict[str, Any]]:
        """Segments page text into clinical chunks with semantic boundaries."""
        clean = self.clean_text(text)
        if len(clean) < 120:
            return []

        part_title, chapter_title = self.get_chapter_info(page_num_1based)
        chunks: List[Dict[str, Any]] = []

        start = 0
        chunk_idx = 0
        text_len = len(clean)

        while start < text_len:
            end = min(start + TARGET_CHUNK_SIZE, text_len)
            if end < text_len:
                # Seek best sentence boundary (. or ; or ? or !)
                boundary = -1
                for punct in [". ", "; ", "?\n", "!\n", "\n\n"]:
                    pos = clean.rfind(punct, start + (TARGET_CHUNK_SIZE // 2), end)
                    if pos > boundary:
                        boundary = pos + len(punct)
                if boundary > 0:
                    end = boundary

            chunk_content = clean[start:end].strip()
            if len(chunk_content) >= 80:
                chunk_id = f"HARRISON_P{page_num_1based:04d}_C{chunk_idx:02d}"
                chunks.append({
                    "id": chunk_id,
                    "specialty": "Internal Medicine",
                    "book": "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
                    "book_title": "Harrison's Principles of Internal Medicine, 21st Edition (2022)",
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
        if CHECKPOINT_PATH.exists():
            try:
                with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading checkpoint ({e}), starting fresh.")
        return {"last_completed_page": 0, "total_chunks": 0}

    def save_checkpoint(self, last_page: int, total_chunks: int, elapsed: float):
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "last_completed_page": last_page,
                "total_chunks": total_chunks,
                "total_pages": self.total_pages,
                "elapsed_seconds": round(elapsed, 1),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, f, indent=2)

    def run_full_ingestion(self, resume: bool = True):
        logger.info("=================================================================")
        logger.info("Starting Full Harrison's Principles of Internal Medicine Embedding")
        logger.info(f"Target: {self.total_pages} pages | GPU: RTX 4060 | Model: all-MiniLM-L6-v2")
        logger.info("=================================================================")

        checkpoint = self.load_checkpoint() if resume else {"last_completed_page": 0, "total_chunks": 0}
        start_page = checkpoint.get("last_completed_page", 0)
        total_embedded_chunks = checkpoint.get("total_chunks", 0)

        # Load existing chunks collection if resuming
        all_chunks_collection: List[Dict[str, Any]] = []
        if resume and COLLECTION_PATH.exists():
            try:
                with open(COLLECTION_PATH, "r", encoding="utf-8") as f:
                    all_chunks_collection = json.load(f)
                    logger.info(f"Loaded {len(all_chunks_collection)} existing chunks from {COLLECTION_PATH}")
            except Exception as e:
                logger.warning(f"Could not load collection JSON ({e})")

        all_embeddings_list: List[List[float]] = []
        if resume and EMBEDDINGS_PATH.exists():
            try:
                arr = np.load(str(EMBEDDINGS_PATH))
                all_embeddings_list = arr.tolist()
                logger.info(f"Loaded {len(all_embeddings_list)} existing embeddings from {EMBEDDINGS_PATH}")
            except Exception as e:
                logger.warning(f"Could not load embeddings npy ({e})")

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
                # 1. Compute dense embeddings on GPU
                texts_to_embed = [c["content"] for c in batch_chunks]
                t_embed_start = time.time()
                batch_embeddings = self.embedder.embed_texts(texts_to_embed, batch_size=EMBEDDING_BATCH_SIZE)
                embed_duration = time.time() - t_embed_start

                # Attach embeddings to chunks
                for chunk, emb in zip(batch_chunks, batch_embeddings):
                    chunk["embedding"] = emb

                # 2. Batch insert into SQLite knowledge_chunks table
                t_db_start = time.time()
                inserted = self.db_repo.batch_save_knowledge_chunks(batch_chunks)
                db_duration = time.time() - t_db_start

                # 3. Append to memory lists
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

                batch_total_time = time.time() - t_batch_start
                throughput = len(batch_chunks) / max(embed_duration, 0.001)

                logger.info(
                    f"Pages [{page_batch_start + 1:4d}-{page_batch_end:4d}/{self.total_pages}] "
                    f"({(page_batch_end / self.total_pages) * 100:5.1f}%) | "
                    f"Batch Chunks: {len(batch_chunks):4d} | "
                    f"Total Chunks: {total_embedded_chunks:6d} | "
                    f"Embed: {embed_duration:.2f}s ({throughput:.0f} ch/s) | "
                    f"DB: {db_duration:.2f}s"
                )
            else:
                logger.info(f"Pages [{page_batch_start + 1:4d}-{page_batch_end:4d}/{self.total_pages}] had no text chunks.")

            # Update checkpoint and save on-disk files periodically (every 500 pages or at end)
            elapsed = time.time() - t_start
            self.save_checkpoint(page_batch_end, total_embedded_chunks, elapsed)

            if page_batch_end % 500 == 0 or page_batch_end == self.total_pages:
                self._persist_collection_and_vectors(all_chunks_collection, all_embeddings_list)

        # Final persistence
        self._persist_collection_and_vectors(all_chunks_collection, all_embeddings_list)
        total_time = time.time() - t_start
        logger.info("=================================================================")
        logger.info(f"SUCCESS: Fully Embedded Harrison's Principles of Internal Medicine!")
        logger.info(f"Total Pages Processed: {self.total_pages}")
        logger.info(f"Total Chunks Generated & Stored: {total_embedded_chunks:,}")
        logger.info(f"Database Table: knowledge_chunks in data/aivh.db")
        logger.info(f"Total Elapsed Time: {total_time:.2f}s ({total_time / 60:.2f} min)")
        logger.info("=================================================================")

    def _persist_collection_and_vectors(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        COLLECTION_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            logger.info(f"Saving collection JSON ({len(chunks)} chunks) to {COLLECTION_PATH}...")
            with open(COLLECTION_PATH, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2)

            logger.info(f"Saving NumPy embeddings array ({len(embeddings)} vectors) to {EMBEDDINGS_PATH}...")
            emb_matrix = np.array(embeddings, dtype=np.float32)
            np.save(str(EMBEDDINGS_PATH), emb_matrix)
            logger.info(f"Persisted embeddings matrix with shape: {emb_matrix.shape}")
        except Exception as e:
            logger.error(f"Error persisting collection or embeddings: {e}")


if __name__ == "__main__":
    resume_flag = "--fresh" not in sys.argv
    ingestor = HarrisonFullBookIngestor()
    ingestor.run_full_ingestion(resume=resume_flag)
