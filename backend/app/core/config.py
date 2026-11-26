import os
from typing import List, Union, Any
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

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
        "https://groundtruthai1.vercel.app",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        default_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "https://groundtruthai1.vercel.app",
        ]
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            origins = [i.strip() for i in v.split(",") if i.strip()]
            for d in default_origins:
                if d not in origins:
                    origins.append(d)
            return origins
        elif isinstance(v, list):
            res = [str(i) for i in v]
            for d in default_origins:
                if d not in res:
                    res.append(d)
            return res
        return default_origins

    # Database: Default SQLite for serverless and development, remote PostgreSQL when DATABASE_URL is set
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_database_url(cls, v: Any) -> str:
        is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
        v_str = str(v).strip() if v else ""
        
        # On serverless (Vercel / Lambda), always use /tmp/groundtruth.db if no remote PostgreSQL is configured
        if is_serverless:
            if not v_str or "localhost" in v_str or "127.0.0.1" in v_str or "sqlite" in v_str or "groundtruth_user" in v_str:
                return "sqlite:////tmp/groundtruth.db"

        if not v_str:
            return f"sqlite:///{os.path.join(BACKEND_DIR, 'groundtruth.db').replace('\\', '/')}"
            
        if v_str.startswith("postgres://"):
            v_str = v_str.replace("postgres://", "postgresql://", 1)
            
        if v_str.startswith("sqlite:///."):
            rel_path = v_str[len("sqlite:///."):].lstrip("/\\")
            abs_path = os.path.join(BACKEND_DIR, rel_path).replace("\\", "/")
            return f"sqlite:///{abs_path}"
        return v_str
    
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
    STORAGE_DIR: str = "/tmp/uploads" if (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) else os.path.join(BACKEND_DIR, "uploads")
    
    model_config = SettingsConfigDict(
        env_file=[
            os.path.join(BACKEND_DIR, ".env"),
            os.path.join(ROOT_DIR, ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
try:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
except Exception:
    pass
