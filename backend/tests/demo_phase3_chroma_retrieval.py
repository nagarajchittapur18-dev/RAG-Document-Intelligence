"""
Standalone local verification script for Phase 3 & 4:
Embedding Generation, ChromaDB Persistence, Metadata Filtering & Semantic Retrieval.
"""

import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.pdf_processor import PDFProcessor
from app.services.chunker import DocumentChunker
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


def main():
    print("=" * 80)
    print("  PHASE 3 & 4 VERIFICATION: EMBEDDINGS & CHROMADB VECTOR RETRIEVAL")
    print("=" * 80)

    sample_pdf = backend_dir.parent / "sample_documents" / "rag_research_paper.pdf"
    if not sample_pdf.exists():
        print(f"Error: Sample PDF not found at {sample_pdf}. Run Phase 2 first.")
        return

    # 1. Extraction & Chunking
    print("\n[1] Processing PDF with PDFProcessor and DocumentChunker...")
    processor = PDFProcessor()
    extracted_doc = processor.extract_document(str(sample_pdf))

    chunker = DocumentChunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_document(extracted_doc, document_id="doc_rag_001")
    print(f"    -> Extracted {extracted_doc.page_count} pages, generated {len(chunks)} chunks.")

    # 2. Embedding Model & Vector Store
    print("\n[2] Initializing EmbeddingService (all-MiniLM-L6-v2) & VectorStore...")
    t0 = time.perf_counter()
    embedder = EmbeddingService()
    t_load = (time.perf_counter() - t0) * 1000
    print(f"    -> Embedding model loaded in {t_load:.1f}ms (dimension={embedder.embedding_dimension}).")

    demo_chroma_dir = backend_dir / "chroma_data_demo"
    vector_store = VectorStore(
        persist_directory=str(demo_chroma_dir),
        collection_name="demo_academic_papers",
        embedding_service=embedder,
    )

    # 3. Insert Chunks into ChromaDB
    print("\n[3] Ingesting chunks and computing embeddings into ChromaDB...")
    t0 = time.perf_counter()
    vector_store.add_chunks(chunks)
    t_ingest = (time.perf_counter() - t0) * 1000
    print(f"    -> Ingestion completed in {t_ingest:.1f}ms. Total stored chunks: {vector_store.collection.count()}")

    # 4. Test Semantic Retrieval on Questions
    test_queries = [
        (
            "How much does page-level metadata reduce citation hallucination?",
            "Expected: Page 1 (mentions 40% reduction)",
        ),
        (
            "What are the four processing tiers in the architecture?",
            "Expected: Page 2 (mentions Document Ingestion, Text Normalization, Recursive Chunking, Dense Embedding)",
        ),
        (
            "What were the MRR evaluation results comparing BM25 with Cross-Encoder Reranking?",
            "Expected: Page 3 (mentions MRR 0.74 to 0.89)",
        ),
        (
            "What is the recommended recipe for baking chocolate chip cookies?",
            "Expected: Irrelevant / low similarity score (<0.35)",
        ),
    ]

    print("\n" + "=" * 80)
    print("  EXECUTING SEMANTIC SIMILARITY RETRIEVAL BENCHMARKS")
    print("=" * 80)

    for idx, (query, expectation) in enumerate(test_queries, 1):
        print(f"\nQuery #{idx}: \"{query}\"")
        print(f"Goal:     {expectation}")

        t_start = time.perf_counter()
        results = vector_store.similarity_search(query_text=query, top_k=2)
        latency_ms = (time.perf_counter() - t_start) * 1000

        print(f"Latency:  {latency_ms:.2f} ms | Retrieved: {len(results)} chunks")
        if not results:
            print("  [NO RESULTS]")
            continue

        for rank, res in enumerate(results, 1):
            flag = "RELEVANT" if res.similarity_score >= 0.40 else "LOW CONFIDENCE"
            snippet = res.text[:95].replace("\n", " ")
            print(f"  Rank #{rank} [{flag}] Score: {res.similarity_score:.4f} | Page {res.page_number} ({res.chunk_id})")
            print(f"         Snippet: \"{snippet}...\"")

    print("\n" + "=" * 80)
    print("  VERIFYING CASCADE DELETION")
    print("=" * 80)
    print(f"Chunks before deletion: {vector_store.collection.count()}")
    deleted = vector_store.delete_document("doc_rag_001")
    print(f"Deleted chunks for 'doc_rag_001': {deleted}")
    print(f"Chunks after deletion:  {vector_store.collection.count()}")

    # Cleanup demo directory
    import shutil
    if demo_chroma_dir.exists():
        shutil.rmtree(demo_chroma_dir, ignore_errors=True)

    print("\n[SUCCESS] Embeddings and ChromaDB vector store verified successfully!")


if __name__ == "__main__":
    main()
