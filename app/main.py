from fastapi import FastAPI
from app.routes import metadata, text, tables

app = FastAPI(
    title="SmartPDF",
    description="Automated PDF Data Extraction API",
    version="1.0.0"
)

app.include_router(text.router)
app.include_router(tables.router)
app.include_router(metadata.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "SmartPDF is running"}