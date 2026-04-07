"""Screen capture service for OCR region."""

from __future__ import annotations

from typing import Optional

from .models import OCRRegion


class OCRCaptureService:
    """Capture image from selected screen region.

    Uses PIL.ImageGrab if available. If not available on environment,
    returns None so caller can handle gracefully.
    """

    def capture(self, region: OCRRegion):
        if not region or not region.is_valid():
            return None
        try:
            from PIL import ImageGrab  # type: ignore
        except Exception:
            return None
        try:
            return ImageGrab.grab(bbox=region.to_bbox())
        except Exception:
            return None
