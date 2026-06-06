import pdfplumber
from app.utils.file_utils import save_upload, cleanup_file
from app.utils.pdf_utils import is_valid_pdf, is_password_protected
from fastapi import HTTPException
def extract_metadata_from_file(file_bytes: bytes, filename: str) -> dict:
    file_path = save_upload(file_bytes, filename)
    try:
        if not is_valid_pdf(file_path):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        if is_password_protected(file_path):
            raise HTTPException(status_code=400, detail="Password-protected PDF files are not supported")
        with pdfplumber.open(file_path) as pdf:
            meta = pdf.metadata
            return {
                "filename": filename,
                "pages": len(pdf.pages),
                "title": meta.get("Title", None),
                "author": meta.get("Author", None),
                "creator": meta.get("Creator", None),
                "created": meta.get("CreationDate", None),
            }
    finally:
        cleanup_file(file_path)