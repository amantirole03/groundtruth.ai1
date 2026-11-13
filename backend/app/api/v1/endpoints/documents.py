import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.models import Document, DocumentChunk, User
from app.schemas.schemas import DocumentResponse
from app.api.deps import get_current_user
from app.core.config import settings
from app.services.document_processor import DocumentProcessor, DocumentProcessingError
from app.services.embedding_provider import get_embedding_provider

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validates, extracts, chunks, embeds, and indexes an uploaded document (PDF, DOCX, TXT).
    Guarantees tenant isolation and preserves page provenance.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    # 1. Filename sanitization & Extension validation
    safe_filename = DocumentProcessor.sanitize_filename(file.filename)
    extension = safe_filename.split(".")[-1].lower() if "." in safe_filename else ""
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{extension}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read contents & size validation
    if hasattr(file, "file") and file.file:
        contents = file.file.read()
    else:
        contents = file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # 3. Save physical file to storage
    doc_id = str(uuid.uuid4())
    storage_filename = f"{doc_id}_{safe_filename}"
    storage_path = os.path.join(settings.STORAGE_DIR, storage_filename)
    
    with open(storage_path, "wb") as f:
        f.write(contents)

    # 4. Create document record with pending status
    doc = Document(
        id=doc_id,
        owner_id=current_user.id,
        filename=safe_filename,
        storage_key=storage_path,
        status="processing",
        page_count=0
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # 5. Extract text based on extension
        if extension == "pdf":
            pages = DocumentProcessor.extract_text_from_pdf(storage_path)
        elif extension == "docx":
            pages = DocumentProcessor.extract_text_from_docx(storage_path)
        elif extension == "txt":
            pages = DocumentProcessor.extract_text_from_txt(storage_path)
        else:
            raise DocumentProcessingError(f"Unsupported format: {extension}")

        page_count = max([p["page_number"] for p in pages], default=1)
        doc.page_count = page_count

        # 6. Chunk text
        chunks = DocumentProcessor.chunk_text(
            pages=pages,
            document_id=doc.id,
            owner_id=current_user.id,
            source_filename=doc.filename,
            chunk_size_tokens=settings.CHUNK_SIZE,
            chunk_overlap_tokens=settings.CHUNK_OVERLAP
        )

        if not chunks:
            raise DocumentProcessingError("No extractable chunks found in document.")

        # 7. Generate Embeddings
        embedder = get_embedding_provider()
        chunk_texts = [c["content"] for c in chunks]
        embeddings = embedder.embed_batch(chunk_texts)

        # 8. Save chunks with embeddings
        for i, c in enumerate(chunks):
            db_chunk = DocumentChunk(
                id=c["id"],
                document_id=doc.id,
                owner_id=current_user.id,
                page_number=c["page_number"],
                content=c["content"],
                embedding=embeddings[i]
            )
            db.add(db_chunk)

        doc.status = "completed"
        doc.error_message = None
        db.commit()
        db.refresh(doc)

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            page_count=doc.page_count,
            chunk_count=len(chunks),
            error_message=None,
            created_at=doc.created_at
        )

    except DocumentProcessingError as dpe:
        doc.status = "failed"
        doc.error_message = str(dpe)
        db.commit()
        db.refresh(doc)
        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            page_count=doc.page_count,
            chunk_count=0,
            error_message=str(dpe),
            created_at=doc.created_at
        )
    except Exception as exc:
        doc.status = "failed"
        doc.error_message = f"Unexpected processing error: {str(exc)}"
        db.commit()
        db.refresh(doc)
        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            page_count=doc.page_count,
            chunk_count=0,
            error_message=str(exc),
            created_at=doc.created_at
        )

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all documents belonging to the authenticated user."""
    docs = db.query(Document).filter(Document.owner_id == current_user.id).order_by(Document.created_at.desc()).all()
    
    results = []
    for doc in docs:
        chunk_count = db.query(func.count(DocumentChunk.id)).filter(DocumentChunk.document_id == doc.id).scalar() or 0
        results.append(DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            page_count=doc.page_count,
            chunk_count=chunk_count,
            error_message=doc.error_message,
            created_at=doc.created_at
        ))
    return results

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_details(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves metadata of a specific document with server-side ownership verification."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    chunk_count = db.query(func.count(DocumentChunk.id)).filter(DocumentChunk.document_id == doc.id).scalar() or 0
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        page_count=doc.page_count,
        chunk_count=chunk_count,
        error_message=doc.error_message,
        created_at=doc.created_at
    )

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a document and cascades deletion to chunks and vectors.
    Enforces strict ownership check and cleans up storage.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized.")

    # Remove physical file if exists
    if os.path.exists(doc.storage_key):
        try:
            os.remove(doc.storage_key)
        except Exception:
            pass

    # Cascades will automatically delete chunks and citations
    db.delete(doc)
    db.commit()
    return {"message": "Document and associated vectors successfully deleted."}
