from app.services.invoice_service import parse_invoice
from app.services.text_service import extract_text_from_file
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/extract", tags=["Extraction"])


@router.post("/invoice")
async def extract_invoice_data(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    result = extract_text_from_file(await file.read(), file.filename)

    if result.get("type") == "scanned":
        raise HTTPException(
            status_code=400, detail="Scanned PDFs not supported for invoice extraction")

    return parse_invoice(result["text"])
