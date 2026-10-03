# Academic Research Methodology & Evaluation Design

## 1. Research Objectives
In compliance with MCA Master's Degree academic guidelines, RAGMate incorporates a comparative empirical evaluation of Information Retrieval (IR) paradigms within a Retrieval-Augmented Generation framework:
1. **Experiment 1 (Baseline)**: Lexical / Keyword Retrieval via BM25 (Best Matching 25).
2. **Experiment 2 (Proposed Method)**: Dense Semantic Retrieval via bi-encoder sentence embeddings (`all-MiniLM-L6-v2`) and ChromaDB vector space indexing.
3. **Experiment 3 (Enhanced Method)**: Two-stage retrieval utilizing First-Stage Dense Retrieval followed by Cross-Encoder Reranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`).

---

## 2. Evaluation Metrics Definition

### 2.1 Retrieval Metrics

#### Precision@K
Measures the proportion of retrieved chunks that are genuinely relevant to the query:
$$\text{Precision@K} = \frac{|\text{Retrieved Chunks in Top } K \cap \text{Ground Truth Relevant Chunks}|}{K}$$

#### Recall@K
Measures the proportion of all relevant chunks in the knowledge base that were retrieved in Top $K$:
$$\text{Recall@K} = \frac{|\text{Retrieved Chunks in Top } K \cap \text{Ground Truth Relevant Chunks}|}{|\text{Total Relevant Chunks}|}$$

#### Hit Rate@K
Binary metric indicating whether at least one relevant ground truth chunk appears in the Top $K$ retrieved set:
$$\text{HitRate@K} = \begin{cases} 1 & \text{if } |\text{Retrieved@K} \cap \text{Relevant}| > 0 \\ 0 & \text{otherwise} \end{cases}$$

#### Mean Reciprocal Rank (MRR)
Evaluates ranking quality based on the position of the first relevant chunk:
$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
where $\text{rank}_i$ is the position of the first correct chunk for query $i$.

---

### 2.2 Generation Quality Metrics

#### Faithfulness (Groundedness)
$$\text{Faithfulness} = \frac{\text{Number of Claims in Answer Verified by Context}}{\text{Total Claims in Answer}}$$
Answers that invent assertions not in the retrieved context are penalized.

#### Answer Relevance
Semantic cosine similarity between the generated answer and the ground truth reference answer.

---

### 2.3 Latency & Throughput Metrics
- **Retrieval Latency ($t_{ret}$)**: Milliseconds required to embed the query and perform vector/BM25 lookup.
- **Rerank Latency ($t_{rerank}$)**: Milliseconds spent by the cross-encoder model scoring candidates.
- **Generation Latency ($t_{gen}$)**: Milliseconds elapsed between sending prompt to Google Gemini and receiving the full response.
- **Total Latency**: $t_{total} = t_{ret} + t_{rerank} + t_{gen}$.
