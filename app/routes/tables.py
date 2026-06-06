from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.services.table_service import extract_tables_from_file

router = APIRouter(prefix="/extract", tags=["Extraction"])

@router.post("/tables")
async def extract_tables_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    output_path = extract_tables_from_file(await file.read(), file.filename)
    
    if not output_path:
        return {"message": "No tables found in PDF"}
    
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="extracted_tables.xlsx"
    )