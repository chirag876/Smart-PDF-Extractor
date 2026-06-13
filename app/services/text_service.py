from app.utils.file_utils import save_upload, cleanup_file
from app.utils.pdf_utils import extract_text, is_scanned_pdf, is_valid_pdf, is_password_protected, ocr_with_gemini
from fastapi import HTTPException

def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
    file_path = save_upload(file_bytes, filename)
    try:
        if not is_valid_pdf(file_path):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        if is_password_protected(file_path):
            raise HTTPException(status_code=400, detail="Password-protected PDF files are not supported")
        if is_scanned_pdf(file_path):
            try:
                ocr_text = ocr_with_gemini(file_path)
                return {
                    "type": "scanned",
                    "_extraction_method": "ocr_gemini",
                    "text": ocr_text
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"OCR failed: {str(e)}"
                )
        return {
            "type": "digital",
            "_extraction_method": "pdfplumber",
            "text": extract_text(file_path)
        }
    finally:
        cleanup_file(file_path)