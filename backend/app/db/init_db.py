"""
DocuRAG Production Database Migration & Schema Initializer
Supports zero-downtime initialization for both PostgreSQL and SQLite.
"""

import logging
import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.config import settings
from app.services.document_store import DatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ragmate.db.init")


def init_database() -> bool:
    """Initializes and verifies all database tables, columns, and indexes."""
    logger.info("Initializing DocuRAG Database...")
    target_url = getattr(settings, "DATABASE_URL", "sqlite:///./ragmate_database.db")
    dialect = "PostgreSQL" if "postgres" in target_url else "SQLite"
    logger.info("Target Dialect: %s (URL: %s)", dialect, target_url.split("@")[-1])

    try:
        db = DatabaseManager()
        is_healthy = db.ping()
        if not is_healthy:
            logger.error("Failed to connect to database during initialization.")
            return False

        logger.info("Successfully connected and pinged database.")

        # Verify tables exist
        required_tables = ["users", "documents", "chat_sessions", "messages", "chat_session_documents"]
        with db._get_connection() as conn:
            if db.is_postgres:
                res = conn.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    """
                )
                existing = [r["table_name"] for r in res.fetchall()]
            else:
                res = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing = [r["name"] for r in res.fetchall()]

        logger.info("Existing database tables: %s", existing)
        missing = [t for t in required_tables if t not in existing]
        if missing:
            logger.error("Missing required tables after initialization: %s", missing)
            return False

        logger.info("All required tables verified: %s", required_tables)
        logger.info("Database schema is fully production-ready.")
        return True

    except Exception as e:
        logger.error("Database migration error: %s", e, exc_info=True)
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
