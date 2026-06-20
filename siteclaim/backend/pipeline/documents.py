"""Turn an uploaded document into images a vision model can read (Phase 7).

``to_images(file_bytes, content_type) -> list[base64-PNG]``:
  * PDF  → rasterise each page to PNG with PyMuPDF (first ``MAX_PAGES`` pages, ~150 DPI).
  * JPEG / PNG / WEBP → normalise to a single PNG (via PyMuPDF, so no Pillow needed).
  * anything else → a clear ``ValueError``.

There is no OCR step — the vision model reads the rendered image directly. PyMuPDF
(``fitz``) is imported **lazily** inside the functions, so importing this module costs
nothing and DEMO_MODE never needs the dependency installed.
"""

import base64
from typing import Optional

MAX_PAGES = 5
DEFAULT_DPI = 150


def _b64_png(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("ascii")


def _pdf_to_pngs(data: bytes, max_pages: int, dpi: int) -> list[str]:
    import fitz  # PyMuPDF — lazy

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    images: list[str] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for index in range(min(len(doc), max_pages)):
            pix = doc[index].get_pixmap(matrix=matrix, alpha=False)
            images.append(_b64_png(pix.tobytes("png")))
    if not images:
        raise ValueError("PDF has no rasterisable pages.")
    return images


def _image_to_png(data: bytes) -> str:
    import fitz  # PyMuPDF — lazy

    pix = fitz.Pixmap(data)  # loads PNG/JPEG/WEBP/… into a pixmap
    if pix.alpha or pix.colorspace is None or pix.n > 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)  # normalise to RGB
    return _b64_png(pix.tobytes("png"))


def to_images(
    file_bytes: bytes,
    content_type: Optional[str],
    *,
    max_pages: int = MAX_PAGES,
    dpi: int = DEFAULT_DPI,
) -> list[str]:
    """Rasterise an uploaded document to a list of base64-encoded PNG images."""
    if not file_bytes:
        raise ValueError("Empty file — nothing to extract.")
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct == "application/pdf" or ct.endswith("/pdf"):
        return _pdf_to_pngs(file_bytes, max_pages=max_pages, dpi=dpi)
    if ct.startswith("image/"):
        return [_image_to_png(file_bytes)]
    raise ValueError(
        f"Unsupported document type {content_type!r}. Upload a PDF, JPEG, PNG, or WEBP."
    )
