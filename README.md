# SmartPDF

A production-ready **PDF data extraction API** built with FastAPI.  
Upload a PDF get back text, tables, metadata, or structured invoice data. Handles edge cases cleanly so your application doesn't have to.

---

## Why SmartPDF

Most PDF libraries give you raw output and leave error handling to you. SmartPDF wraps extraction in a clean REST API with consistent error responses, scanned PDF detection, and automatic file cleanup ready to integrate into any backend pipeline.

---

## Features

- Extract **text** from digital PDFs
- Extract **tables** as `.xlsx` (lattice → stream fallback via `camelot`)
- Extract **PDF metadata** — title, author, pages, creator, creation date
- Extract **structured invoice data** — vendor, bill-to, line items, totals (regex-based)
- **Scanned PDF detection** — returns clear error instead of empty output
- **Password-protected PDF detection** — returns `400` with descriptive message
- Automatic cleanup of uploaded files after processing

---

## Tech Stack

- **FastAPI**
- `pdfplumber` — text + metadata extraction
- `camelot` — table extraction
- `pandas` + `openpyxl` — Excel output

---

## Project Structure

```text
app/
  main.py                  # FastAPI app + route registration
  routes/
    text.py                # POST /extract/text
    tables.py              # POST /extract/tables
    metadata.py            # POST /extract/metadata
    invoice.py             # POST /extract/invoice
  services/
    text_service.py
    table_service.py
    metadata_service.py
    invoice_service.py
  utils/
    pdf_utils.py
    file_utils.py
  config/
    config.py
```

---

## API Endpoints

### Health Check

`GET /health`

```json
{ "status": "ok", "message": "SmartPDF is running" }
```

---

### Extract Text — `POST /extract/text`

| Scenario | Status | Response |
|---|---|---|
| Digital PDF | `200` | `{ "text": "..." }` |
| Scanned PDF | `200` | `{ "type": "scanned", "message": "Scanned PDF detected. OCR required.", "text": null }` |
| Password-protected | `400` | `{ "detail": "PDF is password protected" }` |
| Invalid file | `422` | Validation error |

---

### Extract Tables — `POST /extract/tables`

| Scenario | Status | Response |
|---|---|---|
| Tables found | `200` | Returns `extracted_tables.xlsx` file |
| No tables found | `200` | `{ "message": "No tables found in PDF" }` |
| Password-protected | `400` | `{ "detail": "PDF is password protected" }` |

---

### Extract Metadata — `POST /extract/metadata`

```json
{
  "filename": "sample.pdf",
  "pages": 3,
  "title": "...",
  "author": "...",
  "creator": "...",
  "created": "..."
}
```

---

### Extract Invoice Data — `POST /extract/invoice`

| Scenario | Status | Response |
|---|---|---|
| Digital PDF | `200` | Structured invoice JSON |
| Scanned PDF | `400` | `{ "detail": "Scanned PDFs not supported for invoice extraction" }` |
| Password-protected | `400` | `{ "detail": "PDF is password protected" }` |

**Response example:**
```json
{
  "vendor": "...",
  "bill_to": "...",
  "total_amount": "...",
  "payment_terms": "...",
  "items": [
    { "sno": 1, "name": "...", "qty": "...", "discount": "...", "tax": "...", "price": 0 }
  ]
}
```

---

## Setup & Running

### 1. Create virtual environment

```bash
python -m venv pdfenv
pdfenv\Scripts\activate        # Windows
source pdfenv/bin/activate     # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> `camelot` may require Ghostscript. Install from [ghostscript.com](https://www.ghostscript.com/) if table extraction fails.

### 3. Start server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API Docs

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

---

## Usage Examples

```bash
# Extract text
curl -X POST "http://localhost:8000/extract/text" \
  -F "file=@./sample.pdf"

# Extract tables (saves Excel file)
curl -X POST "http://localhost:8000/extract/tables" \
  -F "file=@./table.pdf" \
  --output extracted_tables.xlsx

# Extract metadata
curl -X POST "http://localhost:8000/extract/metadata" \
  -F "file=@./sample.pdf"

# Extract invoice data
curl -X POST "http://localhost:8000/extract/invoice" \
  -F "file=@./invoice.pdf"
```

---

## Roadmap

- [ ] OCR support for scanned PDFs (`pytesseract`)
- [ ] Batch processing — multiple PDFs in one request
- [ ] Rate limiting — per-IP request throttling
- [ ] Structured logging — per-request audit trail
- [ ] Text search — keyword lookup within PDF content
- [ ] Unit + integration tests (`pytest`)

---

## Known Limitations

- Invoice extraction is regex-based — accuracy depends on invoice format consistency
- Scanned PDFs return an error; OCR is on the roadmap

---

## License

MIT