"""
Standalone local verification script for Phase 2:
PDF Text Extraction, Cleaning, Page Provenance, and Configurable Chunking.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app imports resolve
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pymupdf
from app.services.pdf_processor import PDFProcessor
from app.services.chunker import DocumentChunker


def generate_sample_research_paper(destination: Path) -> Path:
    """Generates a realistic 3-page academic paper PDF for demonstration."""
    doc = pymupdf.open()

    # Page 1: Abstract and Introduction
    p1 = doc.new_page(width=595, height=842)
    p1_text = (
        "RAGMate Academic Research Report: Dense Retrieval Architectures\n"
        "Authors: MCA Research Laboratory\n\n"
        "ABSTRACT\n"
        "Retrieval-Augmented Generation (RAG) integrates dense passage retrieval with "
        "pre-trained sequence-to-sequence language models to ground generative outputs on "
        "external, verifiable knowledge. In this work, we analyze the performance of "
        "bi-encoder semantic embeddings combined with hierarchical text chunking. "
        "Our experiments indicate that maintaining granular page-level metadata reduces "
        "citation hallucination by over 40% compared to non-grounded benchmarks.\n\n"
        "1. INTRODUCTION\n"
        "Standard large language models (LLMs) struggle with factual hallucinations and "
        "lack verifiable provenance when querying non-public documents. Traditional "
        "methods rely on fine-tuning, which is computationally expensive and inflexible "
        "to continuously updated corpora. Retrieval-Augmented Generation circumvents these "
        "limitations by retrieving relevant knowledge chunks at query time."
    )
    p1.insert_text((50, 72), p1_text, fontsize=11)

    # Page 2: Architecture and Methodology
    p2 = doc.new_page(width=595, height=842)
    p2_text = (
        "2. SYSTEM ARCHITECTURE & METHODOLOGY\n\n"
        "The proposed architecture consists of four distinct processing tiers:\n"
        "1. Document Ingestion: Arbitrary multi-page PDF documents are ingested and parsed "
        "using high-performance C-level bindings via PyMuPDF.\n"
        "2. Page-level Text Normalization: Whitespace is regularized, hyphenated line breaks "
        "are resolved, and control characters are stripped.\n"
        "3. Recursive Chunking: Cleaned text is partitioned into overlapping windows of size "
        "800 to 1200 characters with 150-character sliding overlap.\n"
        "4. Dense Semantic Embedding: Each chunk is encoded into a 384-dimensional vector "
        "space using the all-MiniLM-L6-v2 transformer model.\n\n"
        "Vector indexing is performed in ChromaDB, enabling sub-10ms nearest neighbor search "
        "using cosine similarity metrics over indexed document subsets."
    )
    p2.insert_text((50, 72), p2_text, fontsize=11)

    # Page 3: Evaluation and Conclusion
    p3 = doc.new_page(width=595, height=842)
    p3_text = (
        "3. EXPERIMENTAL EVALUATION\n\n"
        "We evaluated retrieval efficacy across three paradigms: Keyword BM25, Dense Semantic "
        "Retrieval, and Dense Retrieval with Cross-Encoder Reranking. The benchmark dataset "
        "comprises 100 manually verified technical queries with exact ground-truth passage annotations.\n\n"
        "Results show that Cross-Encoder Reranking improves Mean Reciprocal Rank (MRR) from "
        "0.74 to 0.89 while maintaining acceptable generation latency under 850ms.\n\n"
        "4. CONCLUSION & FUTURE WORK\n"
        "Page-grounded RAG provides an academically sound, hallucination-resistant architecture "
        "for document question answering. Future work will investigate hybrid dense-sparse indexing "
        "and agentic multi-hop document reasoning."
    )
    p3.insert_text((50, 72), p3_text, fontsize=11)

    destination.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(destination))
    doc.close()
    return destination


def main():
    print("=" * 75)
    print("  PHASE 2 LOCAL VERIFICATION: PDF EXTRACTION & CHUNKING PIPELINE")
    print("=" * 75)

    sample_pdf_path = backend_dir.parent / "sample_documents" / "rag_research_paper.pdf"
    print(f"\n[1] Generating sample academic PDF at:\n    {sample_pdf_path}")
    generate_sample_research_paper(sample_pdf_path)
    print("    -> PDF successfully generated with 3 pages.")

    print("\n[2] Initializing PDFProcessor...")
    processor = PDFProcessor(max_file_size_mb=25)

    extracted_doc = processor.extract_document(str(sample_pdf_path))
    print(f"    -> Extracted Document: {extracted_doc.filename}")
    print(f"    -> Total Pages:        {extracted_doc.page_count}")
    print(f"    -> Total Characters:   {extracted_doc.total_characters}")
    print(f"    -> Total Words:        {extracted_doc.total_words}")

    print("\n--- Page Summary ---")
    for page in extracted_doc.pages:
        print(f"  Page {page.page_number}: {page.word_count} words | {page.char_count} chars")
        preview = page.text[:120].replace("\n", " ")
        print(f"    Preview: \"{preview}...\"\n")

    print("[3] Initializing DocumentChunker (chunk_size=400, chunk_overlap=80)...")
    chunker = DocumentChunker(chunk_size=400, chunk_overlap=80)
    chunks = chunker.chunk_document(extracted_doc, document_id="demo_doc_001")

    print(f"    -> Generated {len(chunks)} chunks across {extracted_doc.page_count} pages.\n")
    print("=" * 75)
    print(f"{'Chunk ID':<22} | {'Page':<5} | {'Length':<6} | Preview")
    print("-" * 75)
    for c in chunks:
        text_preview = c.text[:45].replace("\n", " ")
        print(f"{c.chunk_id:<22} | {c.page_number:<5} | {c.char_count:<6} | {text_preview}...")

    print("=" * 75)
    print("\n[4] Metadata Verification on Chunk #0:")
    for k, v in chunks[0].metadata.items():
        print(f"    {k:<20}: {v}")

    print("\n[SUCCESS] Phase 2 PDF Extraction and Chunking verified end-to-end!")


if __name__ == "__main__":
    main()
