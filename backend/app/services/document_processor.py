import os
import re
import uuid
import hashlib
from typing import List, Dict, Any, Tuple
from app.core.config import settings

class DocumentProcessingError(Exception):
    """Custom exception raised when document extraction or validation fails."""
    pass

class DocumentProcessor:
    """
    Handles file validation, text extraction (PDF, DOCX, TXT),
    page number preservation, text normalization, and overlapping chunk generation.
    """

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizes filename against directory traversal and dangerous characters."""
        base = os.path.basename(filename)
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\. ]", "_", base)
        return cleaned or "unnamed_document"

    @staticmethod
    def compute_file_hash(content: bytes) -> str:
        """Computes SHA-256 hash of file contents for deduplication checks."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF page by page using pypdf or PyMuPDF (fitz).
        Preserves page numbers (1-indexed).
        """
        pages = []
        # 1. Try lightweight pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise DocumentProcessingError("Document is encrypted or password-protected.")
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                cleaned = DocumentProcessor.clean_text(text)
                if cleaned:
                    pages.append({
                        "page_number": page_idx + 1,
                        "content": cleaned
                    })
            if pages:
                return pages
        except DocumentProcessingError:
            raise
        except Exception:
            pass

        # 2. Fallback to PyMuPDF (fitz) if installed
        try:
            import fitz
            doc = fitz.open(file_path)
            if doc.is_encrypted:
                raise DocumentProcessingError("Document is encrypted or password-protected.")
            if doc.page_count == 0:
                raise DocumentProcessingError("PDF document contains no pages.")
            for page_idx in range(doc.page_count):
                page = doc.load_page(page_idx)
                text = page.get_text("text")
                cleaned = DocumentProcessor.clean_text(text)
                if cleaned:
                    pages.append({
                        "page_number": page_idx + 1,
                        "content": cleaned
                    })
            doc.close()
            if pages:
                return pages
        except DocumentProcessingError:
            raise
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process PDF: {str(e)}")

        if not pages:
            raise DocumentProcessingError("PDF document contains no extractable text. Scanned documents may require OCR.")
        return pages

    @staticmethod
    def extract_text_from_docx(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from DOCX using python-docx or standard library zipfile.
        """
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = []
            for p in doc.paragraphs:
                cleaned = DocumentProcessor.clean_text(p.text)
                if cleaned:
                    paragraphs.append(cleaned)
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(DocumentProcessor.clean_text(cell.text) for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)
            full_text = "\n\n".join(paragraphs)
            if not full_text.strip():
                raise DocumentProcessingError("DOCX document contains no extractable text.")
            return [{"page_number": 1, "content": full_text}]
        except ImportError:
            # Fallback for lightweight serverless environments: extract XML from docx archive directly
            import zipfile
            import xml.etree.ElementTree as ET
            try:
                with zipfile.ZipFile(file_path) as z:
                    xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                text = "".join(tree.itertext())
                cleaned = DocumentProcessor.clean_text(text)
                if not cleaned:
                    raise DocumentProcessingError("DOCX document contains no extractable text.")
                return [{"page_number": 1, "content": cleaned}]
            except Exception as e:
                raise DocumentProcessingError(f"Failed to process DOCX file: {str(e)}")
        except DocumentProcessingError:
            raise
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process DOCX file: {str(e)}")

    @staticmethod
    def extract_text_from_txt(file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text from plain text file with resilient encoding fallback.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                raise DocumentProcessingError(f"Could not decode text file: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read TXT file: {str(e)}")

        cleaned = DocumentProcessor.clean_text(content)
        if not cleaned:
            raise DocumentProcessingError("Text file is empty.")

        return [{"page_number": 1, "content": cleaned}]

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalizes whitespace and removes unprintable control characters."""
        if not text:
            return ""
        # Replace non-breaking spaces and carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
        # Strip ASCII control characters except newline and tab
        text = "".join(ch for ch in text if ch in ("\n", "\t") or ord(ch) >= 32)
        # Collapse excessive newlines and whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @staticmethod
    def chunk_text(
        pages: List[Dict[str, Any]],
        document_id: str,
        owner_id: str,
        source_filename: str,
        chunk_size_tokens: int = 600,
        chunk_overlap_tokens: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Splits extracted pages into overlapping chunks while preserving page provenance.
        Approximate token conversion: 1 token ~ 4 characters.
        """
        char_size = chunk_size_tokens * 4
        char_overlap = chunk_overlap_tokens * 4
        step = max(char_size - char_overlap, 100)

        chunks = []
        for page in pages:
            page_num = page["page_number"]
            page_content = page["content"]
            total_len = len(page_content)

            if total_len <= char_size:
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "owner_id": owner_id,
                    "source_filename": source_filename,
                    "page_number": page_num,
                    "content": page_content,
                })
                continue

            start = 0
            while start < total_len:
                end = min(start + char_size, total_len)
                chunk_slice = page_content[start:end].strip()
                if chunk_slice:
                    chunks.append({
                        "id": str(uuid.uuid4()),
                        "document_id": document_id,
                        "owner_id": owner_id,
                        "source_filename": source_filename,
                        "page_number": page_num,
                        "content": chunk_slice,
                    })
                if end == total_len:
                    break
                start += step

        return chunks
