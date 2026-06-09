import tempfile
import os
import pdfplumber
from app.services.invoice_service import parse_invoice_from_words, parse_invoice
from app.services.text_service import extract_text_from_file
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/extract", tags=["Extraction"])


@router.post("/invoice")
async def extract_invoice_data(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_bytes = await file.read()

    # Check for password protection and scanned PDF first
    text_result = extract_text_from_file(file_bytes, file.filename)

    if text_result.get("type") == "scanned":
        raise HTTPException(
            status_code=400,
            detail="Scanned PDFs not supported for invoice extraction"
        )

    # Use coordinate-based extraction (more accurate for two-column layouts)
    # Write bytes to a temp file since pdfplumber needs a file path or file object
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            all_words = []
            for page in pdf.pages:
                all_words.extend(page.extract_words())
        return parse_invoice_from_words(all_words)
    except Exception:
        # Fallback to plain text parsing if coordinate extraction fails
        return parse_invoice(text_result.get("text", ""))
    finally:
        os.unlink(tmp_path)