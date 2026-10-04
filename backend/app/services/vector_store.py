import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel, Field

from app.config import settings
from app.services.chunker import DocumentChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger("ragmate.vector_store")


class SearchResult(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    document_name: str = Field(..., description="Parent document name")
    page_number: int = Field(..., description="1-indexed source page number")
    text: str = Field(..., description="Text content of the retrieved chunk")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    rerank_score: Optional[float] = Field(None, description="Cross-encoder relevance score (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Complete chunk metadata")


class VectorStore:
    """
    Persistent ChromaDB vector database manager for document chunks.
    Supports chunk addition, cascade deletion, semantic similarity search, and multi-tenant metadata filtering.
    """

    DEFAULT_COLLECTION_NAME = "ragmate_documents"

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or self.DEFAULT_COLLECTION_NAME
        self.embedding_service = embedding_service or EmbeddingService()

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        logger.info(
            "Initializing ChromaDB PersistentClient at directory: %s",
            self.persist_directory,
        )
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Get or create collection configured for cosine distance
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' active with %d existing entries",
            self.collection_name,
            self.collection.count(),
        )

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: Optional[List[List[float]]] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """
        Inserts or updates document chunks in the ChromaDB collection.
        Automatically generates embeddings if not provided.
        """
        if not chunks:
            return 0

        # Generate embeddings if needed
        if embeddings is None:
            logger.info("Computing embeddings for %d chunks...", len(chunks))
            chunk_texts = [c.text for c in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks provided but received {len(embeddings)} embeddings."
            )

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.text)

            meta = dict(chunk.metadata)
            meta["document_id"] = str(chunk.document_id)
            meta["document_name"] = str(chunk.document_name)
            meta["page_number"] = int(chunk.page_number)
            meta["chunk_id"] = str(chunk.chunk_id)
            if user_id:
                meta["user_id"] = str(user_id)

            metadatas.append(meta)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(
            "Upserted %d chunks into collection '%s' (Total chunks now: %d)",
            len(chunks),
            self.collection_name,
            self.collection.count(),
        )
        return len(chunks)

    def delete_document(self, document_id: str) -> int:
        """
        Removes all vector embeddings and chunks associated with a document_id.
        Ensures vector store consistency when a document is deleted.
        """
        doc_id_str = str(document_id)
        # Find all chunk IDs for this document
        existing = self.collection.get(
            where={"document_id": doc_id_str},
            include=["metadatas"],
        )
        chunk_ids = existing.get("ids", [])

        if chunk_ids:
            self.collection.delete(ids=chunk_ids)
            logger.info(
                "Deleted %d chunks for document_id '%s' from ChromaDB",
                len(chunk_ids),
                doc_id_str,
            )
            return len(chunk_ids)

        logger.info("No chunks found in ChromaDB for document_id '%s'", doc_id_str)
        return 0

    def get_document_chunk_count(self, document_id: str) -> int:
        """Returns the number of chunks stored in ChromaDB for a given document."""
        existing = self.collection.get(
            where={"document_id": str(document_id)},
            include=[],
        )
        return len(existing.get("ids", []))

    def similarity_search(
        self,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        document_ids: Optional[List[Union[str, int]]] = None,
        user_id: Optional[Union[str, int]] = None,
        min_similarity: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Performs semantic cosine similarity search over stored document chunks.
        Supports single-document, multi-document, and user-tenant filtering.
        """
        if self.collection.count() == 0:
            logger.warning("Vector store is empty. No chunks to retrieve.")
            return []

        # Derive query embedding if not provided
        if query_embedding is None:
            if not query_text or not query_text.strip():
                raise ValueError("Either query_text or query_embedding must be provided.")
            query_embedding = self.embedding_service.embed_query(query_text)

        # Build metadata filter
        where_filter: Optional[Dict[str, Any]] = None
        filter_clauses: List[Dict[str, Any]] = []

        if document_ids:
            str_doc_ids = [str(d) for d in document_ids if d]
            if len(str_doc_ids) == 1:
                filter_clauses.append({"document_id": str_doc_ids[0]})
            elif len(str_doc_ids) > 1:
                filter_clauses.append({"document_id": {"$in": str_doc_ids}})

        if user_id:
            filter_clauses.append({"user_id": str(user_id)})

        if len(filter_clauses) == 1:
            where_filter = filter_clauses[0]
        elif len(filter_clauses) > 1:
            where_filter = {"$and": filter_clauses}

        # Query ChromaDB collection
        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self.collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        search_results: List[SearchResult] = []

        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for chunk_id, doc_text, metadata, distance in zip(
            ids_list, docs_list, metas_list, dists_list
        ):
            # For cosine space: distance is (1 - cosine_similarity)
            similarity = max(0.0, min(1.0, 1.0 - float(distance)))

            if min_similarity is not None and similarity < min_similarity:
                continue

            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    document_id=str(metadata.get("document_id", "")),
                    document_name=str(metadata.get("document_name", "")),
                    page_number=int(metadata.get("page_number", 1)),
                    text=doc_text,
                    similarity_score=round(similarity, 4),
                    metadata=metadata,
                )
            )

        logger.info(
            "Similarity search completed: retrieved %d candidate chunks (top_k=%d)",
            len(search_results),
            top_k,
        )
        return search_results
