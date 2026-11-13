# GroundTruth.ai Architecture Specification

## 1. Executive Summary & Core Principle
GroundTruth.ai is an enterprise Retrieval-Augmented Generation (RAG) platform founded on a single non-negotiable rule:
> **"Every factual answer must be supported by evidence from the uploaded documents. If sufficient evidence cannot be established, the system must say that it does not know."**

The platform rejects the claim that generative models can be magically hallucination-free. Instead, it provides mathematical and structural guarantees:
1. **Server-Side Citation Validation**: Every citation ID is checked against the database of chunks retrieved for that specific query. Hallucinated chunk IDs, invented page numbers, or ungrounded quotes are rejected.
2. **Claim-by-Claim Entailment Verification**: Generated answers are decomposed into atomic testable claims and evaluated for natural language entailment against retrieved evidence (marking each as `Supported`, `Contradicted`, or `Uncertain`).
3. **Honest Abstention Guarantee**: Queries lacking sufficiently similar passages (`similarity < RETRIEVAL_THRESHOLD`) or plagued by unresolved contradictions trigger explicit abstentions (`insufficient_evidence`, `conflicting_evidence`).

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (React / Vite / TS)"]
        UI[SaaS Dashboard / Chat Workspace / Evidence Viewer]
    end

    subgraph API ["FastAPI Application Gateway"]
        Auth[JWT Token Validation & Tenant Identification]
        DocRouter[Document Ingestion Router]
        ChatRouter[Chat & RAG Router]
        EvalRouter[Evaluation & Telemetry Router]
    end

    subgraph Processing ["Ingestion & Extraction Engine"]
        Extractor[PyMuPDF / python-docx / Text Cleaners]
        Chunker[Overlapping Chunker (600 tok / 100 ov)]
        Embedder[Vector Embedding Provider (OpenAI / Mock)]
    end

    subgraph Storage ["Persistence Layer"]
        PG[(PostgreSQL + pgvector)]
        FileStore[Local Storage / S3 Bucket]
    end

    subgraph RAG ["Grounded Verification Pipeline"]
        Retriever[Tenant-Scoped Vector Cosine Search]
        ThresholdCheck{Cosine Similarity >= 0.25?}
        Generator[Conditioned LLM Answer Generator]
        ClaimDecomp[Claim Decomposition Engine]
        Verifier[Entailment Verifier & Citation Validator]
    end

    UI -->|HTTP / Bearer Token| API
    API --> Auth
    Auth --> DocRouter
    Auth --> ChatRouter
    Auth --> EvalRouter

    DocRouter --> Extractor --> Chunker --> Embedder --> PG
    DocRouter --> FileStore

    ChatRouter --> Retriever
    Retriever -->|owner_id match| PG
    Retriever --> ThresholdCheck
    ThresholdCheck -- No --> Abstain1[Return 'insufficient_evidence']
    ThresholdCheck -- Yes --> Generator --> ClaimDecomp --> Verifier
    Verifier --> Client
```

---

## 3. The 12-Step Grounded RAG Pipeline

1. **Document Upload**: User uploads PDF, DOCX, or TXT file with strict file size (20MB) and extension validation.
2. **Text & Metadata Extraction**: Page boundaries and numbers are preserved (PyMuPDF for PDF, python-docx for DOCX, UTF-8/Latin-1 for TXT). Control characters and anomalous whitespace are cleaned.
3. **Overlapping Chunking**: Documents are split into passages of ~600 tokens (~2400 chars) with ~100 tokens (~400 chars) overlap to prevent loss of context across boundaries.
4. **Embedding Generation**: Chunks are embedded into 1536-dimensional vectors via pluggable providers (`MockEmbeddingProvider`, `OpenAIEmbeddingProvider`).
5. **pgvector Storage**: Chunks and vectors are stored in PostgreSQL with `owner_id` indexing.
6. **Query Submission**: Authenticated user submits a natural language question.
7. **Scoped Vector Retrieval**: Query is embedded and searched exclusively against chunks where `owner_id == current_user.id`.
8. **Threshold Filtering**: Passages must meet or exceed `RETRIEVAL_THRESHOLD` (0.25). If no passages qualify, the system halts with `insufficient_evidence`.
9. **Grounded Answer Generation**: The LLM is instructed via strict system prompt to formulate answers conditioned strictly on retrieved evidence.
10. **Claim Decomposition**: Candidate response is parsed into atomic, factual claims.
11. **Server-Side Claim Verification**:
    - Each claim is verified for lexical and semantic entailment against retrieved passages.
    - Citation IDs and excerpts are checked against the database to prevent invented citations.
12. **Honest Delivery or Bounded Abstention**:
    - If contradicted claims exist: returns `conflicting_evidence`.
    - If claims remain unsupported and ungrounded: returns `insufficient_evidence`.
    - If supported: returns answer with clickable citation chips linked to exact page excerpts.

---

## 4. Threat Model & Security Controls

| Threat Vector | Mitigation Strategy |
|---|---|
| **Cross-Tenant Data Leakage** | All SQL queries explicitly filter by `owner_id == current_user.id`. Foreign keys enforce CASCADE deletes. |
| **Hallucinated Citations** | Server validates citation IDs against actual query result set; rejects invented chunk IDs or quotes. |
| **Prompt Injection in Documents** | Document text is passed purely as untrusted data in user context; instructions embedded within documents are never executed. |
| **Denial of Service / Huge Files** | Request body limits (20MB), streaming file reads, timeout protection on external AI calls. |
| **Credential Compromise** | Password hashing via bcrypt (rounds=12 in production), JWT tokens with expiration, API keys isolated on backend. |
