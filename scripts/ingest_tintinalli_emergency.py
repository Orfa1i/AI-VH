"""
Ingestion & Vector Embedding Script for Tintinalli's Emergency Medicine Manual
Extracts text from the 1,089-page emergency medicine manual, chunks into structured clinical passages,
computes 384-dimensional dense vectors with all-MiniLM-L6-v2 on NVIDIA RTX 4060 GPU with CUDA,
and stores vectors into data/knowledge and SQLite knowledge_chunks table.
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
logger = logging.getLogger("TintinalliIngestion")

PDF_PATH = PROJECT_ROOT / "Medical Books/Agent for (Emergency-medicine)/Tintinallis_Emergency_Medicine_Manual.pdf"
if not PDF_PATH.exists():
    ALT_PATH = Path(r"C:\Users\PCD\Desktop\Med-books\Tintinalli’s Emergency Medicine Manual ( PDFDrive ).pdf")
    if ALT_PATH.exists():
        PDF_PATH = ALT_PATH

BOOK_TITLE = "Tintinalli's Emergency Medicine Manual"
SPECIALTY = "Emergency Medicine"
COLLECTION_PATH = PROJECT_ROOT / "data/knowledge/tintinalli_collection.json"
EMBEDDINGS_PATH = PROJECT_ROOT / "data/knowledge/tintinalli_embeddings.npy"
CHECKPOINT_PATH = PROJECT_ROOT / "data/knowledge/tintinalli_checkpoint.json"


def run_tintinalli_ingestion(resume: bool = True, limit_pages: int = None):
    logger.info("Initializing SpecialtyBookEmbedder for Tintinalli's Emergency Medicine...")
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
    parser = argparse.ArgumentParser(description="Ingest & embed Tintinalli's Emergency Medicine Manual")
    parser.add_argument("--fresh", action="store_true", help="Start ingestion from scratch, ignoring checkpoint")
    parser.add_argument("--limit-pages", type=int, default=None, help="Limit number of pages for dry-run testing")
    args = parser.parse_args()

    run_tintinalli_ingestion(resume=not args.fresh, limit_pages=args.limit_pages)
