from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.utils.file_utils import save_upload, cleanup_file
import pdfplumber
import pandas as pd
import uuid

router = APIRouter(prefix="/extract", tags=["Extraction"])

@router.post("/tables")
async def extract_tables_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_bytes = await file.read()
    file_path = save_upload(file_bytes, file.filename)

    try:
        all_tables = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_tables.append({
                        "page": page_num + 1,
                        "data": df.to_dict(orient="records")
                    })

        if not all_tables:
            return {"message": "No tables found in PDF", "tables": []}

        output_path = f"outputs/{uuid.uuid4()}.xlsx"
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for i, table in enumerate(all_tables):
                df = pd.DataFrame(table["data"])
                df.to_excel(writer, sheet_name=f"Page{table['page']}_Table{i+1}", index=False)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="extracted_tables.xlsx"
        )
    finally:
        cleanup_file(file_path)