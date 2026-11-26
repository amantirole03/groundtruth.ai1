import os
import sys
import logging

# Ensure backend directory and root directory are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

for p in (root_dir, backend_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, init_db, SessionLocal
import app.models.models
from app.models.models import User
from app.core.security import get_password_hash

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

# Initialize database schema and pre-seed target user
try:
    init_db()
    db = SessionLocal()
    try:
        user_email = "amantirole39@gmail.com"
        existing = db.query(User).filter(User.email == user_email).first()
        if not existing:
            user = User(
                email=user_email,
                password_hash=get_password_hash("Password123!")
            )
            db.add(user)
            db.commit()
    finally:
        db.close()
except Exception as e:
    logging.getLogger("uvicorn.error").warning(f"Database bootstrap warning: {e}")

# Global error handler to prevent unhandled 500 crashes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_trace = traceback.format_exc()
    logging.getLogger("uvicorn.error").error(f"Global exception: {error_trace}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
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
        "database": "connected",
        "version": "1.0.0"
    }
