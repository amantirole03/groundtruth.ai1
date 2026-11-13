import os
from typing import List, Union, Any
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GroundTruth.ai"
    TAGLINE: str = "Answers you can verify."
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "development-secret-key-groundtruth-rag-verification-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i) for i in v]
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

    # Database: Default PostgreSQL with pgvector, fallback SQLite supported for isolated tests
    DATABASE_URL: str = "postgresql://groundtruth_user:groundtruth_pass@localhost:5432/groundtruth_db"
    
    # AI Providers (LLM & Embeddings)
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "gemini", "anthropic"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    EMBEDDING_PROVIDER: str = "mock"  # "mock", "openai", "gemini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536  # Default pgvector dimension (1536 for OpenAI, 768 for gemini, 128 for mock)

    # RAG & Verification Parameters
    CHUNK_SIZE: int = 600      # Target token count (~2400 chars)
    CHUNK_OVERLAP: int = 100   # Overlap token count (~400 chars)
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_THRESHOLD: float = 0.25  # Minimum cosine similarity threshold for evidence inclusion
    
    # Storage and Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "txt"}
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
