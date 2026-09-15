"""
Medical Knowledge Seeding Script
Populates the database vector store with textbook chunks from Harrison's Internal Medicine.
Usage:
    py -3.13 -m backend.database.seed_knowledge
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from .repository import db_repo, DatabaseRepository
from ..rag.book_parser import HarrisonParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SeedKnowledge")

CHUNKS_JSON_PATH = Path("data/knowledge/harrison_chunks.json")


def seed_harrison_knowledge(repo: DatabaseRepository = db_repo) -> Dict[str, Any]:
    """Reads Harrison's chunks, computes semantic embeddings, and stores them in the database."""
    chunks: List[Dict[str, Any]] = []

    # 1. Try reading from cached JSON
    if CHUNKS_JSON_PATH.exists():
        try:
            with open(CHUNKS_JSON_PATH, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                logger.info(f"Loaded {len(chunks)} chunks from {CHUNKS_JSON_PATH}")
        except Exception as e:
            logger.warning(f"Could not read {CHUNKS_JSON_PATH} ({e}), extracting from parser...")

    # 2. Fallback to HarrisonParser if needed
    if not chunks:
        parser = HarrisonParser()
        chunks = parser.load_or_extract_chunks(max_pages_per_chapter=2)
        logger.info(f"Extracted {len(chunks)} chunks using HarrisonParser.")

    if not chunks:
        logger.error("No chunks available to seed.")
        return {"status": "error", "message": "No chunks found", "seeded_count": 0}

    # 3. Ingest into database vector store
    seeded = 0
    specialties_seen = set()

    for item in chunks:
        chunk_id = item.get("id", f"HARRISON_P{item.get('page', 0)}_{abs(hash(item.get('text', '')[:40])) % 100000}")
        specialty = item.get("specialty", "INTERNAL_MEDICINE")
        book = item.get("book", "Harrison's Principles of Internal Medicine, 21st Ed.")
        chapter = item.get("chapter", "Internal Medicine")
        topic = item.get("topic", "Clinical Manifestations")
        content = item.get("text", "")
        page = item.get("page", 0)

        # Generate dense semantic vector representation
        embedding = repo.compute_embedding(f"{topic} {chapter} {content}")
        metadata = {
            "book": book,
            "page": page,
            "chapter": chapter,
            "topic": topic,
            "char_length": len(content),
        }

        repo.save_knowledge_chunk(
            chunk_id=chunk_id,
            specialty=specialty,
            book_title=book,
            chapter=chapter,
            topic=topic,
            content=content,
            embedding=embedding,
            metadata=metadata,
        )
        specialties_seen.add(specialty)
        seeded += 1

    total_in_db = repo.count_knowledge_chunks()
    logger.info(f"Successfully seeded {seeded} knowledge chunks. Total in database: {total_in_db}.")

    return {
        "status": "success",
        "seeded_count": seeded,
        "total_in_db": total_in_db,
        "specialties": list(specialties_seen),
        "engine": repo.manager.engine_type,
        "pgvector_active": repo.manager.pgvector_enabled,
    }


def main():
    logger.info("Starting Harrison's Medical Knowledge database vector seeding...")
    result = seed_harrison_knowledge()
    logger.info(f"Seeding completed: {result}")


if __name__ == "__main__":
    main()
