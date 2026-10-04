"""
Creates the academic MCA evaluation benchmark dataset (60 verified questions).
Exports both JSON and CSV versions to evaluation/dataset/.
"""

import json
import csv
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

QUESTIONS = [
    # --- Type 1: Direct Factual Questions (Q001 - Q012) ---
    {
        "id": "Q001",
        "question": "What is the vector dimension produced by the embedding model?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_01_p5_c0"],
        "reference_answer": "The all-MiniLM-L6-v2 model encodes text chunks into a 384-dimensional dense semantic vector space.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q002",
        "question": "What is the parsing throughput advantage of PyMuPDF compared to PyPDF2?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [2],
        "expected_chunk_ids": ["doc_eval_doc_01_p2_c0"],
        "reference_answer": "PyMuPDF achieves a 15x parsing throughput advantage compared to pure-Python parsers like PyPDF2.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q003",
        "question": "What target window size and sliding overlap are used for recursive chunking?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [4],
        "expected_chunk_ids": ["doc_eval_doc_01_p4_c0"],
        "reference_answer": "Recursive chunking employs a target window size of 1000 characters with a sliding overlap of 150 characters.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q004",
        "question": "What parametric hallucination rate was reported for vanilla large language models?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [1],
        "expected_chunk_ids": ["doc_eval_doc_01_p1_c0"],
        "reference_answer": "Vanilla large language models suffer from a parametric hallucination rate of 38.2% on technical benchmarks.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q005",
        "question": "Which specific cross-encoder transformer model is used for reranking?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [2],
        "expected_chunk_ids": ["doc_eval_doc_02_p2_c0"],
        "reference_answer": "The system employs the cross-encoder/ms-marco-MiniLM-L-6-v2 transformer model for candidate reranking.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q006",
        "question": "What dataset was used to fine-tune the cross-encoder reranker model?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [2],
        "expected_chunk_ids": ["doc_eval_doc_02_p2_c0"],
        "reference_answer": "The cross-encoder model was fine-tuned on the Microsoft MS-MARCO passage ranking dataset.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q007",
        "question": "How much average CPU latency is introduced by cross-encoder scoring for 15 candidates?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_02_p5_c0"],
        "reference_answer": "Cross-encoder scoring on candidate pools of size N = 15 adds an average of 185.4ms latency on multi-core CPUs.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q008",
        "question": "What percentage of ungrounded LLM responses were found to contain at least one unsupported assertion?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [1],
        "expected_chunk_ids": ["doc_eval_doc_03_p1_c0"],
        "reference_answer": "Empirical analysis revealed that 78% of ungrounded LLM answers on specialized corporate documents contain at least one unsupported assertion.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q009",
        "question": "What is the maximum character budget allocated for retrieved context in the prompt?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_03_p5_c0"],
        "reference_answer": "Retrieved context injected into the prompt is bounded by a strict maximum character budget of 12,000 characters.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q010",
        "question": "What is the average generation latency measured when using Google Gemini?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_03_p6_c0"],
        "reference_answer": "Generative response synthesis with Google Gemini exhibits an average latency of 1,120ms.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q011",
        "question": "What minimum cosine similarity threshold is required for chunks to be considered relevant?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [4],
        "expected_chunk_ids": ["doc_eval_doc_03_p4_c0"],
        "reference_answer": "The system enforces a minimum cosine similarity threshold of 0.15, rejecting any chunk with lower similarity as noise.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q012",
        "question": "By how much did interactive inline citation chips speed up claim verification in the user study?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [8],
        "expected_chunk_ids": ["doc_eval_doc_03_p8_c0"],
        "reference_answer": "Verification time per claim dropped from 42.0 seconds to 6.5 seconds, representing a 6.4x verification speedup.",
        "question_type": "fact",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    },

    # --- Type 2: Methodology Questions (Q013 - Q020) ---
    {
        "id": "Q013",
        "question": "What four steps comprise the text sanitization pipeline before chunking?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [3],
        "expected_chunk_ids": ["doc_eval_doc_01_p3_c0"],
        "reference_answer": "The four steps are: 1. Whitespace regularization, 2. Hyphenation resolution at line breaks, 3. Non-printable ASCII control code filtering (0x00 to 0x1F), and 4. Unicode NFC normalization.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q014",
        "question": "Why is two-stage retrieval preferred over single-stage bi-encoder retrieval?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [1],
        "expected_chunk_ids": ["doc_eval_doc_02_p1_c0"],
        "reference_answer": "Bi-encoders independently embed queries and documents, losing token-level interactions. Two-stage retrieval combines fast bi-encoder candidate retrieval with high-precision cross-encoder joint self-attention.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q015",
        "question": "How does the source-aware round-robin balancing algorithm prevent single-document dominance?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [4],
        "expected_chunk_ids": ["doc_eval_doc_02_p4_c0"],
        "reference_answer": "The orchestrator partitions candidates by document ID and interleaves chunks in round-robin sequence (doc1_c0, doc2_c0, doc1_c1, doc2_c1) to guarantee equal evidence representation.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q016",
        "question": "How does the citation sanitization algorithm handle hallucinated citation numbers and dangling punctuation?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [3],
        "expected_chunk_ids": ["doc_eval_doc_03_p3_c0"],
        "reference_answer": "Deterministic regex sanitization prunes any citation reference to non-existent source IDs and regularizes preceding whitespace around punctuation marks.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q017",
        "question": "What hierarchical separator priority is used in recursive chunking, and why?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [4],
        "expected_chunk_ids": ["doc_eval_doc_01_p4_c0"],
        "reference_answer": "The hierarchy uses ['\\n\\n', '\\n', '. ', '? ', '! ', '; ', ', ', ' ', ''] to prioritize splitting on paragraph and sentence boundaries before resorting to word-level splits.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q018",
        "question": "How does L2 unit-norm normalization simplify similarity computations in vector space?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_01_p5_c0"],
        "reference_answer": "When vectors have L2 unit norm (||v||_2 = 1.0), the cosine similarity between vectors u and v reduces directly to their inner dot product: cos(u, v) = u . v.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q019",
        "question": "What is the difference between intrinsic hallucinations and extrinsic hallucinations in generative QA?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [1],
        "expected_chunk_ids": ["doc_eval_doc_03_p1_c0"],
        "reference_answer": "Intrinsic hallucinations directly contradict facts present in retrieved evidence, whereas extrinsic hallucinations introduce unverified external assertions that cannot be substantiated from context.",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q020",
        "question": "What procedure does the system follow when evidence is insufficient or similarity is below 0.15?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [4],
        "expected_chunk_ids": ["doc_eval_doc_03_p4_c0"],
        "reference_answer": "The system triggers an explicit abstention response: 'I could not find sufficient information in the selected documents to answer this question.'",
        "question_type": "methodology",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_03"]
    },

    # --- Type 3: Algorithm & Formulation Questions (Q021 - Q028) ---
    {
        "id": "Q021",
        "question": "What mathematical formula is used to calibrate unconstrained cross-encoder logits into relevance probabilities?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [2],
        "expected_chunk_ids": ["doc_eval_doc_02_p2_c0"],
        "reference_answer": "Logits z are calibrated using the standard logistic sigmoid function: sigma(z) = 1 / (1 + exp(-z)), mapping scores into [0.0, 1.0].",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q022",
        "question": "What is the cosine distance formula used by ChromaDB HNSW space?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_01_p6_c0"],
        "reference_answer": "ChromaDB calculates cosine distance as: D(u, v) = 1 - (u . v) / (||u|| ||v||).",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q023",
        "question": "What token sequence structure is supplied as input to the cross-encoder transformer model?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [2],
        "expected_chunk_ids": ["doc_eval_doc_02_p2_c0"],
        "reference_answer": "The cross-encoder takes concatenated sequences in the format: [CLS] query [SEP] passage [SEP].",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q024",
        "question": "What tokens are monitored by the deterministic regex comparison intent detector?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [3],
        "expected_chunk_ids": ["doc_eval_doc_02_p3_c0"],
        "reference_answer": "The regex monitors for comparative tokens including 'compare', 'versus', 'difference', 'contrast', 'distinguish', and 'between'.",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q025",
        "question": "What execution latency does the deterministic regex intent detector exhibit compared to LLM classifiers?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [3],
        "expected_chunk_ids": ["doc_eval_doc_02_p3_c0"],
        "reference_answer": "Deterministic regex token matching executes in sub-microsecond time (0.01ms), unlike LLM classifiers which take 300ms to 600ms.",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q026",
        "question": "Why is passage text truncated to 1000 characters before cross-encoder scoring?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_02_p5_c0"],
        "reference_answer": "Truncating text to 1000 characters prevents quadratic O(N^2) self-attention latency bottlenecks in the transformer layers.",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q027",
        "question": "What layers, hidden dimensions, and attention heads comprise the all-MiniLM-L6-v2 model?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_01_p5_c0"],
        "reference_answer": "The model features 6 transformer layers, 384 hidden dimensions, and 12 self-attention heads.",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q028",
        "question": "What Unicode decomposition form is applied to normalize text before embedding generation?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [3],
        "expected_chunk_ids": ["doc_eval_doc_01_p3_c0"],
        "reference_answer": "Text is normalized into Unicode NFC (Canonical Decomposition, followed by Canonical Composition) form.",
        "question_type": "algorithm",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },

    # --- Type 4: Experimental Results Questions (Q029 - Q036) ---
    {
        "id": "Q029",
        "question": "What baseline Hit Rate@5 and MRR were achieved by vector-only retrieval?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_01_p6_c0"],
        "reference_answer": "Baseline vector-only retrieval achieved a Hit Rate@5 of 82.0% and a Mean Reciprocal Rank (MRR) of 0.714.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q030",
        "question": "What relative MRR improvement percentage was reported after applying cross-encoder reranking?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [1, 5],
        "expected_chunk_ids": ["doc_eval_doc_02_p1_c0", "doc_eval_doc_02_p5_c0"],
        "reference_answer": "Cross-encoder reranking improved Mean Reciprocal Rank (MRR) from 0.714 to 0.865, representing a +21.1% relative gain.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q031",
        "question": "What final Hit Rate@5 was reached after cross-encoder reranking on the candidate pool?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_02_p5_c0"],
        "reference_answer": "Reranking the candidate pool down to top K = 5 elevated the Hit Rate@5 from 82.0% to 94.0%.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q032",
        "question": "What candidate pool size N was found to be the optimal sweet spot in the ablation study?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_02_p6_c0"],
        "reference_answer": "A candidate pool size of N = 15 achieved 96.2% candidate recall with 185.4ms CPU latency, serving as the optimal sweet spot.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q033",
        "question": "How much latency speedup did ONNX Runtime INT8 quantization provide over PyTorch CPU FP32?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [7],
        "expected_chunk_ids": ["doc_eval_doc_02_p7_c0"],
        "reference_answer": "ONNX Runtime INT8 quantization reduced latency from 185.4ms to 58.2ms, achieving a 3.2x speedup with <0.005 score degradation.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q034",
        "question": "Why did 1500-character chunks perform worse in the chunk size ablation study?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [7],
        "expected_chunk_ids": ["doc_eval_doc_01_p7_c0"],
        "reference_answer": "Chunks of 1500 characters caused embedding vector dilution where key facts were overshadowed by peripheral sentences.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q035",
        "question": "What factual faithfulness score was achieved by the grounded RAG framework in human evaluation?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_03_p6_c0"],
        "reference_answer": "Human evaluation confirmed a 92.4% factual faithfulness score with zero critical unsupported assertions.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q036",
        "question": "What similarity threshold tau maximized the F1-score for out-of-domain abstention?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [7],
        "expected_chunk_ids": ["doc_eval_doc_03_p7_c0"],
        "reference_answer": "A threshold of tau = 0.15 maximized F1-score, yielding 95.0% precision on out-of-domain queries.",
        "question_type": "results",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_03"]
    },

    # --- Type 5: Multi-Document Comparison Questions (Q037 - Q044) ---
    {
        "id": "Q037",
        "question": "Compare the latency trade-offs between vector retrieval in Document 1 and cross-encoder reranking in Document 2.",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_01_p6_c0", "doc_eval_doc_02_p5_c0"],
        "reference_answer": "Vector similarity search averages 45.2ms latency for candidate retrieval, whereas cross-encoder reranking adds an additional 185.4ms on CPU to improve precision.",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_02"]
    },
    {
        "id": "Q038",
        "question": "Compare the input sequence format and architecture of all-MiniLM-L6-v2 in Document 1 versus ms-marco-MiniLM-L-6-v2 in Document 2.",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_01_p5_c0", "doc_eval_doc_02_p2_c0"],
        "reference_answer": "The bi-encoder in Document 1 embeds text into 384-dim isolated vectors, while the cross-encoder in Document 2 accepts concatenated [CLS] query [SEP] passage [SEP] sequences for joint cross-attention.",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_02"]
    },
    {
        "id": "Q039",
        "question": "Contrast the failure modes of vector search in Document 1 with the failure modes of cross-encoders in Document 2.",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [8],
        "expected_chunk_ids": ["doc_eval_doc_01_p8_c0", "doc_eval_doc_02_p8_c0"],
        "reference_answer": "Vector search fails on lexical specificity, negation blindness, and polysemy; cross-encoder rerankers fail on candidate truncation (>1000 chars) and semantic false friends.",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_02"]
    },
    {
        "id": "Q040",
        "question": "Compare the ablation findings regarding chunk size in Document 1 with candidate pool size N in Document 2.",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [7],
        "expected_chunk_ids": ["doc_eval_doc_01_p7_c0", "doc_eval_doc_02_p6_c0"],
        "reference_answer": "Document 1 identified 1000 characters as the optimal chunk size to balance specificity and completeness, while Document 2 found N = 15 candidate pool size optimal to balance recall (96.2%) and CPU latency (185.4ms).",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_02"]
    },
    {
        "id": "Q041",
        "question": "How do the multi-document balancing in Document 2 and the context budgeting in Document 3 cooperate to construct the LLM prompt?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [4],
        "expected_chunk_ids": ["doc_eval_doc_02_p4_c0", "doc_eval_doc_03_p5_c0"],
        "reference_answer": "Document 2 balances chunks across documents via round-robin allocation to avoid starvation, and Document 3 caps the resulting combined context to 12,000 characters to prevent attention degradation.",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_02", "eval_doc_03"]
    },
    {
        "id": "Q042",
        "question": "Compare the 42.5% hallucination reduction from dense retrieval in Document 1 with the 92.4% faithfulness score in Document 3.",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [1],
        "expected_chunk_ids": ["doc_eval_doc_01_p1_c0", "doc_eval_doc_03_p6_c0"],
        "reference_answer": "Document 1 demonstrates that adding retrieved context reduces parametric hallucinations by 42.5%, and Document 3 shows that strict grounding and citations achieve a 92.4% factual faithfulness score.",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_03"]
    },
    {
        "id": "Q043",
        "question": "What is the difference between how PyMuPDF extracts page provenance in Document 1 and how citation chips verify provenance in Document 3?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [2],
        "expected_chunk_ids": ["doc_eval_doc_01_p2_c0", "doc_eval_doc_03_p2_c0"],
        "reference_answer": "PyMuPDF tags text blocks with bounding boxes and 1-indexed page metadata during parsing, which Document 3 utilizes to render interactive inline citations and open full-page verification drawers.",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_03"]
    },
    {
        "id": "Q044",
        "question": "How does the full pipeline end-to-end response time of 1,350ms in Document 3 compare with its constituent retrieval and reranking latencies?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [6],
        "expected_chunk_ids": ["doc_eval_doc_01_p6_c0", "doc_eval_doc_02_p5_c0", "doc_eval_doc_03_p6_c0"],
        "reference_answer": "The 1,350ms total latency comprises ~45.2ms vector retrieval (Doc 1), ~185.4ms cross-encoder reranking (Doc 2), and ~1,120ms Gemini generation (Doc 3).",
        "question_type": "comparison",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01", "eval_doc_02", "eval_doc_03"]
    },

    # --- Type 6: Multi-Hop Questions (Q045 - Q050) ---
    {
        "id": "Q045",
        "question": "How do the 150-character sliding overlap and the separator priority work together to preserve semantic context across chunk boundaries?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [4, 7],
        "expected_chunk_ids": ["doc_eval_doc_01_p4_c0", "doc_eval_doc_01_p7_c0"],
        "reference_answer": "Hierarchical separators ensure chunks split along natural sentence/paragraph ends, while the 150-character sliding overlap carries boundary context into the next chunk, preventing boundary information loss.",
        "question_type": "multi_hop",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q046",
        "question": "Trace how text flows from PyMuPDF extraction through sanitization to L2-normalized vector embedding.",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [2, 3, 5],
        "expected_chunk_ids": ["doc_eval_doc_01_p2_c0", "doc_eval_doc_01_p3_c0", "doc_eval_doc_01_p5_c0"],
        "reference_answer": "Text is extracted via PyMuPDF C-bindings, sanitized through 4 normalization passes (whitespace, hyphen-wrap, control codes, NFC), recursively chunked, and encoded into 384-dim L2 unit-norm vectors.",
        "question_type": "multi_hop",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q047",
        "question": "Why does cross-encoder reranking require both candidate truncation to 1000 characters and candidate pool sizing of N=15?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [5, 6],
        "expected_chunk_ids": ["doc_eval_doc_02_p5_c0", "doc_eval_doc_02_p6_c0"],
        "reference_answer": "Pool size N=15 achieves 96.2% candidate recall without excessive overhead, and truncating passages to 1000 characters prevents quadratic O(N^2) attention latency, keeping CPU inference at ~185.4ms.",
        "question_type": "multi_hop",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q048",
        "question": "How does the minimum similarity threshold of 0.15 interact with the abstention response to prevent context saturation?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [4, 5],
        "expected_chunk_ids": ["doc_eval_doc_03_p4_c0", "doc_eval_doc_03_p5_c0"],
        "reference_answer": "Chunks below 0.15 similarity are discarded as noise; if no candidates qualify, the system immediately returns the abstention message without calling Gemini or occupying the 12,000-character context budget.",
        "question_type": "multi_hop",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q049",
        "question": "How does the two-stage pipeline combine candidate generation, sigmoid calibration, and citation sanitization into final answers?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [2, 5],
        "expected_chunk_ids": ["doc_eval_doc_02_p2_c0", "doc_eval_doc_02_p5_c0", "doc_eval_doc_03_p3_c0"],
        "reference_answer": "The bi-encoder retrieves 15 candidates, the cross-encoder computes logits calibrated via sigma(z) into [0, 1] to select top-5, and citation sanitization ensures Gemini cites only valid source indices.",
        "question_type": "multi_hop",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_02", "eval_doc_03"]
    },
    {
        "id": "Q050",
        "question": "How do verifiable inline citations and the document evidence drawer translate into user verification efficiency gains?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [2, 8],
        "expected_chunk_ids": ["doc_eval_doc_03_p2_c0", "doc_eval_doc_03_p8_c0"],
        "reference_answer": "Clickable bracketed chips link directly to highlighted sentences in the PDF page viewer, cutting claim verification time from 42.0s to 6.5s and increasing user trust scores by 84%.",
        "question_type": "multi_hop",
        "difficulty": "hard",
        "selected_document_ids": ["eval_doc_03"]
    },

    # --- Type 7: Contextual Follow-Up Questions (Q051 - Q054) ---
    {
        "id": "Q051",
        "question": "What transformer model is used for generating dense passage embeddings?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_01_p5_c0"],
        "reference_answer": "The system uses the all-MiniLM-L6-v2 transformer model for generating dense passage embeddings.",
        "question_type": "contextual",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q052",
        "question": "And what mathematical normalization is applied to its output vectors?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_01_p5_c0"],
        "reference_answer": "Output vectors are normalized using L2 unit norm (||v||_2 = 1.0) so that inner dot products equal cosine similarities.",
        "question_type": "contextual",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q053",
        "question": "What is the average CPU latency introduced by cross-encoder reranking?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [5],
        "expected_chunk_ids": ["doc_eval_doc_02_p5_c0"],
        "reference_answer": "Cross-encoder reranking introduces an average inference latency of 185.4ms on multi-core CPUs.",
        "question_type": "contextual",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q054",
        "question": "And how much does ONNX runtime INT8 quantization reduce this latency?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [7],
        "expected_chunk_ids": ["doc_eval_doc_02_p7_c0"],
        "reference_answer": "ONNX runtime INT8 quantization reduces cross-encoder latency by 3.2x, dropping inference time to 58.2ms.",
        "question_type": "contextual",
        "difficulty": "medium",
        "selected_document_ids": ["eval_doc_02"]
    },

    # --- Type 8: Unanswerable Out-of-Domain Questions (Q055 - Q060) ---
    {
        "id": "Q055",
        "question": "What was Alphabet's net profit margin in the third quarter of 2024?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [],
        "expected_chunk_ids": [],
        "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
        "question_type": "unanswerable",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q056",
        "question": "Which quantum computing algorithm was simulated in the physical cryostat experiments?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [],
        "expected_chunk_ids": [],
        "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
        "question_type": "unanswerable",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q057",
        "question": "What was the patient's diastolic blood pressure reading after administering the trial medication?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [],
        "expected_chunk_ids": [],
        "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
        "question_type": "unanswerable",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    },
    {
        "id": "Q058",
        "question": "What is the recommended cold tire pressure for a 2023 Tesla Model 3?",
        "document_id": "eval_doc_01",
        "document_name": "rag_dense_retrieval.pdf",
        "expected_pages": [],
        "expected_chunk_ids": [],
        "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
        "question_type": "unanswerable",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_01"]
    },
    {
        "id": "Q059",
        "question": "Who was elected as the Prime Minister of the United Kingdom in July 1945?",
        "document_id": "eval_doc_02",
        "document_name": "neural_reranking_systems.pdf",
        "expected_pages": [],
        "expected_chunk_ids": [],
        "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
        "question_type": "unanswerable",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_02"]
    },
    {
        "id": "Q060",
        "question": "What ingredients are required to prepare traditional Bolognese ragu sauce?",
        "document_id": "eval_doc_03",
        "document_name": "llm_grounding_and_hallucination.pdf",
        "expected_pages": [],
        "expected_chunk_ids": [],
        "reference_answer": "I could not find sufficient information in the selected documents to answer this question.",
        "question_type": "unanswerable",
        "difficulty": "easy",
        "selected_document_ids": ["eval_doc_03"]
    }
]


def export_dataset():
    # 1. Export JSON
    json_path = DATASET_DIR / "evaluation_questions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(QUESTIONS, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(QUESTIONS)} questions to {json_path}")

    # 2. Export CSV
    csv_path = DATASET_DIR / "evaluation_questions.csv"
    headers = [
        "id", "question", "document_id", "document_name", "expected_pages",
        "expected_chunk_ids", "reference_answer", "question_type", "difficulty", "selected_document_ids"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for q in QUESTIONS:
            writer.writerow([
                q["id"],
                q["question"],
                q["document_id"],
                q["document_name"],
                ";".join(map(str, q["expected_pages"])),
                ";".join(q["expected_chunk_ids"]),
                q["reference_answer"],
                q["question_type"],
                q["difficulty"],
                ";".join(q["selected_document_ids"])
            ])
    print(f"Saved {len(QUESTIONS)} questions to {csv_path}")


if __name__ == "__main__":
    export_dataset()
