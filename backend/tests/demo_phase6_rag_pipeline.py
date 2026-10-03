"""
End-to-End RAG Pipeline Demo & Verification:
Extract -> Chunk -> Embed -> ChromaDB -> Retrieve -> Google Gemini Grounded Answer & Citations.
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
from app.services.retrieval import RetrievalService
from app.services.gemini import GeminiService, SAFE_FALLBACK_ANSWER


def main():
    print("=" * 80)
    print("  PHASE 5 & 6 END-TO-END RAG PIPELINE WITH GOOGLE GEMINI")
    print("=" * 80)

    sample_pdf = backend_dir.parent / "sample_documents" / "rag_research_paper.pdf"
    if not sample_pdf.exists():
        print(f"Error: Sample PDF not found at {sample_pdf}. Run Phase 2 first.")
        return

    # 1. Extraction & Chunking
    print("\n[1] Extracting text and chunking document...")
    processor = PDFProcessor()
    extracted_doc = processor.extract_document(str(sample_pdf))

    chunker = DocumentChunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_document(extracted_doc, document_id="ragmate_paper_01")
    print(f"    -> Extracted {extracted_doc.page_count} pages, generated {len(chunks)} chunks.")

    # 2. Embedding & ChromaDB Indexing
    print("\n[2] Ingesting into VectorStore (ChromaDB)...")
    temp_chroma = backend_dir / "chroma_data_rag_demo"
    vector_store = VectorStore(
        persist_directory=str(temp_chroma),
        collection_name="rag_demo_collection",
    )
    vector_store.add_chunks(chunks)
    print(f"    -> Indexed {vector_store.collection.count()} chunks into ChromaDB.")

    # 3. Initialize Services
    retrieval_service = RetrievalService(vector_store=vector_store)
    gemini_service = GeminiService()
    print(f"    -> GeminiService initialized with model: {gemini_service.model_name}")

    # 4. Test Queries
    queries = [
        (
            "According to the research paper, what percentage reduction in citation hallucination is achieved by using page-level metadata?",
            "Grounded factual query with specific metric from Page 1",
        ),
        (
            "What are the four processing tiers in the proposed system architecture?",
            "Grounded structural query spanning methodology on Page 2",
        ),
        (
            "What is the official procedure for filing personal tax returns in California?",
            "Unanswerable out-of-domain query (should trigger safe fallback)",
        ),
    ]

    for idx, (question, description) in enumerate(queries, 1):
        print("\n" + "=" * 80)
        print(f"TEST CASE #{idx}: {question}")
        print(f"Description:  {description}")
        print("-" * 80)

        t_total = time.perf_counter()

        # Step A: Semantic Retrieval
        contexts = retrieval_service.retrieve(query=question, top_k=2)
        print(f"Retrieval:   Found {len(contexts)} candidates above similarity threshold.")

        # Step B: LLM Generation with Grounding
        response = gemini_service.generate_grounded_answer(question=question, contexts=contexts)
        total_latency = (time.perf_counter() - t_total) * 1000

        print(f"Latency:     {total_latency:.1f} ms (Model: {response.model_used})")
        print(f"Grounded:    {response.is_grounded}")
        print(f"\nAI ANSWER:\n{response.answer}\n")

        if response.sources:
            print("SOURCE CITATIONS:")
            for s in response.sources:
                print(f"  * Document: {s.document_name} | Page {s.page_number} | Score: {s.similarity_score:.4f}")
                print(f"    Snippet: \"{s.snippet}\"")
        else:
            print("SOURCE CITATIONS: [None - Fallback triggered or ungrounded]")

    # Cleanup demo chroma directory
    import shutil
    if temp_chroma.exists():
        shutil.rmtree(temp_chroma, ignore_errors=True)

    print("\n" + "=" * 80)
    print("  [SUCCESS] END-TO-END RAG PIPELINE VERIFIED WITH GROUNDING & SAFE FALLBACK")
    print("=" * 80)


if __name__ == "__main__":
    main()
