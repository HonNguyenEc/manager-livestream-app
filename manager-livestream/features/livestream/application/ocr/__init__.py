"""OCR application package for livestream comment reading.

This package is intentionally split by single responsibility so each concern
(capture, preprocess, OCR read, parse, dedupe, log, runner) can evolve safely.
"""

from .models import OCRComment, OCRLine, OCRRegion, OCRSettings
from .runner import OCRRunner

__all__ = [
    "OCRComment",
    "OCRLine",
    "OCRRegion",
    "OCRSettings",
    "OCRRunner",
]
