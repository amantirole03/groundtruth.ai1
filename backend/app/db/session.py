from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# Engine configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_db_initialized = False

def init_db():
    global _db_initialized
    if not _db_initialized:
        try:
            import app.models.models  # Ensures all model tables are registered in Base.metadata
            Base.metadata.create_all(bind=engine)
            _db_initialized = True
        except Exception as e:
            import logging
            logging.getLogger("uvicorn.error").warning(f"Database table initialization warning: {e}")

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
