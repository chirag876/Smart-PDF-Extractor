# SmartPDF

A production-ready **PDF data extraction API** built with FastAPI.  
Upload a PDF  get back text, tables, metadata, or structured invoice data. Handles edge cases cleanly so your application doesn't have to.

---

## Why SmartPDF

Most PDF libraries give you raw output and leave error handling to you. SmartPDF wraps extraction in a clean REST API with consistent error responses, scanned PDF detection, and automatic file cleanup  ready to integrate into any backend pipeline.

---

## Features

- Extract **text** from digital PDFs
- Extract **tables** as `.xlsx` (lattice → stream fallback via `camelot`)
- Extract **PDF metadata**  title, author, pages, creator, creation date
- Extract **structured invoice data**  hybrid coordinate + LLM-based extraction
- **Scanned PDF detection**  returns clear error instead of empty output
- **Password-protected PDF detection**  returns `400` with descriptive message
- Automatic cleanup of uploaded files after processing

---

## Tech Stack

- **FastAPI**
- `pdfplumber`  text, metadata + coordinate-based extraction
- `camelot`  table extraction
- `pandas` + `openpyxl`  Excel output
- `google-genai`  Gemini 2.0 Flash LLM fallback for invoice extraction
- `python-dotenv`  environment variable management

---

## How Invoice Extraction Works

Invoice extraction uses a three-layer hybrid approach:

1. **Coordinate-based extraction**  uses pdfplumber's word-level x/y positions to split content into left and right columns, handling two-column invoice layouts accurately
2. **LLM fallback**  if more than 50% of fields come back null, Gemini 2.0 Flash is called automatically to extract data from any invoice format
3. **Plain text fallback**  if coordinate extraction is unavailable, regex-based parsing is used as a last resort

The response includes an `_extraction_method` field indicating which path was taken  `coordinate`, `llm_fallback`, or `coordinate_partial`.

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
    invoice_service.py     # Hybrid coordinate + LLM extraction
  utils/
    pdf_utils.py
    file_utils.py
  config/
    config.py              # Environment variable loading
```

---

## API Endpoints

### Health Check

`GET /health`

```json
{ "status": "ok", "message": "SmartPDF is running" }
```

---

### Extract Text  `POST /extract/text`

| Scenario | Status | Response |
|---|---|---|
| Digital PDF | `200` | `{ "text": "..." }` |
| Scanned PDF | `200` | `{ "type": "scanned", "message": "Scanned PDF detected. OCR required.", "text": null }` |
| Password-protected | `400` | `{ "detail": "PDF is password protected" }` |
| Invalid file | `422` | Validation error |

---

### Extract Tables  `POST /extract/tables`

| Scenario | Status | Response |
|---|---|---|
| Tables found | `200` | Returns `extracted_tables.xlsx` file |
| No tables found | `200` | `{ "message": "No tables found in PDF" }` |
| Password-protected | `400` | `{ "detail": "PDF is password protected" }` |

---

### Extract Metadata  `POST /extract/metadata`

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

### Extract Invoice Data  `POST /extract/invoice`

| Scenario | Status | Response |
|---|---|---|
| Digital PDF | `200` | Structured invoice JSON |
| Scanned PDF | `400` | `{ "detail": "Scanned PDFs not supported for invoice extraction" }` |
| Password-protected | `400` | `{ "detail": "PDF is password protected" }` |

**Response example:**
```json
{
  "invoice_number": "INV-001",
  "issue_date": "June 09, 2026",
  "due_date": "June 24, 2026",
  "status": "PAID",
  "vendor": "Example LLC",
  "bill_to": "Customer Name",
  "total_amount": "47200.00",
  "tax_rate": "18%",
  "payment_terms": "Payment due within 15 days",
  "items": [
    { "sno": 1, "name": "Python Backend Development", "unit_price": "25000.00", "qty": "1", "line_total": "25000.00" }
  ],
  "_extraction_method": "llm_fallback"
}
```

---

## Setup & Running

### 1. Get Gemini API Key

Get a free API key from [aistudio.google.com](https://aistudio.google.com)  no credit card required.

### 2. Create `.env` file

```bash
cp .env.example .env
# Add your Gemini API key in .env
```

### 3. Create virtual environment

```bash
python -m venv pdfenv
pdfenv\Scripts\activate        # Windows
source pdfenv/bin/activate     # Mac/Linux
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

> `camelot` may require Ghostscript. Install from [ghostscript.com](https://www.ghostscript.com/) if table extraction fails.

### 5. Start server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. API Docs

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

- [x] OCR support for scanned PDFs (`pytesseract`)
- [ ] Batch processing  multiple PDFs in one request
- [ ] Rate limiting  per-IP request throttling
- [ ] Structured logging  per-request audit trail
- [ ] Text search  keyword lookup within PDF content
- [ ] Unit + integration tests (`pytest`)

---

## Known Limitations

- Invoice extraction accuracy depends on PDF quality  scanned PDFs are not supported
- LLM fallback requires a valid `GEMINI_API_KEY` in `.env`  without it, coordinate extraction result is returned as-is

---

## License

MIT