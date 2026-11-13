from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.models import Document, Message, User, Conversation
from app.schemas.schemas import SystemStatsResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/stats", tags=["System Statistics"])

@router.get("", response_model=SystemStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns authentic, real dashboard metrics derived strictly from the database.
    Zero fake statistics.
    """
    # Documents stats
    total_docs = db.query(func.count(Document.id)).filter(Document.owner_id == current_user.id).scalar() or 0
    indexed_docs = db.query(func.count(Document.id)).filter(
        Document.owner_id == current_user.id,
        Document.status == "completed"
    ).scalar() or 0

    # Status distribution
    status_counts = db.query(
        Document.status, func.count(Document.id)
    ).filter(Document.owner_id == current_user.id).group_by(Document.status).all()
    processing_statuses = {s: cnt for s, cnt in status_counts}

    # Questions answered and abstained
    # Find all message IDs belonging to user's conversations
    user_conv_ids = db.query(Conversation.id).filter(Conversation.owner_id == current_user.id).subquery()

    answered_count = db.query(func.count(Message.id)).filter(
        Message.conversation_id.in_(user_conv_ids),
        Message.role == "assistant",
        Message.status == "answered"
    ).scalar() or 0

    abstained_count = db.query(func.count(Message.id)).filter(
        Message.conversation_id.in_(user_conv_ids),
        Message.role == "assistant",
        Message.status.in_(["insufficient_evidence", "conflicting_evidence"])
    ).scalar() or 0

    # Recent activity
    recent_messages = db.query(Message, Conversation.title).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.owner_id == current_user.id,
        Message.role == "assistant"
    ).order_by(Message.created_at.desc()).limit(5).all()

    recent_activity = [
        {
            "id": msg.id,
            "conversation_title": conv_title,
            "status": msg.status,
            "content_preview": msg.content[:90] + ("..." if len(msg.content) > 90 else ""),
            "created_at": msg.created_at.isoformat()
        }
        for msg, conv_title in recent_messages
    ]

    return SystemStatsResponse(
        total_documents=total_docs,
        indexed_documents=indexed_docs,
        questions_answered=answered_count,
        questions_abstained=abstained_count,
        recent_activity=recent_activity,
        processing_statuses=processing_statuses
    )
