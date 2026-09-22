from __future__ import annotations

import io
from PIL import Image
import pytesseract


def extract_text(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    text = pytesseract.image_to_string(image)
    return text.strip()
