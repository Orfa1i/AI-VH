"""
Ingestion & Vector Embedding Script for Williams Gynecology
Extracts text from Williams Gynecology (Study Guide / Reference),
chunks into structured clinical passages, computes 384-dimensional dense vectors
with all-MiniLM-L6-v2 on NVIDIA RTX 4060 GPU with CUDA acceleration, and stores vectors into
data/knowledge/gynecology_collection.json, data/knowledge/gynecology_embeddings.npy,
and SQLite knowledge_chunks table in data/aivh.db.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.specialty_book_embedder import SpecialtyBookEmbedder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("GynecologyIngestion")

PDF_PATH = PROJECT_ROOT / "Medical Books/Agent for (Gynecology)/Williams_Gynecology.pdf"
if not PDF_PATH.exists():
    ALT_PATH = Path(r"C:\Users\PCD\Desktop\Med-books\Williams gynecology.pdf")
    if ALT_PATH.exists():
        PDF_PATH = ALT_PATH

BOOK_TITLE = "Williams Gynecology"
SPECIALTY = "Gynecology"
COLLECTION_PATH = PROJECT_ROOT / "data/knowledge/gynecology_collection.json"
EMBEDDINGS_PATH = PROJECT_ROOT / "data/knowledge/gynecology_embeddings.npy"
CHECKPOINT_PATH = PROJECT_ROOT / "data/knowledge/gynecology_checkpoint.json"


def run_gynecology_ingestion(resume: bool = True, limit_pages: int = None):
    logger.info("Initializing SpecialtyBookEmbedder for Williams Gynecology...")
    embedder = SpecialtyBookEmbedder(
        pdf_path=PDF_PATH,
        book_title=BOOK_TITLE,
        specialty=SPECIALTY,
        collection_path=COLLECTION_PATH,
        embeddings_path=EMBEDDINGS_PATH,
        checkpoint_path=CHECKPOINT_PATH,
    )
    if limit_pages is not None and limit_pages > 0:
        embedder.total_pages = min(embedder.total_pages, limit_pages)
        logger.info(f"Limiting ingestion to {embedder.total_pages} pages for test run.")

    embedder.run_ingestion(resume=resume)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest & embed Williams Gynecology")
    parser.add_argument("--fresh", action="store_true", help="Start ingestion from scratch, ignoring checkpoint")
    parser.add_argument("--limit-pages", type=int, default=None, help="Optional page limit for test run")
    args = parser.parse_args()

    run_gynecology_ingestion(resume=not args.fresh, limit_pages=args.limit_pages)
