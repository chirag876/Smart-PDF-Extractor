import re
import json
import os
import pdfplumber
from google import genai
from dotenv import load_dotenv
import time
load_dotenv()


# ── Column boundary ───────────────────────────────────────────────────────────
MID_X = 250

# ── Null threshold for LLM fallback ──────────────────────────────────────────
# If coordinate extraction returns more than this fraction of null values,
# we fall back to LLM extraction.
NULL_THRESHOLD = 0.5


# ── Internal helpers ──────────────────────────────────────────────────────────

def _group_words_by_line(words: list, tolerance: int = 3) -> dict:
    lines = {}
    for w in words:
        top = round(w["top"] / tolerance) * tolerance
        lines.setdefault(top, []).append(w)
    for top in lines:
        lines[top].sort(key=lambda w: w["x0"])
    return dict(sorted(lines.items()))


def _words_to_text(word_list: list) -> str:
    return " ".join(w["text"] for w in word_list).strip()


def _build_columns(words: list) -> list[dict]:
    rows = []
    for top, wlist in _group_words_by_line(words).items():
        left = _words_to_text([w for w in wlist if w["x0"] < MID_X])
        right = _words_to_text([w for w in wlist if w["x0"] >= MID_X])
        rows.append({"top": top, "left": left, "right": right})
    return rows


def _left_value(rows: list, label: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(label)}\s+(.+)", re.IGNORECASE)
    for row in rows:
        m = pattern.match(row["left"])
        if m:
            return m.group(1).strip()
    return None


def _right_value(rows: list, label: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(label)}\s+(.+)", re.IGNORECASE)
    for row in rows:
        m = pattern.match(row["right"])
        if m:
            return m.group(1).strip()
    return None


def _null_ratio(result: dict) -> float:
    """Return the fraction of fields that are null or empty."""
    fields = [v for k, v in result.items() if k != "_extraction_method"]
    if not fields:
        return 1.0
    null_count = sum(1 for v in fields if v is None or v == [] or v == "")
    return null_count / len(fields)


# ── Public API ────────────────────────────────────────────────────────────────

def parse_invoice_from_words(words: list) -> dict:
    """
    Primary entry point.
    1. Try coordinate-based extraction.
    2. If > 50% fields are null, fall back to LLM extraction.
    """
    result = _parse(words)

    if _null_ratio(result) > NULL_THRESHOLD:
        # Reconstruct plain text from words for LLM input
        plain_text = " ".join(w["text"] for w in sorted(
            words, key=lambda w: (w["top"], w["x0"])))
        llm_result = _parse_with_llm_text(plain_text)
        if llm_result:
            llm_result["_extraction_method"] = "llm_fallback"
            return llm_result
        result["_extraction_method"] = "coordinate_partial"
    else:
        result["_extraction_method"] = "coordinate"

    return result


def parse_invoice_from_path(pdf_path: str) -> dict:
    """Parse invoice from a PDF file path."""
    with pdfplumber.open(pdf_path) as pdf:
        all_words = []
        for page in pdf.pages:
            all_words.extend(page.extract_words())
    return parse_invoice_from_words(all_words)


def parse_invoice(text: str) -> dict:
    """Fallback: parse from plain text only (no coordinate data)."""
    return _parse_from_text(text)


# ── Coordinate-based extraction ───────────────────────────────────────────────

def _parse(words: list) -> dict:
    rows = _build_columns(words)
    return {
        "invoice_number": _extract_invoice_number(rows),
        "issue_date":     _extract_issue_date(rows),
        "due_date":       _extract_due_date(rows),
        "status":         _extract_status(rows),
        "vendor":         _extract_vendor(rows),
        "bill_to":        _extract_bill_to(rows),
        "total_amount":   _extract_total(rows),
        "tax_rate":       _extract_tax_rate(rows),
        "payment_terms":  _extract_payment_terms(rows),
        "items":          _extract_items(rows),
    }


def _extract_invoice_number(rows):
    return _left_value(rows, "Invoice Number") or _left_value(rows, "Invoice No") or _left_value(rows, "Invoice #")


def _extract_issue_date(rows):
    return _left_value(rows, "Issue Date") or _left_value(rows, "Date") or _left_value(rows, "Invoice Date")


def _extract_due_date(rows):
    return _left_value(rows, "Due Date") or _left_value(rows, "Payment Due")


def _extract_status(rows):
    return _left_value(rows, "Status")


def _extract_vendor(rows):
    for row in rows:
        if re.search(r'\bBill\s+To\b', row["right"], re.IGNORECASE):
            return row["left"] if row["left"] else None
    return None


def _extract_bill_to(rows):
    found_header = False
    for row in rows:
        if re.search(r'\bBill\s+To\b', row["right"], re.IGNORECASE):
            found_header = True
            continue
        if found_header and row["right"]:
            val = row["right"]
            if re.match(r'[\(\d\+]', val) or "@" in val:
                continue
            return val
    return None


def _extract_total(rows):
    labels = ["Amount Due", "Grand Total", "Net Amount",
              "Net Payable", "Total Amount", "Total"]
    for label in labels:
        val = _right_value(rows, label)
        if val:
            amount = re.sub(r'[^\d.]', '', val.replace(',', ''))
            return amount if amount else val
    return None


def _extract_tax_rate(rows):
    val = _right_value(rows, "Tax Rate")
    if not val:
        for row in rows:
            m = re.search(
                r'(GST|IGST|CGST|SGST)[^\d]*([\d.]+%?)', row["right"], re.IGNORECASE)
            if m:
                return m.group(2)
    return val


def _extract_payment_terms(rows):
    for row in rows:
        m = re.search(r'(Payment\s+is\s+due[^\n]+|Net\s+\d+\s+days)',
                      row["left"] + " " + row["right"], re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_items(rows) -> list:
    STOP_WORDS = re.compile(
        r'^(Subtotal|Tax|Amount Due|Grand Total|Total|Net Amount|Note|For questions)',
        re.IGNORECASE
    )
    HEADER_WORDS = re.compile(
        r'\b(Item|Description|Particulars)\b', re.IGNORECASE)

    items = []
    in_table = False

    for row in rows:
        full_line = (row["left"] + " " + row["right"]).strip()

        if not in_table:
            if HEADER_WORDS.search(full_line):
                in_table = True
            continue

        if STOP_WORDS.match(row["left"]) or STOP_WORDS.match(row["right"]):
            break

        if not full_line:
            continue

        m = re.match(
            r'^(.+?)\s+\$?([\d,]+\.?\d*)\s+(\d+)\s+\$?([\d,]+\.?\d*)$',
            full_line
        )
        if m:
            items.append({
                "sno":        len(items) + 1,
                "name":       m.group(1).strip(),
                "unit_price": m.group(2).replace(',', ''),
                "qty":        m.group(3),
                "line_total": m.group(4).replace(',', ''),
            })
        else:
            name = row["left"].strip()
            if name and not STOP_WORDS.match(name):
                items.append({
                    "sno":        len(items) + 1,
                    "name":       name,
                    "unit_price": None,
                    "qty":        None,
                    "line_total": None,
                })

    return items


# ── LLM fallback ──────────────────────────────────────────────────────────────

INVOICE_SCHEMA = {
    "invoice_number": "",
    "issue_date": "",
    "due_date": "",
    "status": "",
    "vendor": "",
    "bill_to": "",
    "total_amount": "",
    "tax_rate": "",
    "payment_terms": "",
    "items": [
        {
            "sno": 1,
            "name": "",
            "unit_price": "",
            "qty": "",
            "line_total": ""
        }
    ]
}

LLM_PROMPT = f"""Extract all invoice data from the text below.
Return ONLY valid JSON matching this exact schema. Use null for missing fields. No explanation, no markdown.

Schema:
{json.dumps(INVOICE_SCHEMA, indent=2)}

Invoice text:
"""


MODELS = [""]


def _parse_with_llm_text(text: str) -> dict | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    client = genai.Client(api_key=api_key)

    for attempt in range(3):
        for model in MODELS:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=LLM_PROMPT + text
                )
                raw = response.text
                clean = re.sub(r'```json|```', '', raw).strip()
                return json.loads(clean)
            except Exception as e:
                err = str(e)
                if "503" in err or "429" in err:
                    wait = (2 ** attempt) * 10  # 10s, 20s, 40s
                    print(
                        f"[LLM] Attempt {attempt+1} failed, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"[LLM] ERROR: {type(e).__name__}: {e}")
                    return None

        print("[LLM] ERROR: All retries exhausted")
        return None


# ── Plain-text fallback ───────────────────────────────────────────────────────

def _parse_from_text(text: str) -> dict:
    """Used when only plain text is available (no pdfplumber word data)."""
    def search(pattern, flags=re.IGNORECASE):
        m = re.search(pattern, text, flags)
        return m.group(1).strip() if m else None

    items = []
    pattern = re.compile(
        r'^(?!Item\b)([A-Za-z][A-Za-z0-9\s\-\/]+?)\s+\$?([\d.]+)\s+(\d+)\s+\$?([\d.]+)$',
        re.MULTILINE
    )
    for i, m in enumerate(pattern.finditer(text), start=1):
        items.append({
            "sno": i,
            "name": m.group(1).strip(),
            "unit_price": m.group(2),
            "qty": m.group(3),
            "line_total": m.group(4),
        })

    return {
        "invoice_number": search(r'Invoice Number\s+(\S+)'),
        "issue_date":     search(r'Issue Date\s+(.+)'),
        "due_date":       search(r'Due Date\s+(.+)'),
        "status":         search(r'Status\s+(\S+)'),
        "vendor":         None,
        "bill_to":        None,
        "total_amount":   search(r'(?:Amount Due|Grand Total|Total)\s+\$?([\d,]+\.?\d*)'),
        "tax_rate":       search(r'Tax Rate\s+(\S+)'),
        "payment_terms":  search(r'(Payment is due[^\n]+)'),
        "items":          items,
    }
