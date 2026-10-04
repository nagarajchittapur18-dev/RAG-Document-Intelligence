import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("ragmate.database")


class UserRecord(BaseModel):
    id: str
    name: str
    email: str
    password_hash: str
    created_at: str
    updated_at: str


class DocumentRecord(BaseModel):
    id: str
    user_id: str
    filename: str
    file_path: str
    pages: int
    chunks: int
    file_size: int
    status: str
    created_at: str


class ChatSessionRecord(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str


class ChatMessageRecord(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str


class DatabaseManager:
    """
    Central SQLite database manager providing multi-tenant persistence
    for users, documents, chat sessions, and messages.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = str(base_dir / "ragmate_database.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # 1. Users table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # 2. Documents table (with user_id foreign key)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    pages INTEGER NOT NULL DEFAULT 0,
                    chunks INTEGER NOT NULL DEFAULT 0,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'completed',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )

            # Check and perform migration if documents table was created earlier without user_id
            cursor = conn.execute("PRAGMA table_info(documents)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                logger.info("Migrating documents table: adding user_id column...")
                conn.execute("ALTER TABLE documents ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default_user'")

            # 3. Chat sessions table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )

            # 4. Messages table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
                """
            )

            # 5. Chat session documents table (many-to-many relationship for document scope)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_session_documents (
                    session_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    PRIMARY KEY (session_id, document_id),
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id),
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
                """
            )

            # Check for is_active column in chat_session_documents
            cursor = conn.execute("PRAGMA table_info(chat_session_documents)")
            csd_cols = [r["name"] for r in cursor.fetchall()]
            if "is_active" not in csd_cols:
                conn.execute("ALTER TABLE chat_session_documents ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")

            # Performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id, updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_session_docs ON chat_session_documents(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_session_docs_doc ON chat_session_documents(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at DESC)")
            conn.commit()

    # =========================================================================
    # USER REPOSITORY
    # =========================================================================

    def create_user(self, name: str, email: str, password_hash: str) -> UserRecord:
        user_id = uuid.uuid4().hex[:12]
        now_iso = datetime.now(timezone.utc).isoformat()
        normalized_email = email.strip().lower()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, name, email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, name.strip(), normalized_email, password_hash, now_iso, now_iso),
            )
            conn.commit()

        return UserRecord(
            id=user_id,
            name=name.strip(),
            email=normalized_email,
            password_hash=password_hash,
            created_at=now_iso,
            updated_at=now_iso,
        )

    def get_user_by_email(self, email: str) -> Optional[UserRecord]:
        normalized_email = email.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (normalized_email,)).fetchone()
            if row:
                return UserRecord(**dict(row))
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserRecord]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                return UserRecord(**dict(row))
        return None

    # =========================================================================
    # DOCUMENT REPOSITORY (User Scoped)
    # =========================================================================

    def add_document(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        pages: int,
        chunks: int,
        file_size: int,
        user_id: str = "default_user",
        status: str = "completed",
    ) -> DocumentRecord:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (id, user_id, filename, file_path, pages, chunks, file_size, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, str(user_id), filename, file_path, pages, chunks, file_size, status, now_iso),
            )
            conn.commit()

        return DocumentRecord(
            id=document_id,
            user_id=str(user_id),
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
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (str(document_id),)).fetchone()
            if row:
                return DocumentRecord(**dict(row))
        return None

    def list_documents(self, user_id: Optional[str] = None) -> List[DocumentRecord]:
        if user_id:
            return self.list_documents_for_user(user_id)
        return self.list_all_documents()

    def list_documents_for_user(self, user_id: str) -> List[DocumentRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
                (str(user_id),),
            ).fetchall()
            return [DocumentRecord(**dict(row)) for row in rows]

    def list_all_documents(self) -> List[DocumentRecord]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
            return [DocumentRecord(**dict(row)) for row in rows]

    def delete_document(self, document_id: str, user_id: Optional[str] = None) -> bool:
        with self._get_connection() as conn:
            # Mark document as inactive in session bindings so sessions know a document was removed
            conn.execute("UPDATE chat_session_documents SET is_active = 0 WHERE document_id = ?", (str(document_id),))

            if user_id:
                cur = conn.execute(
                    "DELETE FROM documents WHERE id = ? AND user_id = ?",
                    (str(document_id), str(user_id)),
                )
            else:
                cur = conn.execute("DELETE FROM documents WHERE id = ?", (str(document_id),))
            conn.commit()
            return cur.rowcount > 0

    # =========================================================================
    # CHAT SESSIONS & MESSAGES REPOSITORY
    # =========================================================================

    def create_chat_session(
        self,
        user_id: str,
        title: str,
        document_ids: Optional[List[str]] = None,
    ) -> ChatSessionRecord:
        session_id = uuid.uuid4().hex[:12]
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, str(user_id), title.strip(), now_iso, now_iso),
            )
            if document_ids:
                for doc_id in document_ids:
                    conn.execute(
                        "INSERT OR IGNORE INTO chat_session_documents (session_id, document_id) VALUES (?, ?)",
                        (session_id, str(doc_id)),
                    )
            conn.commit()

        return ChatSessionRecord(
            id=session_id,
            user_id=str(user_id),
            title=title.strip(),
            created_at=now_iso,
            updated_at=now_iso,
        )

    def bind_session_documents(self, session_id: str, document_ids: List[str]):
        """Associates or updates the active document scope for a chat session."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chat_session_documents WHERE session_id = ?", (str(session_id),))
            for doc_id in document_ids:
                conn.execute(
                    "INSERT OR REPLACE INTO chat_session_documents (session_id, document_id, is_active) VALUES (?, ?, 1)",
                    (str(session_id), str(doc_id)),
                )
            conn.commit()

    def get_session_documents(self, session_id: str, active_only: bool = True) -> List[str]:
        """Retrieves list of document IDs bound to a chat session."""
        with self._get_connection() as conn:
            if active_only:
                rows = conn.execute(
                    """
                    SELECT csd.document_id 
                    FROM chat_session_documents csd
                    JOIN documents d ON csd.document_id = d.id
                    WHERE csd.session_id = ? AND csd.is_active = 1
                    """,
                    (str(session_id),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT document_id FROM chat_session_documents WHERE session_id = ?",
                    (str(session_id),),
                ).fetchall()
            return [str(r["document_id"]) for r in rows]

    def get_unavailable_documents_count(self, session_id: str) -> int:
        """Counts how many documents previously bound to this session have been deleted."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) as count 
                FROM chat_session_documents csd
                WHERE csd.session_id = ? AND (
                    csd.is_active = 0 OR csd.document_id NOT IN (SELECT id FROM documents)
                )
                """,
                (str(session_id),),
            ).fetchone()
            return int(row["count"]) if row else 0

    def rename_chat_session(self, session_id: str, user_id: str, new_title: str) -> Optional[ChatSessionRecord]:
        """Renames a chat session verifying user ownership."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (new_title.strip(), now_iso, str(session_id), str(user_id)),
            )
            conn.commit()
            if cur.rowcount > 0:
                return self.get_chat_session(session_id, user_id)
        return None

    def update_session_title_if_default(self, session_id: str, new_title: str) -> bool:
        """Updates session title if it currently has the default placeholder title."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE chat_sessions 
                SET title = ?, updated_at = ? 
                WHERE id = ? AND (title = 'New Conversation' OR title = '' OR title IS NULL)
                """,
                (new_title.strip(), now_iso, str(session_id)),
            )
            conn.commit()
            return cur.rowcount > 0

    def list_chat_sessions_for_user(self, user_id: str) -> List[ChatSessionRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                (str(user_id),),
            ).fetchall()
            return [ChatSessionRecord(**dict(row)) for row in rows]

    def list_chat_sessions_with_counts(self, user_id: str) -> List[Dict[str, Any]]:
        """Lists chat sessions for user with document_count and message_count in a single query."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT 
                    s.id,
                    s.user_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS message_count,
                    (SELECT COUNT(*) FROM chat_session_documents csd 
                     JOIN documents d ON csd.document_id = d.id 
                     WHERE csd.session_id = s.id AND csd.is_active = 1) AS document_count
                FROM chat_sessions s
                WHERE s.user_id = ?
                ORDER BY s.updated_at DESC
                """,
                (str(user_id),),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_chat_session(self, session_id: str, user_id: str) -> Optional[ChatSessionRecord]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
                (str(session_id), str(user_id)),
            ).fetchone()
            if row:
                return ChatSessionRecord(**dict(row))
        return None

    def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        with self._get_connection() as conn:
            # Delete session document links
            conn.execute(
                """
                DELETE FROM chat_session_documents WHERE session_id IN (
                    SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?
                )
                """,
                (str(session_id), str(user_id)),
            )
            # Delete messages
            conn.execute(
                """
                DELETE FROM messages WHERE session_id IN (
                    SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?
                )
                """,
                (str(session_id), str(user_id)),
            )
            cur = conn.execute(
                "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?",
                (str(session_id), str(user_id)),
            )
            conn.commit()
            return cur.rowcount > 0

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatMessageRecord:
        msg_id = uuid.uuid4().hex[:12]
        now_iso = datetime.now(timezone.utc).isoformat()
        sources_str = json.dumps(sources) if sources else None

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, session_id, role, content, sources_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, str(session_id), role, content, sources_str, now_iso),
            )
            # Update session timestamp
            conn.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (now_iso, str(session_id)),
            )
            conn.commit()

        return ChatMessageRecord(
            id=msg_id,
            session_id=str(session_id),
            role=role,
            content=content,
            sources=sources or [],
            created_at=now_iso,
        )

    def get_messages_for_session(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ChatMessageRecord]:
        with self._get_connection() as conn:
            query = "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC"
            params: list = [str(session_id)]
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            rows = conn.execute(query, tuple(params)).fetchall()

            messages: List[ChatMessageRecord] = []
            for r in rows:
                sources = json.loads(r["sources_json"]) if r["sources_json"] else []
                messages.append(
                    ChatMessageRecord(
                        id=r["id"],
                        session_id=r["session_id"],
                        role=r["role"],
                        content=r["content"],
                        sources=sources,
                        created_at=r["created_at"],
                    )
                )
            return messages


# Compatibility alias so existing imports of DocumentStore work seamlessly
DocumentStore = DatabaseManager
