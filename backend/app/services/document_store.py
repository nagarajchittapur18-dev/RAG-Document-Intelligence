import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger("ragmate.document_store")


class DocumentRecord(BaseModel):
    id: str
    filename: str
    file_path: str
    pages: int
    chunks: int
    file_size: int
    status: str
    created_at: str


class DocumentStore:
    """
    Lightweight SQLite document metadata registry.
    Persists document attributes across restarts and synchronizes with ChromaDB.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = str(base_dir / "ragmate_documents.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    pages INTEGER NOT NULL DEFAULT 0,
                    chunks INTEGER NOT NULL DEFAULT 0,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'completed',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_document(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        pages: int,
        chunks: int,
        file_size: int,
        status: str = "completed",
    ) -> DocumentRecord:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (id, filename, file_path, pages, chunks, file_size, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, filename, file_path, pages, chunks, file_size, status, now_iso),
            )
            conn.commit()

        return DocumentRecord(
            id=document_id,
            filename=filename,
            file_path=file_path,
            pages=pages,
            chunks=chunks,
            file_size=file_size,
            status=status,
            created_at=now_iso,
        )

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
            if row:
                return DocumentRecord(**dict(row))
        return None

    def list_documents(self) -> List[DocumentRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
            return [DocumentRecord(**dict(row)) for row in rows]

    def delete_document(self, document_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            return cur.rowcount > 0
