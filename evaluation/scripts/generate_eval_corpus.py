"""
Evaluation Corpus Generator for DocuRAG / RAGMate Phase 12.
Generates 3 comprehensive 8-page academic research PDFs (24 pages total)
and indexes them into an isolated ChromaDB evaluation collection ('ragmate_eval_collection').
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure backend app imports are available
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

import pymupdf
from app.services.pdf_processor import PDFProcessor
from app.services.chunker import DocumentChunker, DocumentChunk
from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService

EVAL_COLLECTION_NAME = "ragmate_eval_collection"
CORPUS_DIR = root_dir / "evaluation" / "corpus"

DOCUMENTS_SPEC = [
    {
        "doc_id": "eval_doc_01",
        "filename": "rag_dense_retrieval.pdf",
        "title": "Dense Semantic Retrieval Architectures for Document Question Answering",
        "pages": [
            # Page 1: Abstract & Introduction
            "Dense Semantic Retrieval Architectures for Document Question Answering\n"
            "Authors: MCA Research Laboratory\n\n"
            "ABSTRACT\n"
            "Retrieval-Augmented Generation (RAG) integrates dense passage retrieval with "
            "pre-trained sequence-to-sequence language models to ground generative outputs on "
            "external, verifiable knowledge. We evaluate dense semantic retrieval architectures "
            "against traditional term-frequency indexing on the Stanford SQuAD and TriviaQA benchmarks. "
            "Our empirical experiments show that vanilla large language models suffer from a parametric "
            "hallucination rate of 38.2%. Combining dense passage retrieval with page-grounded context "
            "reduces factual hallucinations by 42.5% compared to ungrounded LLM baselines.\n\n"
            "1. INTRODUCTION & PROBLEM FORMULATION\n"
            "Standard large language models (LLMs) struggle with factual hallucinations and lack verifiable "
            "provenance when answering technical queries over private corpora. Traditional fine-tuning "
            "is computationally prohibitive and cannot easily accommodate dynamic document updates. "
            "Retrieval-Augmented Generation addresses these challenges by retrieving relevant text passages "
            "at query time, injecting them directly into the LLM context prompt.",

            # Page 2: Ingestion & PyMuPDF
            "2. DOCUMENT INGESTION & HIGH-THROUGHPUT EXTRACTION\n\n"
            "The document ingestion pipeline implements high-throughput PDF parsing coupled with rigorous "
            "text sanitation before chunking.\n\n"
            "2.1 High-Throughput PDF Extraction\n"
            "PDF extraction is performed using PyMuPDF (Python bindings for the MuPDF C-library), achieving "
            "a 15x parsing throughput advantage compared to pure-Python parsers such as PyPDF2. "
            "The extractor preserves exact 1-indexed page provenance for every extracted character block.\n\n"
            "2.2 Page Provenance & Font Handling\n"
            "During extraction, text blocks are tagged with exact bounding box coordinates and font size "
            "metadata, enabling accurate distinction between section headers and body paragraphs.",

            # Page 3: Text Sanitization Pipeline
            "3. SANITATION & TEXT REGULARIZATION\n\n"
            "Extracted text is preprocessed through a multi-pass normalization pipeline:\n\n"
            "3.1 Whitespace Regularization\n"
            "Multiple consecutive spaces, non-breaking spaces, horizontal tabs, and inconsistent line endings "
            "are converted to standardized single spaces and standard newline characters.\n\n"
            "3.2 Hyphenation Resolution\n"
            "Trailing hyphens at line breaks (hyphen-wrap) caused by column justification are recombined into single words.\n\n"
            "3.3 Control Code Filtering & Unicode Normalization\n"
            "Non-printable ASCII control characters (0x00 to 0x1F) are stripped, and text is converted to "
            "Unicode NFC canonical decomposition form to guarantee consistent embedding tokenization.",

            # Page 4: Recursive Chunking
            "4. RECURSIVE CHUNKING & SEPARATOR HIERARCHY\n\n"
            "Granular passage segmentation is crucial for dense vector retrieval accuracy.\n\n"
            "4.1 Target Window & Overlap\n"
            "We employ a recursive chunking strategy with a target window size of 1000 characters and a "
            "sliding overlap of 150 characters. The sliding window preserves semantic continuity across chunk boundaries.\n\n"
            "4.2 Separator Priority\n"
            "Text splitting respects a hierarchical separator priority:\n"
            "['\\n\\n', '\\n', '. ', '? ', '! ', '; ', ', ', ' ', '']\n"
            "This hierarchical splitting ensures syntactic cohesion while guaranteeing that sentence boundaries "
            "are preserved wherever possible without splitting numbers or acronyms.",

            # Page 5: Dense Bi-Encoder Embeddings
            "5. DENSE EMBEDDING GENERATION\n\n"
            "5.1 Bi-Encoder Model Architecture\n"
            "Each chunk is encoded into a 384-dimensional dense semantic vector space using the "
            "all-MiniLM-L6-v2 transformer model. The model features 6 transformer layers, 384 hidden dimensions, "
            "and 12 self-attention heads.\n\n"
            "5.2 L2 Normalization\n"
            "Embeddings are normalized using L2 unit norm (||v||_2 = 1.0). This mathematical normalization "
            "ensures that the inner dot product of any two embedding vectors equals their cosine similarity: "
            "cos(u, v) = u . v.",

            # Page 6: Vector Indexing & Baseline Benchmarks
            "6. VECTOR INDEXING & BASELINE RETRIEVAL PERFORMANCE\n\n"
            "Embeddings and chunk metadata are indexed in ChromaDB using Hierarchical Navigable Small World "
            "(HNSW) graph indexing with cosine distance space: D(u, v) = 1 - (u . v) / (||u|| ||v||).\n\n"
            "6.1 Latency Benchmarks\n"
            "Vector similarity search demonstrates an average query latency of 45.2ms when retrieving candidate "
            "pools of size K = 15 over indexed collections.\n\n"
            "6.2 Retrieval Baseline Results\n"
            "On a test set of technical queries, baseline vector-only retrieval achieves a Hit Rate@5 of 82.0% "
            "and a Mean Reciprocal Rank (MRR) of 0.714. However, dense bi-encoder embeddings occasionally fail "
            "on subtle keyword distinctions.",

            # Page 7: Chunk Size Ablation
            "7. ABLATION STUDY: CHUNK SIZE AND OVERLAP\n\n"
            "We systematically evaluated chunk sizes of 500, 1000, and 1500 characters on retrieval performance:\n"
            "1. 500-character chunks: High precision but fragmented context, reducing downstream Gemini synthesis quality.\n"
            "2. 1000-character chunks: Optimal empirical balance, achieving 82.0% Hit Rate@5 while retaining full conceptual sentences.\n"
            "3. 1500-character chunks: Caused embedding vector dilution where key facts were overshadowed by peripheral sentences.\n"
            "An overlap of 150 characters eliminated boundary information loss across adjacent chunks.",

            # Page 8: Vector Search Limitations
            "8. LIMITATIONS OF SINGLE-STAGE VECTOR RETRIEVAL\n\n"
            "Detailed failure analysis of vector search reveals three primary vulnerability modes:\n"
            "1. Lexical Specificity Failure: Queries with rare identifiers or version numbers receive lower similarity scores.\n"
            "2. Negation Blindness: Bi-encoders frequently map 'system X supports Y' and 'system X does not support Y' to near-identical vectors.\n"
            "3. Polysemy Confusion: Technical terms with multiple contextual meanings across documents lead to spurious candidate retrieval."
        ]
    },
    {
        "doc_id": "eval_doc_02",
        "filename": "neural_reranking_systems.pdf",
        "title": "Cross-Encoder Neural Reranking for Precision Evidence Selection",
        "pages": [
            # Page 1: Motivation & Two-Stage Paradigm
            "Cross-Encoder Neural Reranking for Precision Evidence Selection\n"
            "Authors: MCA Research Laboratory\n\n"
            "ABSTRACT\n"
            "First-stage dense vector retrieval maps queries and documents into isolated vector representations, "
            "losing fine-grained inter-token interactions. Two-stage retrieval pairs high-recall bi-encoders with "
            "a cross-encoder reranker to reorder candidates based on full self-attention. We evaluate the "
            "cross-encoder/ms-marco-MiniLM-L-6-v2 model on technical document collections. Cross-encoder "
            "reranking improves Mean Reciprocal Rank (MRR) by +21.1% over vector-only baselines.\n\n"
            "1. THE TWO-STAGE RETRIEVAL PARADIGM\n"
            "Bi-encoder architectures optimize for search latency at the expense of semantic precision. "
            "Because queries and passages are embedded independently, query-document token interactions are "
            "compressed into a single dot product. Cross-encoders overcome this bottleneck by performing full "
            "cross-attention across all query and passage tokens simultaneously.",

            # Page 2: Cross-Encoder Architecture & Scoring
            "2. CROSS-ENCODER ARCHITECTURE & CALIBRATION\n\n"
            "2.1 Transformer Cross-Encoder Model\n"
            "We employ cross-encoder/ms-marco-MiniLM-L-6-v2, fine-tuned on the Microsoft MS-MARCO passage "
            "ranking dataset. The model accepts concatenated query and passage sequences [CLS] query [SEP] passage [SEP].\n\n"
            "2.2 Sigmoid Relevance Score Calibration\n"
            "The model outputs an unconstrained scalar logit z in (-infinity, +infinity). To provide human-interpretable "
            "relevance probabilities and ensure consistency with vector similarity scales, logits are calibrated via "
            "the standard logistic sigmoid function:\n"
            "sigma(z) = 1 / (1 + exp(-z))\n"
            "This maps raw scores monotonically into the bounded interval [0.0, 1.0]. A score of 0.85 indicates "
            "strong contextual relevance, whereas scores below 0.30 denote non-relevant candidates.",

            # Page 3: Comparison Intent Detection
            "3. COMPARISON INTENT DETECTION & QUERY PARSING\n\n"
            "3.1 Deterministic Intent Detection\n"
            "When users ask comparative questions across multiple documents, conventional retrieval often suffers "
            "from single-document dominance. We implement deterministic regex intent detection that monitors for "
            "comparative tokens including 'compare', 'versus', 'difference', 'contrast', 'distinguish', and 'between'.\n\n"
            "3.2 Zero-Latency Classification\n"
            "Unlike LLM-based query intent classifiers that introduce 300ms to 600ms latency, deterministic regex token "
            "matching executes in sub-microsecond time (0.01ms), adding zero overhead to the retrieval pipeline.",

            # Page 4: Source-Aware Round-Robin Balancing
            "4. MULTI-DOCUMENT SOURCE BALANCING ALGORITHM\n\n"
            "4.1 Source Starvation Mitigation\n"
            "In multi-document comparison queries, one dense document may monopolize all top K candidate slots. "
            "To solve this, our retrieval orchestrator partitions candidates by document ID.\n\n"
            "4.2 Round-Robin Interleaving\n"
            "When comparison intent is active, candidate chunks are selected via round-robin allocation:\n"
            "doc1_chunk0, doc2_chunk0, doc1_chunk1, doc2_chunk1.\n"
            "This ensures that both documents receive balanced representation in the prompt context presented to Gemini.",

            # Page 5: Empirical Reranking Latency & Performance
            "5. QUANTITATIVE RERANKING BENCHMARKS & LATENCY\n\n"
            "5.1 Latency Profile\n"
            "Cross-encoder scoring on candidate pools of size N = 15 adds an average of 185.4ms latency on modern "
            "multi-core CPUs. To prevent quadratic O(N^2) token attention bottlenecks, passage texts are truncated "
            "to 1000 characters prior to reranking.\n\n"
            "5.2 Retrieval Performance Comparison\n"
            "Reranking candidate pools down to top K = 5 elevates the Hit Rate@5 from 82.0% to 94.0%. "
            "Mean Reciprocal Rank (MRR) increases from 0.714 to 0.865, representing a +21.1% relative gain. "
            "The reranker effectively pushes relevant but low-similarity passages to top ranks.",

            # Page 6: Candidate Pool Size Ablation
            "6. ABLATION STUDY: CANDIDATE POOL SIZE (N)\n\n"
            "We investigated the effect of varying first-stage candidate pool size N in [5, 10, 15, 20, 30]:\n"
            "1. N = 5: Insufficient recall; reranker cannot recover relevant passages missed by the bi-encoder.\n"
            "2. N = 15: Optimal sweet spot; achieves 96.2% candidate recall with 185.4ms CPU reranking time.\n"
            "3. N = 30: Diminishing returns; marginal +0.8% recall gain accompanied by latency doubling to 370ms.",

            # Page 7: Hardware & Quantization Benchmarks
            "7. HARDWARE ACCELERATION & MODEL OPTIMIZATION\n\n"
            "We benchmarked cross-encoder inference across multiple execution runtimes:\n"
            "1. PyTorch CPU (FP32): 185.4ms average latency for 15 candidate pairs.\n"
            "2. ONNX Runtime CPU (INT8 Quantization): 58.2ms average latency, representing a 3.2x speedup with <0.005 score degradation.\n"
            "3. CUDA GPU (FP16): 22.1ms average latency, optimal for high-throughput batch evaluation.",

            # Page 8: Failure Modes of Cross-Encoder Reranking
            "8. ERROR ANALYSIS OF RERANKING FAILURES\n\n"
            "Cross-encoder reranking failures primarily occur under two conditions:\n"
            "1. Candidate Truncation: Long technical definitions exceeding 1000 characters have critical conclusions clipped.\n"
            "2. Semantic False Friends: Passages with high lexical overlap but contradictory semantic assertions can receive inflated cross-encoder scores."
        ]
    },
    {
        "doc_id": "eval_doc_03",
        "filename": "llm_grounding_and_hallucination.pdf",
        "title": "Hallucination Mitigation and Verifiable Attribution in Generative Q&A",
        "pages": [
            # Page 1: Taxonomy of LLM Hallucinations
            "Hallucination Mitigation and Verifiable Attribution in Generative Q&A\n"
            "Authors: MCA Research Laboratory\n\n"
            "ABSTRACT\n"
            "Large language model generation in academic and enterprise contexts demands verifiable factual "
            "grounding. We propose an attribution framework featuring deterministic bracketed citations, "
            "provenance validation, and out-of-domain abstention mechanisms. Empirical analysis reveals that "
            "78% of ungrounded LLM answers on technical domains contain at least one unsupported assertion. "
            "Our grounded citation framework achieves a 92.4% faithfulness rate with verifiable attribution.\n\n"
            "1. TAXONOMY OF GENERATIVE HALLUCINATIONS\n"
            "We categorize hallucinations into two distinct failure modes:\n"
            "1. Intrinsic Hallucinations: Generated statements that directly contradict facts presented in the retrieved context.\n"
            "2. Extrinsic Hallucinations: Generated statements introducing external claims that cannot be verified from the retrieved context.",

            # Page 2: In-Text Citations & Provenance
            "2. IN-TEXT CITATIONS & PROVENANCE VERIFICATION\n\n"
            "2.1 Granular Bracketed Citation Format\n"
            "Generative answers cite context sources using inline bracketed notation, such as [1], [2], or [1, 2]. "
            "Each citation corresponds to a verified CitationSource entity tracking parent document ID, filename, "
            "source page number, and chunk ID.\n\n"
            "2.2 Interactive Evidence Linking\n"
            "The web interface displays clickable citation chips that trigger the Document Evidence Drawer, "
            "allowing reviewers to view exact source sentences highlighted directly in the document page.",

            # Page 3: Citation Sanitization Algorithm
            "3. CITATION SANITIZATION ALGORITHM\n\n"
            "3.1 Hallucination Pruning\n"
            "To prevent citation hallucination, answers undergo deterministic regex sanitization. Any hallucinated "
            "citation numbers (e.g. citing [999] when only sources [1..4] were provided) are pruned.\n\n"
            "3.2 Punctuation Regularization\n"
            "Pruning citations can leave dangling punctuation or whitespace (e.g., 'model is fast .'). The sanitizer "
            "normalizes space preceding punctuation marks to ensure syntactically valid sentences.",

            # Page 4: Abstention Mechanism & Thresholding
            "4. ABSTENTION MECHANISM & OUT-OF-DOMAIN DETECTION\n\n"
            "4.1 Minimum Similarity Threshold\n"
            "To prevent answering questions when no relevant evidence exists, we enforce a minimum cosine similarity "
            "threshold of 0.15. Chunks scoring below 0.15 are rejected as non-relevant noise.\n\n"
            "4.2 Explicit Abstention Response\n"
            "When the retrieved candidate pool is empty or evidence is insufficient, the system triggers a strict "
            "abstention response:\n"
            "'I could not find sufficient information in the selected documents to answer this question.'\n"
            "This abstention mechanism prevents the LLM from fabricating speculative answers on out-of-domain queries.",

            # Page 5: Context Budgeting & Saturation
            "5. CONTEXT BUDGETING & SATURATION PREVENTION\n\n"
            "5.1 Context Window Budgeting\n"
            "Retrieved context is bounded by a strict character budget of 12,000 characters. Passages are truncated "
            "if necessary to ensure prompts remain well within model context limits and prevent attention degradation.\n\n"
            "5.2 Prompt Grounding Rules\n"
            "System prompts explicitly instruct Gemini to rely exclusively on supplied snippets and reject prior "
            "parametric assumptions when contradictory facts appear in the text.",

            # Page 6: End-to-End Latency Profile
            "6. END-TO-END LATENCY PROFILE & FAITHFULNESS\n\n"
            "6.1 Latency Component Breakdown\n"
            "Generation using Google Gemini averages 1,120ms latency. The complete RAG pipeline achieves an average "
            "end-to-end response time of 1,350ms (45ms vector search + 185ms reranking + 1,120ms generation).\n\n"
            "6.2 Faithfulness Evaluation\n"
            "Human evaluation confirms a 92.4% factual faithfulness score with zero critical unsupported assertions "
            "across 100 benchmark queries.",

            # Page 7: Refusal Threshold Sensitivity
            "7. ABLATION STUDY: REFUSAL THRESHOLD SENSITIVITY\n\n"
            "We evaluated similarity thresholds tau in [0.10, 0.15, 0.20, 0.25] for abstention accuracy:\n"
            "1. tau = 0.10: Too permissive; false positives allowed hallucinated answers on unanswerable queries.\n"
            "2. tau = 0.15: Optimal threshold; maximized F1-score for abstention, yielding 95.0% precision on out-of-domain queries.\n"
            "3. tau = 0.25: Too aggressive; falsely rejected legitimate paraphrased queries on known document topics.",

            # Page 8: User Study & Verification Efficiency
            "8. USER VERIFICATION EFFICIENCY STUDY\n\n"
            "A controlled study with 50 academic evaluators assessed citation verification speed:\n"
            "1. Without interactive citations: Reviewers required an average of 42.0 seconds to verify claims across PDF files.\n"
            "2. With interactive inline chips and page drawers: Verification time dropped to 6.5 seconds per claim (6.4x speedup).\n"
            "User trust scores increased by 84% when verifiable page-grounded citations were visible."
        ]
    }
]


def generate_pdf(doc_spec: Dict[str, Any], output_path: Path) -> Path:
    """Generates a multi-page PDF document using PyMuPDF."""
    doc = pymupdf.open()
    for page_idx, page_content in enumerate(doc_spec["pages"]):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 72), page_content, fontsize=10.5, fontname="helv")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    return output_path


def build_evaluation_corpus() -> Dict[str, List[DocumentChunk]]:
    """
    Generates the PDFs and chunks them using DocumentChunker,
    indexing them into the isolated evaluation ChromaDB collection.
    """
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    processor = PDFProcessor()
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=150)
    embedding_service = EmbeddingService()
    
    vector_store = VectorStore(collection_name=EVAL_COLLECTION_NAME, embedding_service=embedding_service)
    
    all_doc_chunks: Dict[str, List[DocumentChunk]] = {}
    
    print("=" * 70)
    print("  PHASE 12: GENERATING 24-PAGE EVALUATION CORPUS & INDEXING")
    print(f"  Target Collection: {EVAL_COLLECTION_NAME}")
    print("=" * 70)

    for doc_spec in DOCUMENTS_SPEC:
        doc_id = doc_spec["doc_id"]
        filename = doc_spec["filename"]
        pdf_path = CORPUS_DIR / filename
        
        print(f"\n[1] Generating PDF: {filename} ({len(doc_spec['pages'])} pages)...")
        generate_pdf(doc_spec, pdf_path)
        
        print(f"[2] Extracting with PDFProcessor...")
        extracted_doc = processor.extract_document(str(pdf_path))
        
        print(f"[3] Chunking with DocumentChunker (size=1000, overlap=150)...")
        chunks = chunker.chunk_document(extracted_doc, document_id=doc_id)
        all_doc_chunks[doc_id] = chunks
        
        print(f"    -> Created {len(chunks)} chunks for {doc_id} ({filename})")
        for c in chunks:
            print(f"       Chunk ID: {c.chunk_id:25} | Page: {c.page_number} | Chars: {c.char_count:4} | Snippet: {c.text[:55]}...")
            
        print(f"[4] Indexing into ChromaDB collection '{EVAL_COLLECTION_NAME}'...")
        vector_store.delete_document(doc_id)
        added = vector_store.add_chunks(chunks)
        print(f"    -> Ingested {added} chunks into vector store.")

    total_chunks = sum(len(c) for c in all_doc_chunks.values())
    print("\n" + "=" * 70)
    print(f"  CORPUS GENERATION COMPLETE: 3 Documents, {total_chunks} Total Chunks.")
    print("=" * 70)
    return all_doc_chunks


if __name__ == "__main__":
    build_evaluation_corpus()
