from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine

# Automatically ensure database tables exist on startup
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    import logging
    logging.getLogger("uvicorn.error").warning(f"Database table creation deferred/failed: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Evidence-grounded RAG application with factual verification and honest abstention.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Robust CORS configuration supporting localhost, production Vercel domains, and preview URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_origin_regex=r"^https:\/\/([a-zA-Z0-9\-]+\.)?vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router with standard /api prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also mount API router at root for proxies/runtimes that strip the /api prefix
if settings.API_V1_STR:
    app.include_router(api_router)

@app.get("/")
@app.get("/api")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
