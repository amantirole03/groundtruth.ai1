# GroundTruth.ai 🛡️
> **"Answers you can verify."**

GroundTruth.ai is an evidence-grounded Retrieval-Augmented Generation (RAG) platform. Users upload documents and ask questions about their content. The application retrieves relevant passages, generates an answer conditioned exclusively on those passages, provides verifiable source citations, rigorously verifies every factual claim server-side, and honestly abstains when sufficient evidence is unavailable.

---

## 🏛️ Core Principle

> *"Every factual answer must be supported by evidence from the uploaded documents. If sufficient evidence cannot be established, the system must say that it does not know."*

GroundTruth.ai rejects the false promise that generative models are hallucination-free. Instead, it provides mathematical and architectural guardrails:
1. **Server-Side Citation Validation**: Citation IDs and excerpts are checked against the database of actual retrieved chunks. Hallucinated chunk IDs, invented page numbers, or ungrounded quotes are rejected.
2. **Claim Decomposition & Entailment**: Answers are broken down into atomic factual claims and classified as `Supported`, `Contradicted`, or `Uncertain`.
3. **Honest Abstention**: Queries with insufficient evidence (`cosine similarity < RETRIEVAL_THRESHOLD`) or contradictory documents return explicit abstentions (`insufficient_evidence`, `conflicting_evidence`).

---

## 💻 Technology Stack

- **Frontend**:
  - React 18 & TypeScript
  - Vite & Tailwind CSS
  - React Router v6 & Lucide Icons
  - Axios with JWT bearer interceptors
- **Backend**:
  - Python 3.11+ / 3.13
  - FastAPI & Pydantic v2
  - SQLAlchemy 2.0 & Alembic
  - PyMuPDF (fitz) for PDF extraction with page preservation
  - python-docx for DOCX parsing
  - pytest & pytest-asyncio
- **Database**:
  - PostgreSQL 16 with native `pgvector` extension for vector similarity search
  - Dual-mode vector type supporting SQLite for standalone unit testing without false representations
- **AI & Embedding Engine**:
  - Pluggable provider architecture (`OpenAI`, `Mock`, `Gemini`, `Anthropic`)
  - Deterministic high-dimensional feature-hashing embedding provider for air-gapped/offline runs
  - Zero frontend API key leakage
- **Infrastructure**:
  - Multi-stage Dockerfiles (frontend & backend)
  - Docker Compose with health checks and persistent volumes

---

## 📂 Project Structure

```
groundtruth-ai/
├── backend/
│   ├── alembic/              # Database migration scripts & env
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints (auth, docs, chat, eval, stats)
│   │   ├── core/             # Configuration & JWT/bcrypt security
│   │   ├── db/               # SessionLocal & SQLAlchemy base
│   │   ├── models/           # User, Document, DocumentChunk, Message, Citation, Evaluation
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   └── services/         # DocumentProcessor, RAGService, Providers, Evaluator
│   ├── tests/                # 21 comprehensive pytest test cases
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios client with bearer token injection
│   │   ├── components/       # Navbar, ClaimVerificationBadge, EvidenceModal
│   │   ├── context/          # AuthContext with token persistence
│   │   └── pages/            # Landing, Login, Register, Dashboard, Documents, Chat, Evaluation, Settings
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md       # Full architecture and 12-step pipeline diagram
│   ├── API.md                # Complete REST API specification
│   ├── DEPLOYMENT.md         # Docker Compose, Vercel, Render, Supabase guides
│   └── EVALUATION.md         # Synthetic benchmark dataset & metric formulas
├── docker-compose.yml        # Full-stack container orchestration
├── .env.example              # Environment variables template
└── README.md
```

---

## ⚡ Quickstart Guide

### 1. Running with Docker Compose (Recommended)

Start the frontend, FastAPI backend, and PostgreSQL with `pgvector`:
```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Build and launch services
docker compose up --build -d

# 3. Apply database migrations
docker compose exec backend alembic upgrade head
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API & Swagger Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Health Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 2. Local Development Setup (Without Docker)

#### Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install packages
npm install

# Build or run development server
npm run dev
```

---

## 🧪 Testing and Verification

GroundTruth.ai includes 21 automated backend tests verifying:
- Authentication & tenant isolation
- Document upload validation, text extraction, and cascading vector deletes
- Cosine similarity retrieval with threshold gating
- Claim verification & server-side rejection of hallucinated citation IDs
- Prompt injection defense in untrusted document text
- Honest abstention on unanswerable and contradictory queries
- Synthetic benchmark evaluation runner

Run the test suite:
```bash
cd backend
venv\Scripts\python.exe -m pytest -v
```

### Actual Test Run Results:
```text
tests/test_auth.py::test_register_and_login_success PASSED               [  4%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [  9%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 14%]
tests/test_auth.py::test_login_nonexistent_user PASSED                   [ 19%]
tests/test_documents.py::test_upload_txt_document_success PASSED         [ 23%]
tests/test_documents.py::test_upload_empty_file_rejected PASSED          [ 28%]
tests/test_documents.py::test_upload_unsupported_extension_rejected PASSED [ 33%]
tests/test_documents.py::test_upload_corrupted_pdf_handled_gracefully PASSED [ 38%]
tests/test_documents.py::test_cross_user_document_isolation PASSED       [ 42%]
tests/test_documents.py::test_delete_document_cascades PASSED            [ 47%]
tests/test_providers_resilience.py::test_mock_embedding_provider_consistency PASSED [ 52%]
tests/test_providers_resilience.py::test_openai_provider_timeout_fallback PASSED [ 57%]
tests/test_providers_resilience.py::test_text_cleaner_resilience PASSED  [ 61%]
tests/test_providers_resilience.py::test_evaluation_benchmark_execution PASSED [ 66%]
tests/test_rag_pipeline.py::test_correct_answer_with_valid_citation PASSED [ 71%]
tests/test_rag_pipeline.py::test_question_absent_from_documents_abstains PASSED [ 76%]
tests/test_rag_pipeline.py::test_fabricated_citation_id_rejected PASSED  [ 80%]
tests/test_rag_pipeline.py::test_citation_not_supporting_claim_flagged_uncertain PASSED [ 85%]
tests/test_rag_pipeline.py::test_contradictory_document_evidence_abstains PASSED [ 90%]
tests/test_rag_pipeline.py::test_prompt_injection_in_document_safeguard PASSED [ 95%]
tests/test_rag_pipeline.py::test_cross_user_rag_isolation PASSED         [100%]

======================= 21 passed, 7 warnings in 4.66s ========================
```

Frontend production build check:
```bash
cd frontend
npm run build
# Output: dist/assets/index-*.js (303 kB), index-*.css (27 kB) - Built successfully with zero errors.
```

---

## 🔒 Security Architecture

1. **Per-User Boundary**: SQL queries strictly enforce `owner_id == current_user.id`. Documents, chunks, conversations, and citations are isolated.
2. **Untrusted Document Defense**: Text inside uploaded files is treated strictly as passive context data and never executed as prompt instructions.
3. **Secret Isolation**: AI provider API keys are only consumed server-side via `.env` variables and never packaged into frontend assets.
4. **Cascading Deletions**: Deleting a document removes its storage file, database records, and all associated chunks and vector embeddings.

---

## 📄 License
MIT License.
