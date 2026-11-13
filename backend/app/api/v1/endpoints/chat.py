from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.models import Conversation, Message, Citation, User
from app.schemas.schemas import (
    AskRequest,
    AskResponse,
    ConversationResponse,
    ConversationDetailResponse,
    MessageDetailResponse,
    CitationResponse
)
from app.api.deps import get_current_user
from app.services.rag_service import RAGService

router = APIRouter(tags=["Chat & Verification"])

@router.post("/chat/ask", response_model=AskResponse)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a question to the evidence-grounded RAG pipeline.
    Retrieves authorized evidence, generates answer, decomposes into claims,
    and returns verified citations or abstains.
    """
    result = RAGService.execute_rag_pipeline(
        db=db,
        question=request.question,
        owner_id=current_user.id,
        conversation_id=request.conversation_id,
        document_ids=request.document_ids
    )
    return result

@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists conversations belonging to the authenticated user."""
    convs = db.query(Conversation).filter(
        Conversation.owner_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()

    results = []
    for c in convs:
        msg_count = db.query(func.count(Message.id)).filter(Message.conversation_id == c.id).scalar() or 0
        results.append(ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            message_count=msg_count
        ))
    return results

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves conversation message history with full citation breakdown."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized.")

    messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()
    message_details = []

    for msg in messages:
        citations = db.query(Citation).filter(Citation.message_id == msg.id).all()
        citation_responses = []
        for cit in citations:
            doc_filename = cit.document.filename if cit.document else "Unknown Document"
            page_num = cit.chunk.page_number if cit.chunk else 1
            citation_responses.append(CitationResponse(
                id=cit.id,
                document_id=cit.document_id or "",
                filename=doc_filename,
                page_number=page_num,
                chunk_id=cit.chunk_id,
                supporting_excerpt=cit.supporting_excerpt,
                claim_text=cit.claim_text,
                verification_status=cit.verification_status
            ))

        message_details.append(MessageDetailResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            status=msg.status,
            reason=msg.reason,
            citations=citation_responses,
            created_at=msg.created_at
        ))

    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        messages=message_details
    )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a conversation and its messages."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized.")

    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully."}
