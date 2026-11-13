import re
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")

def validate_email_format(email: str) -> str:
    cleaned = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValueError("Invalid email address format.")
    return cleaned

# ----------------- Auth Schemas -----------------
class UserRegister(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_format(v)

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ----------------- Document Schemas -----------------
class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    page_count: int
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

# ----------------- Citation & Claim Schemas -----------------
class CitationResponse(BaseModel):
    id: str
    document_id: str
    filename: str
    page_number: int
    chunk_id: Optional[str] = None
    supporting_excerpt: str
    claim_text: str
    verification_status: str  # "supported", "contradicted", "uncertain"
    model_config = {"from_attributes": True}

class ClaimVerification(BaseModel):
    claim: str
    status: str  # "supported", "contradicted", "uncertain"
    evidence_excerpt: Optional[str] = None
    citation_id: Optional[str] = None
    reason: Optional[str] = None

# ----------------- Chat & Ask Schemas -----------------
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None

class AskResponse(BaseModel):
    status: str  # "answered", "insufficient_evidence", "conflicting_evidence"
    answer: str
    claims: List[ClaimVerification] = []
    citations: List[CitationResponse] = []
    reason: Optional[str] = None
    conversation_id: str
    message_id: str

# ----------------- Conversation Schemas -----------------
class MessageDetailResponse(BaseModel):
    id: str
    role: str
    content: str
    status: str
    reason: Optional[str] = None
    citations: List[CitationResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    message_count: int = 0
    model_config = {"from_attributes": True}

class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    messages: List[MessageDetailResponse] = []
    model_config = {"from_attributes": True}

# ----------------- Evaluation Schemas -----------------
class EvaluationMetrics(BaseModel):
    total_cases: int
    retrieval_recall_at_k: float
    citation_support_rate: float
    answer_correctness_rate: float
    correct_abstention_rate: float
    false_abstention_rate: float
    mean_latency_ms: float
    estimated_cost_usd: float

class EvaluationResultItem(BaseModel):
    id: str
    category: str
    question: str
    expected_status: str
    actual_status: str
    status_match: bool
    actual_answer: str
    latency_ms: float
    metrics: Dict[str, Any]

class EvaluationSummaryResponse(BaseModel):
    total_runs: int
    latest_metrics: Optional[EvaluationMetrics] = None
    recent_evaluations: List[EvaluationResultItem] = []

class EvaluationRunRequest(BaseModel):
    sample_size: Optional[int] = 10

# ----------------- System Stats Schema -----------------
class SystemStatsResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    questions_answered: int
    questions_abstained: int
    recent_activity: List[Dict[str, Any]] = []
    processing_statuses: Dict[str, int] = {}
