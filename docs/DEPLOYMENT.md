# GroundTruth.ai Deployment Guide

This guide details local orchestration, containerized execution, database vector initialization, and production cloud deployment strategies for **GroundTruth.ai**.

---

## 1. Local Containerized Orchestration (Docker Compose)

The repository provides a complete production-grade `docker-compose.yml` defining three tightly coupled services:
1. `postgres`: PostgreSQL 16 image bundled with `pgvector` (`pgvector/pgvector:pg16`).
2. `backend`: FastAPI Python 3.11 container with PyMuPDF, python-docx, and vector abstractions.
3. `frontend`: Multi-stage Docker build producing an optimized Vite bundle served via high-performance Nginx with SPA routing and reverse-proxy rules.

### Prerequisites
- Docker Engine 24.0+
- Docker Compose v2.20+

### Step-by-Step Local Startup
1. **Clone and Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Inspect `.env` and set:
   ```env
   SECRET_KEY="generate-a-strong-32-byte-secret-key"
   DATABASE_URL="postgresql://groundtruth_user:groundtruth_pass@postgres:5432/groundtruth_db"
   LLM_PROVIDER="mock"            # Set to "openai" for live model
   EMBEDDING_PROVIDER="mock"      # Set to "openai" for live embeddings
   OPENAI_API_KEY=""              # Required only if provider="openai"
   ```

2. **Launch Services**:
   ```bash
   docker compose up --build -d
   ```

3. **Run Database Migrations**:
   The database automatically initializes the `vector` extension and creates all required tables on startup. To run or verify Alembic migrations explicitly:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. **Verify Connectivity**:
   - Web Application: [http://localhost:5173](http://localhost:5173)
   - FastAPI Interactive API Docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
   - Health Probe: `curl http://localhost:8000/api/health`

---

## 2. Production Cloud Deployment Architecture

```mermaid
flowchart LR
    subgraph ClientHost [Frontend Hosting]
        Vercel[Vercel / Cloudflare Pages / AWS Amplify]
    end

    subgraph BackendHost [Backend Container Host]
        Render[Render Web Service / Fly.io / AWS ECS]
    end

    subgraph DataTier [Managed Cloud Data Tier]
        Supabase[(Supabase / Neon Postgres + pgvector)]
        S3[(AWS S3 / Cloudflare R2 Object Storage)]
    end

    Vercel -->|HTTPS / API Requests| Render
    Render -->|SQL + Vector Similarity| Supabase
    Render -->|Encrypted Document Blobs| S3
```

---

## 3. Cloud Provider Deployment Steps

### A. Managed Database with pgvector (Supabase or Neon)
Both Supabase and Neon provide free-tier and scalable managed PostgreSQL instances with native `pgvector` extension support.

1. **Create Database**:
   - In Supabase or Neon, create a new project.
   - Obtain the connection string URI:
     `postgresql://postgres:[PASSWORD]@[HOST]:5432/[DB_NAME]?sslmode=require`
2. **Enable pgvector**:
   - In the database SQL Editor, verify or run:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```
3. **Run Alembic Migrations**:
   From your local terminal with the remote connection string:
   ```bash
   cd backend
   DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/[DB_NAME]?sslmode=require" alembic upgrade head
   ```

---

### B. Backend Deployment (Render or Fly.io)

#### Deploying on Render:
1. Sign in to [Render](https://render.com) and click **New > Web Service**.
2. Connect your Git repository containing `groundtruth-ai`.
3. Configure the service:
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Instance Type**: Starter / Free (or higher)
4. Set Environment Variables in Render Dashboard:
   - `DATABASE_URL`: Your managed PostgreSQL connection string (from Supabase/Neon).
   - `SECRET_KEY`: A cryptographically random 32+ byte string (`openssl rand -hex 32`).
   - `ALGORITHM`: `HS256`
   - `LLM_PROVIDER`: `openai` (or `mock` for zero-cost demonstrations).
   - `OPENAI_API_KEY`: `sk-...`
   - `EMBEDDING_PROVIDER`: `openai`
   - `EMBEDDING_MODEL`: `text-embedding-3-small`
   - `EMBEDDING_DIMENSION`: `1536`
   - `RETRIEVAL_THRESHOLD`: `0.25`
   - `BACKEND_CORS_ORIGINS`: `https://your-frontend.vercel.app`
5. Click **Create Web Service**. Note the deployed backend URL (e.g., `https://groundtruth-api.onrender.com`).

---

### C. Frontend Deployment (Vercel)

#### Deploying on Vercel:
1. Sign in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Import your Git repository.
3. Configure the build settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Configure API Proxy / Rewrite in `frontend/vercel.json`:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://groundtruth-api.onrender.com/api/:path*"
       },
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
5. Click **Deploy**. Vercel will provide an SSL-secured custom URL (e.g., `https://groundtruth-ai.vercel.app`).

---

### D. Private Object Storage (AWS S3 or Cloudflare R2)

In production environments requiring multi-instance autoscaling, document uploads should transition from ephemeral local storage to encrypted cloud object storage:
1. **Create Bucket**:
   - Create a private bucket (e.g. `groundtruth-documents-prod`).
   - Enable Server-Side Encryption (SSE-S3 or AWS KMS).
   - Enforce Public Access Block.
2. **Configure IAM / Credentials**:
   Provide the backend service with least-privilege IAM credentials:
   - `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`.
3. Set environment variables on the backend:
   ```env
   STORAGE_BACKEND="s3"
   AWS_S3_BUCKET="groundtruth-documents-prod"
   AWS_ACCESS_KEY_ID="AKIA..."
   AWS_SECRET_ACCESS_KEY="..."
   AWS_REGION="us-east-1"
   ```

---

## 4. Free-Tier Limitations & Operational Considerations

| Provider | Component | Free-Tier Quota / Constraint | Production Recommendation |
|---|---|---|---|
| **Render** | FastAPI Backend | Free instances spin down after 15 minutes of inactivity (50s cold start). | Upgrade to Starter ($7/mo) to eliminate cold starts. |
| **Supabase** | pgvector DB | Pauses after 7 days of inactivity; 500MB storage quota. | Use Pro tier ($25/mo) or Neon serverless for continuous vector loads. |
| **Vercel** | React Vite Frontend | Generous 100GB bandwidth; instantaneous global edge CDN. | Standard free tier is production-ready for frontend assets. |
| **OpenAI** | LLM & Embeddings | Pay-per-token usage (`text-embedding-3-small`: $0.02 / 1M tokens). | Pre-compute and cache document embeddings; use rate-limiting guards. |
