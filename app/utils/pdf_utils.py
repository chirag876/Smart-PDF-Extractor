import pdfplumber

def is_scanned_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                return False
    return True

def extract_text(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def is_valid_pdf(file_path: str) -> bool:
    try:
        with pdfplumber.open(file_path) as pdf:
            _ = len(pdf.pages)
        return True
    except Exception:
        return False

def is_password_protected(file_path: str) -> bool:
    try:
        with pdfplumber.open(file_path) as pdf:
            _ = len(pdf.pages)
        return False
    except Exception as e:
        if "password" in str(e).lower():
            return True
        return False