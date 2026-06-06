from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.metadata_service import extract_metadata_from_file

router = APIRouter(prefix="/extract", tags=["Extraction"])

@router.post("/metadata")
async def extract_metadata_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    return extract_metadata_from_file(await file.read(), file.filename)