# DocuRAG — Final Presentation & Viva Voce Readiness Checklist
**Academic Title:** *AI-Powered Intelligent Document Question Answering System Using Retrieval-Augmented Generation*  
**Standard:** Comprehensive Defense Readiness Verification Protocol  

---

## 1. Documentation & Academic Submissions

| Item | Requirement / Target | Verification Status | File Reference |
|:---:|---|:---:|---|
| [ ] | **MCA Project Report / Dissertation** | 17 chapters + preliminary pages completed | [`docs/project-report.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/project-report.md) |
| [ ] | **IEEE/ACM Conference Research Paper** | Abstract, 11 sections, 21 IEEE citations | [`docs/research-paper.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/research-paper.md) |
| [ ] | **Academic Evidence Inventory** | Codebase audit, corpus specs, benchmark audit | [`docs/academic-evidence-inventory.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/academic-evidence-inventory.md) |
| [ ] | **IEEE References Document** | 21 verified peer-reviewed publications | [`docs/references.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/references.md) |
| [ ] | **Mathematical Methodology Document** | Equations for chunking, embeddings, re-ranking | [`docs/methodology.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/methodology.md) |
| [ ] | **Results & Empirical Analysis** | Experiment `EXP_20261004_065505_60` metrics | [`docs/results-analysis.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/results-analysis.md) |
| [ ] | **Comprehensive Testing Report** | 119/119 tests passing across 17 modules | [`docs/testing-report.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/testing-report.md) |
| [ ] | **Viva Master Summary** | 25 structured viva summary sections | [`docs/viva-master-summary.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/viva-master-summary.md) |
| [ ] | **Presentation Slides Content** | 20 structured slides for defense | [`docs/presentation-content.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/presentation-content.md) |
| [ ] | **Presentation Speaker Notes** | Objective, What to Say, Questions for 20 slides | [`docs/presentation-speaker-notes.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/presentation-speaker-notes.md) |
| [ ] | **Live Demo Script & Contingency Plan** | 20-step sequence with failure recovery plan | [`docs/demo-script.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/demo-script.md) |
| [ ] | **Live Demo Questions Bank** | Categorized test questions with expected answers | [`docs/demo-questions.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/demo-questions.md) |
| [ ] | **Technical Viva Question Bank** | 100+ questions with Top 25 ⭐⭐⭐ marked | [`docs/viva-question-bank.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/viva-question-bank.md) |
| [ ] | **Advanced Viva Question Bank** | 25+ deep architectural/mathematical questions | [`docs/advanced-viva-questions.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/advanced-viva-questions.md) |
| [ ] | **Research-Level Viva Questions** | Novelty, baselines, bias, and 10M scaling | [`docs/research-viva-questions.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/research-viva-questions.md) |
| [ ] | **Interview & Placement Guide** | Placement Q&A, Resume, GitHub, LinkedIn | [`docs/interview-questions.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/interview-questions.md) |
| [ ] | **Viva Cheat Sheet** | High-density 2–3 page rapid review sheet | [`docs/viva-cheat-sheet.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/viva-cheat-sheet.md) |

---

## 2. Live Demonstration Environment Verification

- [ ] **Production Cloud URL Verified**: `https://docurag.vercel.app` (or active local host: `http://localhost:5173`).
- [ ] **FastAPI Backend Active**: Render ASGI web service responding on `/health` with `status: "ok"`.
- [ ] **Database Connection Verified**: PostgreSQL / SQLite returning HTTP 200 on `/health/liveness`.
- [ ] **Vector Store Online**: ChromaDB collection accessible and responding.
- [ ] **Google Gemini API Key Configured**: `.env` contains valid, active `GEMINI_API_KEY`.
- [ ] **Local Offline Fallback Server Ready**:
  - Backend running via `backend\venv\Scripts\uvicorn app.main:app --port 8000`.
  - Frontend running via `npm run dev` in `frontend/`.
- [ ] **Standard Test PDFs Placed on Desktop / Downloads**:
  - `Attention_Is_All_You_Need.pdf` (15 pages, Vaswani et al.)
  - `DPR_Open_Domain_QA.pdf` (5 pages, Karpukhin et al.)
  - `Passage_Reranking_BERT.pdf` (4 pages, Nogueira & Cho)
- [ ] **Adversarial Demo Questions Tested**:
  - Verified that `"What is Shor's algorithm?"` emits: *"I cannot answer this question based on the provided documents."*

---

## 3. Physical & Examination Day Preparation

- [ ] **Laptop Power Adapter & Charged Battery**: Full battery with charger packed.
- [ ] **Display Dongle / HDMI Adapter**: Tested with standard projectors/monitors.
- [ ] **Mobile Hotspot / USB Tethering Configured**: Prepared in case university Wi-Fi blocks WebSocket or REST traffic.
- [ ] **Printed Hardcopies**:
  - 2 Bound copies of Project Report (with signed certificates).
  - 2 Copies of Research Paper for external examiners.
  - 1 Laminated copy of [`docs/viva-cheat-sheet.md`](file:///c:/Users/Nagaraj/Desktop/RAGMate/docs/viva-cheat-sheet.md) for personal quick-review before entry.
- [ ] **Backup Flash Drive**: Contains PPT slides, offline PDF report, paper, and pre-recorded application demo video.
- [ ] **Formal Attire & ID Card**: Department dress code and University Hall Ticket / Seat Number (USN).

---

## 4. Academic Integrity & Consistency Verification

Before stepping into the viva room, certify:
- [ ] Same embedding model cited everywhere: `sentence-transformers/all-MiniLM-L6-v2` ($d = 384$).
- [ ] Same re-ranking model cited everywhere: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- [ ] Same generative LLM cited everywhere: Google Gemini 2.5 Flash (`gemini-2.5-flash`).
- [ ] Same chunking bounds cited everywhere: 500 tokens, 100-token overlap.
- [ ] Same evaluation experiment cited everywhere: `EXP_20261004_065505_60` (Precision@5: 0.2630, Recall@5: 0.9938, Hit Rate@5: 1.0000, Abstention: 1.0000).
- [ ] Zero fabricated figures claimed during oral defense.
