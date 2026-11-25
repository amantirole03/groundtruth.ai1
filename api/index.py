import os
import sys

# Ensure backend directory and root directory are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

for p in (root_dir, backend_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

# Explicit top-level FastAPI instance AST-detectable by Vercel's Python builder
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Evidence-grounded RAG application with factual verification and honest abstention.",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API endpoints with /api prefix and without prefix
app.include_router(api_router, prefix=settings.API_V1_STR)
if settings.API_V1_STR:
    app.include_router(api_router)

@app.get("/")
@app.get("/api")
def root_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
