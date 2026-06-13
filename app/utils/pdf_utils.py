import pdfplumber
import base64
import os
from pdf2image import convert_from_path
from google import genai
from google.genai import types

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

def ocr_with_gemini(file_path: str) -> str:
    """
    Convert scanned PDF pages to images and extract text using Gemini Vision.
    Returns extracted text as a single string.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)

    poppler_path = os.getenv("POPPLER_PATH", None)
    # Convert PDF pages to images (200 DPI is enough for text, higher = slower)
    images = convert_from_path(file_path, dpi=200, poppler_path=poppler_path)

    extracted_pages = []

    for i, image in enumerate(images):
        # Convert PIL image to base64 PNG
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=image_b64
                            )
                        ),
                        types.Part(
                            text=(
                                "This is a scanned PDF page. Extract ALL text exactly as it appears. "
                                "Preserve line breaks and layout as much as possible. "
                                "Return only the extracted text, no commentary."
                            )
                        )
                    ]
                )
            ]
        )

        page_text = response.text.strip() if response.text else ""
        extracted_pages.append(f"[Page {i + 1}]\n{page_text}")

    return "\n\n".join(extracted_pages)