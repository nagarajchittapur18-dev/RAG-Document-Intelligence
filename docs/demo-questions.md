# DocuRAG — Live Demo Question Bank & Expected Behaviors
**Corpus Tested:** 24-Page Academic Corpus (Vaswani et al. 2017, Karpukhin et al. 2020, Nogueira & Cho 2019)  
**Evaluation Standard:** 100% Truthful Grounding & Deterministic Citations  

---

## 1. Overview

During the live demonstration, examiners will ask questions or ask you to prompt the system. Use this curated question catalog to demonstrate the platform across six cognitive categories:
1. **Easy / Factoid Questions** (single numerical or term lookup)
2. **Medium / Conceptual Questions** (architectural or theoretical explanation)
3. **Difficult / Algorithmic Questions** (mathematical formulas and procedures)
4. **Follow-Up Questions** (conversational coreference and pronoun resolution)
5. **Multi-Document Comparison Questions** (cross-document synthesis and document balancing)
6. **Adversarial / Out-of-Domain Unanswerable Questions** (hallucination defense and abstention)

---

## 2. Categorized Demo Questions & Ground-Truth Expectations

### Category 1: Easy / Factoid Questions (Single Document: Vaswani et al.)
- **Question 1.1**: `"What is the dimensionality d_model of the base Transformer architecture?"`
  - **Target Document**: `Attention_Is_All_You_Need.pdf` (Page 3)
  - **Expected Answer**: *"The dimensionality of the base Transformer architecture is $d_{\text{model}} = 512$ [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 3, Chunk 0.
- **Question 1.2**: `"How many encoder and decoder layers are stacked in the base Transformer?"`
  - **Target Document**: `Attention_Is_All_You_Need.pdf` (Page 3)
  - **Expected Answer**: *"The Transformer model stacks $N = 6$ identical layers in both the encoder and decoder [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 3, Chunk 0.
- **Question 1.3**: `"What dropout rate was applied during training of the Transformer?"`
  - **Target Document**: `Attention_Is_All_You_Need.pdf` (Page 7)
  - **Expected Answer**: *"A residual dropout rate of $P_{\text{drop}} = 0.1$ was applied to the sums of sub-layer outputs and positional encodings [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 7, Chunk 1.

---

### Category 2: Medium / Conceptual Questions (Single Document: Karpukhin et al.)
- **Question 2.1**: `"Explain the primary goal of Dense Passage Retrieval (DPR) compared to traditional BM25."`
  - **Target Document**: `DPR_Open_Domain_QA.pdf` (Pages 1–2)
  - **Expected Answer**: *"Dense Passage Retrieval (DPR) replaces traditional sparse BM25 keyword matching with dense representations learned via dual encoders. Unlike BM25, which suffers from term mismatch, DPR maps questions and passages into a continuous vector space to capture semantic similarity even when lexical tokens differ [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 1, Chunk 0 or Page 2, Chunk 0.
- **Question 2.2**: `"What loss function is used to train the dual encoders in DPR?"`
  - **Target Document**: `DPR_Open_Domain_QA.pdf` (Page 2)
  - **Expected Answer**: *"The DPR dual encoders are trained using negative log-likelihood (NLL) loss over a softmax distribution, optimizing the score of the positive passage against in-batch negative passages [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 2, Chunk 1.

---

### Category 3: Difficult / Algorithmic Questions (Single Document: Vaswani et al. & Nogueira & Cho)
- **Question 3.1**: `"Write down the mathematical formula for Scaled Dot-Product Attention and explain the role of sqrt(d_k)."`
  - **Target Document**: `Attention_Is_All_You_Need.pdf` (Page 4)
  - **Expected Answer**: *"Scaled Dot-Product Attention is computed as:  
    $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$  
    The scaling factor $\frac{1}{\sqrt{d_k}}$ is introduced because for large values of $d_k$, the dot products grow large in magnitude, pushing the softmax function into regions with extremely small gradients [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 4, Chunk 0.
- **Question 3.2**: `"Describe the input sequence formatting used by the BERT cross-encoder for passage re-ranking."`
  - **Target Document**: `Passage_Reranking_BERT.pdf` (Page 2)
  - **Expected Answer**: *"The cross-encoder concatenates the query and candidate passage into a single sequence: `[CLS]` followed by the query tokens, separated by `[SEP]`, followed by the passage tokens and a final `[SEP]`. A segment embedding distinguishes query from passage, and the `[CLS]` token output is fed to a classification layer to compute relevance [1]."*
  - **Citation Verification**: `[1]` $\rightarrow$ Page 2, Chunk 0.

---

### Category 4: Multi-Turn Conversational Follow-Up Questions (Contextual Memory)
- **Turn 1**: `"What optimizer was used to train the Transformer?"`
  - **Expected Answer**: *"The model was trained using the Adam optimizer with $\beta_1 = 0.9$, $\beta_2 = 0.98$, and $\epsilon = 10^{-9}$ [1]."*
- **Turn 2 (Follow-up with pronoun)**: `"What learning rate schedule did it follow?"`
  - **Rewritten Standalone Query (Internal)**: *"What learning rate schedule did the Adam optimizer follow in the Transformer model?"*
  - **Expected Answer**: *"The learning rate was varied according to a formula that increases linearly for the first $\text{warmup\_steps} = 4000$ and decreases proportionally to the inverse square root of the step number thereafter [1]."*
  - **Demonstration Value**: Shows conversational memory and query rewriting without requiring the user to repeat "the Transformer" or "Adam optimizer".

---

### Category 5: Multi-Document Comparison Questions (All Documents Mode)
- **Question 5.1**: `"Compare the retrieval approach of Karpukhin et al. (DPR) with the re-ranking approach of Nogueira and Cho."`
  - **Target Documents**: `DPR_Open_Domain_QA.pdf` and `Passage_Reranking_BERT.pdf`
  - **Expected Answer**: *"Karpukhin et al. utilize a bi-encoder architecture that pre-computes dense passage vectors to enable fast sub-linear retrieval over millions of documents using MIPS [1]. In contrast, Nogueira and Cho utilize a cross-encoder architecture that jointly processes query and passage tokens via full self-attention, producing superior re-ranking accuracy at the cost of higher computational latency [2]."*
  - **Citation Verification**:
    - `[1]` $\rightarrow$ `DPR_Open_Domain_QA.pdf` (Page 1 or 2)
    - `[2]` $\rightarrow$ `Passage_Reranking_BERT.pdf` (Page 1 or 2)
  - **Demonstration Value**: Proves that the adaptive document-balancing algorithm sampled evidence from both documents rather than letting one document monopolize the context.

---

### Category 6: Adversarial / Out-of-Domain Unanswerable Questions (Hallucination Defense)
- **Question 6.1**: `"What is the quantum superposition principle used in Shor's prime factorization algorithm?"`
  - **Expected Answer**:  
    *"I cannot answer this question based on the provided documents."*
  - **Demonstration Value**: Proves that the system refuses to answer out-of-domain questions and achieves a **1.0000 Abstention Accuracy**, completely eliminating hallucination.
- **Question 6.2**: `"What was the battery life of the device tested in the Transformer paper?"`
  - **Expected Answer**:  
    *"I cannot answer this question based on the provided documents."*
  - **Demonstration Value**: The model recognizes that while "Transformer paper" is in-domain, "battery life" is not discussed in the paper.

---

## 3. Examiner Interaction Guidelines

1. **When Asked to Query a Complex Formula**:
   - Use Question 3.1 (Scaled Dot-Product Attention).
   - Point out that LaTeX formatting is rendered cleanly in the React markdown view.
2. **When Asked to Prove Multi-Tenancy**:
   - Open an incognito browser window, log in as a second user, and show that User A's uploaded PDFs do NOT appear in User B's dashboard.
3. **When Asked to Prove Reranking Value**:
   - Open `/evaluation`, scroll to the Comparative Re-ranking Chart, and highlight the **+9.76% gain in Comparison MRR** and **100% Hit Rate@5**.
