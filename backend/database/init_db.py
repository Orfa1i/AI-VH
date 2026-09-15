"""
Database Initialization Script
Runs table creation, extensions setup, and status check.
Usage:
    py -3.13 -m backend.database.init_db
"""

import sys
import logging
from backend.database.connection import db_manager
from backend.database.repository import db_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("InitDB")


def main():
    logger.info("Initializing AI Virtual Hospital Database...")
    status = db_manager.get_status()
    logger.info(f"Database Engine: {status['engine']}")
    logger.info(f"Storage Target: {status['storage_path']}")
    logger.info(f"pgvector Extension Active: {status['pgvector_enabled']}")

    db_repo.init_schema()
    
    report_count = db_repo.count_reports()
    review_count = db_repo.count_reviews()
    chunk_count = db_repo.count_knowledge_chunks()
    
    if chunk_count == 0:
        logger.info("Knowledge vector table is empty. Auto-seeding Harrison's Internal Medicine...")
        from backend.database.seed_knowledge import seed_harrison_knowledge
        seed_res = seed_harrison_knowledge(db_repo)
        chunk_count = seed_res.get("total_in_db", chunk_count)
        logger.info(f"Auto-seeded {seed_res.get('seeded_count', 0)} chunks.")

    logger.info(f"Schema initialized. Existing records: {report_count} reports, {review_count} reviews, {chunk_count} knowledge chunks.")
    logger.info("Database ready for clinical encounters.")


if __name__ == "__main__":
    main()
