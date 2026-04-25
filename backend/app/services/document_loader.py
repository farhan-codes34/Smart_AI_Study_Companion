"""
document_loader.py — Extract raw text from PDF, TXT, or image files

WHY this module exists:
  Every feature (explain, quiz, voice Q&A) needs raw text first.
  We centralise all file-type handling here so the upload route
  doesn't care what format the file is — it just calls load_document()
  and gets back a plain string.

Supported formats:
  - PDF  → pdfplumber  (handles multi-page, tables, scanned-light PDFs)
  - TXT  → plain read  (utf-8 with latin-1 fallback)
  - Image → pytesseract OCR  (PNG, JPG, JPEG, WEBP, BMP, TIFF)
"""

import pdfplumber
import pytesseract
from PIL import Image
from pathlib import Path


# Allowed file extensions grouped by handler
PDF_EXTENSIONS   = {".pdf"}
TEXT_EXTENSIONS  = {".txt", ".md"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

ALL_ALLOWED = PDF_EXTENSIONS | TEXT_EXTENSIONS | IMAGE_EXTENSIONS


def load_document(file_path: str) -> str:
    """
    Main entry point — dispatch to the correct loader based on extension.

    Args:
        file_path: Absolute path to the saved upload file.

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If the file type is not supported.
        RuntimeError: If extraction fails.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        return _load_pdf(path)
    elif suffix in TEXT_EXTENSIONS:
        return _load_txt(path)
    elif suffix in IMAGE_EXTENSIONS:
        return _load_image(path)
    else:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. "
            f"Allowed: {', '.join(sorted(ALL_ALLOWED))}"
        )


# ── Private loaders ───────────────────────────────────────────────────────────

def _load_pdf(path: Path) -> str:
    """
    Extract text from every page of a PDF using pdfplumber.

    WHY pdfplumber over PyPDF2?
      pdfplumber handles layout-heavy PDFs much better and extracts
      text in reading order. It also exposes tables as structured data
      (unused here, but available for future features).
    """
    try:
        pages_text: list[str] = []

        with pdfplumber.open(str(path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    # Tag each page so chunker can see page boundaries
                    pages_text.append(f"[Page {page_num}]\n{text.strip()}")

        if not pages_text:
            raise RuntimeError(
                "No extractable text found in the PDF. "
                "If it is a scanned PDF, convert it to an image first."
            )

        # Join pages with double newline so the chunker treats them as paragraphs
        return "\n\n".join(pages_text)

    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}") from e


def _load_txt(path: Path) -> str:
    """
    Read a plain-text file with utf-8 encoding (latin-1 fallback).

    WHY two encodings?
      Many lecture notes exported from Windows tools use latin-1.
      Trying utf-8 first covers the common case; fallback prevents crashes.
    """
    try:
        try:
            return path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1").strip()
    except Exception as e:
        raise RuntimeError(f"Text file read failed: {e}") from e


def _load_image(path: Path) -> str:
    """
    Run Tesseract OCR on an image to extract text.

    WHY pytesseract?
      It wraps the open-source Tesseract engine which handles printed
      text well. For handwritten notes quality varies, but it is
      free and runs fully locally with no API key.

    Prerequisites:
      Tesseract must be installed and on PATH:
      https://github.com/UB-Mannheim/tesseract/wiki  (Windows)
    """
    try:
        image = Image.open(str(path))

        # lang="eng" = English. Add "+urd" etc. for multilingual notes.
        text = pytesseract.image_to_string(image, lang="eng")

        if not text.strip():
            raise RuntimeError(
                "OCR returned empty text. "
                "Ensure the image is clear and well-lit."
            )

        return text.strip()

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed or not on PATH. "
            "Download it from https://github.com/UB-Mannheim/tesseract/wiki"
        )
    except Exception as e:
        raise RuntimeError(f"Image OCR failed: {e}") from e
