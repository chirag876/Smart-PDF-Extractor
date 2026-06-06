import camelot
from fastapi import HTTPException
import pandas as pd
import uuid
from app.utils.file_utils import save_upload, cleanup_file
from app.utils.pdf_utils import is_valid_pdf, is_password_protected

OUTPUT_DIR = "outputs"

def extract_tables_from_file(file_bytes: bytes, filename: str) -> str:
    file_path = save_upload(file_bytes, filename)
    try:
        if not is_valid_pdf(file_path):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
        if is_password_protected(file_path):
            raise HTTPException(status_code=400, detail="Password-protected PDF files are not supported")
        tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
        if len(tables) == 0:
            tables = camelot.read_pdf(file_path, pages='all', flavor='stream')
        if len(tables) == 0:
            return None
        output_path = f"{OUTPUT_DIR}/{uuid.uuid4()}.xlsx"
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for i, table in enumerate(tables):
                table.df.to_excel(writer, sheet_name=f"Table_{i+1}", index=False)
        return output_path
    finally:
        cleanup_file(file_path)