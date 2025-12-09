# app/services/parser_service.py
import io
import hashlib
import re
import unicodedata
from typing import Tuple

from app.cache.cv_cache import get as cache_get, set as cache_set
from app.core.config import settings


def compute_checksum(b: bytes) -> str:
    """Compute a stable checksum for the CV file bytes."""
    return hashlib.md5(b).hexdigest()


def parse_pdf_bytes(b: bytes) -> str:
    """Extract text from a PDF (non-scanned) using pdfplumber."""
    try:
        import pdfplumber
    except Exception as e:
        raise RuntimeError("pdfplumber not installed") from e

    out = []
    with pdfplumber.open(io.BytesIO(b)) as pdf:
        for p in pdf.pages:
            out.append(p.extract_text() or "")
    return "\n".join(out)


def parse_docx_bytes(b: bytes) -> str:
    """Extract text from a .docx file using python-docx."""
    try:
        import docx
    except Exception as e:
        raise RuntimeError("python-docx not installed") from e

    doc = docx.Document(io.BytesIO(b))
    return "\n".join(p.text for p in doc.paragraphs)


def clean_cv_text(text: str) -> str:
    """
    Cleans extracted CV text:
    - normalizes unicode (NFKC)
    - removes private-use and icon glyph ranges
    - removes control chars and zero-width characters
    - strips non-alphanumeric junk while preserving useful punctuation
    - collapses whitespace
    """
    if not text:
        return ""

    # 1. Normalize unicode (composes characters into common form)
    text = unicodedata.normalize("NFKC", text)

    # 2. Remove Private Use Area and other icon-like ranges
    # Private Use Area ranges: U+E000–U+F8FF, also some fonts use other blocks.
    text = re.sub(r"[\uE000-\uF8FF]", " ", text)
    # Optionally remove other symbol ranges that commonly contain icons
    text = re.sub(r"[\u2500-\u27BF]", " ", text)  # box drawing, dingbats, misc symbols

    # 3. Remove zero-width and bidi/control characters
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F]", "", text)
    # Replace other non-printable control chars with space
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

    # 4. Replace sequences of characters that are not letters/digits/punctuation with space
    # Allow common punctuation used in CVs: . , - + # : / @
    text = re.sub(r"[^A-Za-z0-9\.\,\-\+\#\:\/@\s]", " ", text)

    # 5. Remove repeated punctuation like "....." or ",,,,"
    text = re.sub(r"[\.]{2,}", ".", text)
    text = re.sub(r"[,]{2,}", ",", text)

    # 6. Normalize spacing: collapse multiple whitespace/newlines/tabs into single space
    text = re.sub(r"\s+", " ", text)

    # 7. Trim edges
    text = text.strip()

    return text


def parse_and_cache_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, bool]:
    """
    Main entry:
      - compute checksum cv_id
      - if in cache -> return cached text
      - else parse by extension (pdf/docx/txt)
      - clean and normalize text
      - store in cache (truncated according to settings.max_cv_chars)
    Returns: (cv_id, text, cached_flag)
    """
    cv_id = compute_checksum(file_bytes)

    # 1) Check cache first
    cached = cache_get(cv_id)
    if cached:
        return cv_id, cached["text"], True

    # 2) Parse based on extension
    fname = (filename or "").lower()
    if fname.endswith(".pdf"):
        text = parse_pdf_bytes(file_bytes)
    elif fname.endswith(".docx"):
        text = parse_docx_bytes(file_bytes)
    else:
        # fall back to plain text
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = str(file_bytes)

    # 3) Clean and normalize text
    text = clean_cv_text(text)

    # 4) Truncate to max_cv_chars and cache
    max_chars = int(getattr(settings, "max_cv_chars", 12000))
    text = text[:max_chars]
    cache_set(cv_id, text)

    return cv_id, text, False
