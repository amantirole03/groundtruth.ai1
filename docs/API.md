# GroundTruth.ai REST API Reference

All private endpoints require a Bearer token in the `Authorization` header:
`Authorization: Bearer <jwt_access_token>`

Interactive OpenAPI documentation is available locally at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## 1. Authentication Endpoints

### Register User
- **Method / Path**: `POST /api/auth/register`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "user@example.com",
      "created_at": "2026-10-29T18:00:00Z"
    }
  }
  ```

### Login User
- **Method / Path**: `POST /api/auth/login`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK)**: Token object identical to Register.

### Current User Profile
- **Method / Path**: `GET /api/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**: User profile object.

---

## 2. Document Management Endpoints

### Upload Document
- **Method / Path**: `POST /api/documents/upload`
- **Content-Type**: `multipart/form-data`
- **Payload**: `file` (PDF, DOCX, or TXT file up to 20MB)
- **Response (201 Created)**:
  ```json
  {
    "id": "e9b2512f-41be-4b95-a45e-db83ff3cb411",
    "filename": "q3_financial_report.pdf",
    "status": "completed",
    "page_count": 14,
    "chunk_count": 28,
    "error_message": null,
    "created_at": "2026-10-29T18:05:00Z"
  }
  ```

### List Documents
- **Method / Path**: `GET /api/documents`
- **Response (200 OK)**: Array of `DocumentResponse` objects owned by the authenticated user.

### Get Document Details
- **Method / Path**: `GET /api/documents/{document_id}`
- **Response (200 OK)**: `DocumentResponse` with metadata and status.

### Delete Document
- **Method / Path**: `DELETE /api/documents/{document_id}`
- **Response (200 OK)**:
  ```json
  {
    "message": "Document and associated vectors successfully deleted."
  }
  ```

---

## 3. Chat & Verification Endpoints

### Ask Question (RAG Pipeline)
- **Method / Path**: `POST /api/chat/ask`
- **Request Body**:
  ```json
  {
    "question": "What was the operating margin reported in Q3?",
    "conversation_id": "optional-uuid-to-continue-thread",
    "document_ids": ["optional-array-of-document-ids-to-filter-scope"]
  }
  ```
- **Response (200 OK - Answered)**:
  ```json
  {
    "status": "answered",
    "answer": "Operating margin was reported at 24% for the quarter.",
    "claims": [
      {
        "claim": "Operating margin was reported at 24% for the quarter.",
        "status": "supported",
        "evidence_excerpt": "Operating margin was 24%.",
        "citation_id": "chunk-uuid-123",
        "reason": "Strong lexical entailment with 100% key-term overlap."
      }
    ],
    "citations": [
      {
        "id": "citation-uuid-1",
        "document_id": "doc-uuid-1",
        "filename": "q3_financial_report.pdf",
        "page_number": 3,
        "chunk_id": "chunk-uuid-123",
        "supporting_excerpt": "Operating margin was 24%.",
        "claim_text": "Operating margin was reported at 24% for the quarter.",
        "verification_status": "supported"
      }
    ],
    "reason": null,
    "conversation_id": "conv-uuid-1",
    "message_id": "msg-uuid-1"
  }
  ```

- **Response (200 OK - Insufficient Evidence Abstention)**:
  ```json
  {
    "status": "insufficient_evidence",
    "answer": "I couldn't find sufficient evidence in your uploaded documents to answer this question reliably.",
    "claims": [],
    "citations": [],
    "reason": "No sufficiently relevant supporting evidence was found in the indexed documents.",
    "conversation_id": "conv-uuid-1",
    "message_id": "msg-uuid-2"
  }
  ```

### List Conversations
- **Method / Path**: `GET /api/conversations`
- **Response (200 OK)**: Array of conversation summaries.

### Get Conversation Details
- **Method / Path**: `GET /api/conversations/{conversation_id}`
- **Response (200 OK)**: Complete message history with citations and claim statuses.

---

## 4. Evaluation & Metrics Endpoints

### Get Evaluation Summary
- **Method / Path**: `GET /api/evaluation/summary`
- **Response (200 OK)**: Aggregate metrics (`retrieval_recall_at_k`, `citation_support_rate`, `correct_abstention_rate`, `mean_latency_ms`) and recent test run history.

### Run Synthetic Benchmark
- **Method / Path**: `POST /api/evaluation/run`
- **Request Body**: `{"sample_size": 8}`
- **Response (200 OK)**: Newly generated empirical evaluation results across test cases.

---

## 5. System Health & Statistics

### Health Probe
- **Method / Path**: `GET /api/health`
- **Response (200 OK)**: Service status, active LLM provider, embedding dimension, and thresholds.

### Dashboard Statistics
- **Method / Path**: `GET /api/stats`
- **Response (200 OK)**: Real database metrics: `total_documents`, `indexed_documents`, `questions_answered`, `questions_abstained`, `processing_statuses`, and `recent_activity`.
