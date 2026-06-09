import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"