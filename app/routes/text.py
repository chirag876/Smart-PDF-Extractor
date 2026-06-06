from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.pdf_utils import extract_text, is_scanned_pdf
from app.utils.file_utils import save_upload, cleanup_file

router = APIRouter(prefix="/extract", tags=["Extraction"])

@router.post("/text")
async def extract_text_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    file_bytes = await file.read()
    file_path = save_upload(file_bytes, file.filename)
    
    try:
        scanned = is_scanned_pdf(file_path)
        if scanned:
            return {
                "filename": file.filename,
                "type": "scanned",
                "message": "Scanned PDF detected. OCR required.",
                "text": None
            }
        
        text = extract_text(file_path)
        return {
            "filename": file.filename,
            "type": "digital",
            "text": text
        }
    finally:
        cleanup_file(file_path)