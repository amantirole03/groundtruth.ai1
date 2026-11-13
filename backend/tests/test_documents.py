import io
import pytest
from fastapi import UploadFile, HTTPException
from app.api.v1.endpoints.documents import upload_document, list_documents, get_document_details, delete_document
from app.models.models import Document, DocumentChunk

def test_upload_txt_document_success(db_session, test_user_1):
    content = b"The annual revenue of Acme Corp for fiscal year 2024 was $120 million. Operating margins reached 24%."
    file = UploadFile(filename="annual_report.txt", file=io.BytesIO(content))

    doc_res = upload_document(file=file, db=db_session, current_user=test_user_1)
    assert doc_res.filename == "annual_report.txt"
    assert doc_res.status == "completed"
    assert doc_res.chunk_count >= 1

    # Verify listing
    listed = list_documents(db=db_session, current_user=test_user_1)
    assert len(listed) == 1
    assert listed[0].id == doc_res.id

def test_upload_empty_file_rejected(db_session, test_user_1):
    file = UploadFile(filename="empty.txt", file=io.BytesIO(b""))
    with pytest.raises(HTTPException) as exc_info:
        upload_document(file=file, db=db_session, current_user=test_user_1)
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()

def test_upload_unsupported_extension_rejected(db_session, test_user_1):
    file = UploadFile(filename="malicious.exe", file=io.BytesIO(b"MZ12345"), size=7)
    with pytest.raises(HTTPException) as exc_info:
        upload_document(file=file, db=db_session, current_user=test_user_1)
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail

def test_upload_corrupted_pdf_handled_gracefully(db_session, test_user_1):
    corrupt_bytes = b"NOT_A_REAL_PDF_HEADER_123456789"
    file = UploadFile(filename="corrupt.pdf", file=io.BytesIO(corrupt_bytes))
    
    doc_res = upload_document(file=file, db=db_session, current_user=test_user_1)
    assert doc_res.status == "failed"
    assert doc_res.error_message is not None
    assert "Failed to process PDF" in doc_res.error_message

def test_cross_user_document_isolation(db_session, test_user_1, test_user_2):
    content = b"Confidential Strategy: Project Phoenix is restricted to User 1."
    file = UploadFile(filename="user1_strategy.txt", file=io.BytesIO(content))
    doc_user1 = upload_document(file=file, db=db_session, current_user=test_user_1)

    # User 2 list: empty
    user2_docs = list_documents(db=db_session, current_user=test_user_2)
    assert not any(d.id == doc_user1.id for d in user2_docs)

    # User 2 direct access attempt: must raise 404
    with pytest.raises(HTTPException) as exc_info:
        get_document_details(document_id=doc_user1.id, db=db_session, current_user=test_user_2)
    assert exc_info.value.status_code == 404

    # User 2 delete attempt: must raise 404
    with pytest.raises(HTTPException) as exc_info:
        delete_document(document_id=doc_user1.id, db=db_session, current_user=test_user_2)
    assert exc_info.value.status_code == 404

def test_delete_document_cascades(db_session, test_user_1):
    content = b"Temporary doc. Will be purged completely."
    file = UploadFile(filename="temp.txt", file=io.BytesIO(content))
    doc_res = upload_document(file=file, db=db_session, current_user=test_user_1)

    # Verify chunks exist
    chunks_before = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_res.id).count()
    assert chunks_before > 0

    # Delete
    del_out = delete_document(document_id=doc_res.id, db=db_session, current_user=test_user_1)
    assert "successfully deleted" in del_out["message"]

    # Chunks must be deleted
    chunks_after = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_res.id).count()
    assert chunks_after == 0
