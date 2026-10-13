from typing import Optional, Dict, Any, List
import io
from PIL import Image, ImageDraw, ImageFont

from .pdf_utils import is_pdf_bytes
from .docx_utils import docx_to_pdf_bytes,is_docx_bytes
try:
    import fitz  # type: ignore
except Exception:  # type: ignore[assignment]
    fitz = None  # type: ignore[assignment]

try:
    from PIL import Image  # type: ignore
except Exception:  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]




def pdf_bytes_to_jpeg_pages(pdf_bytes: bytes, dpi: int = 144, quality: int = 85) -> List[bytes]:
    if fitz is None or Image is None:
        raise RuntimeError("PyMuPDF and Pillow are required for pdf_bytes_to_jpeg_pages")
    if not isinstance(pdf_bytes, (bytes, bytearray)) or not is_pdf_bytes(pdf_bytes):
        raise ValueError("Input must be valid PDF bytes")
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    if not (1 <= quality <= 95):
        raise ValueError("quality must be between 1 and 95")

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        images: List[bytes] = []
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            images.append(buffer.getvalue())

        return images
    finally:
        document.close()

def docx_bytes_to_jpeg_pages(docx_bytes: bytes, dpi: int = 144, quality: int = 85) -> List[bytes]:
    if not isinstance(docx_bytes, (bytes, bytearray)) or not is_docx_bytes(docx_bytes):
        raise ValueError("Input must be valid DOCX bytes")
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    if not (1 <= quality <= 95):
        raise ValueError("quality must be between 1 and 95")

    pdf_bytes = docx_to_pdf_bytes(docx_bytes)
    if not pdf_bytes:
        raise ValueError("DOCX to PDF conversion failed")

    return pdf_bytes_to_jpeg_pages(pdf_bytes, dpi=dpi, quality=quality)


def ensure_image(file_bytes: bytes) -> bytes:
    if not file_bytes:
        raise ValueError("Empty file content")
    if is_pdf_bytes(file_bytes):
        logger.info("Converting PDF to image for roasting")
        pages = pdf_bytes_to_jpeg_pages(file_bytes, dpi=150, quality=85)
        if not pages:
            raise ValueError("Failed to convert PDF to image")
        return pages[0]
    if is_docx_bytes(file_bytes):
        logger.info("Converting DOCX to image for roasting")
        pages = docx_bytes_to_jpeg_pages(file_bytes, dpi=150, quality=85)
        if not pages:
            raise ValueError("Failed to convert DOCX to image")
        return pages[0]
    return file_bytes


def overlay_text_on_image(base_image: bytes, text: str) -> bytes:
    img = Image.open(io.BytesIO(base_image)).convert("RGB")
    w, h = img.size
    panel_w = max(int(w * 0.33), 260)
    x0 = w - panel_w
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([x0, 0, w, h], fill=(255, 255, 255, 230))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    max_width = panel_w - 24
    x = x0 + 12
    y = 12
    for para in text.split("\n"):
        words = para.strip().split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip() if line else word
            if draw.textlength(candidate, font=font) <= max_width:
                line = candidate
            else:
                draw.text((x, y), line, font=font, fill=(200, 0, 0))
                y += int(font.size * 1.4)
                line = word
        if line:
            draw.text((x, y), line, font=font, fill=(200, 0, 0))
            y += int(font.size * 1.4)
        y += int(font.size * 0.6)
    composed = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    out = io.BytesIO()
    composed.save(out, format="JPEG", quality=90, optimize=True)
    return out.getvalue()
