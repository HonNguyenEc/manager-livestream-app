"""Image preprocessing service to improve OCR precision."""

from __future__ import annotations


class OCRPreprocessService:
    """Apply lightweight preprocessing before OCR.

    We keep this dependency-light and optional. If PIL operations fail,
    return original image to keep pipeline resilient.
    """

    def process(self, image):
        if image is None:
            return None
        try:
            from PIL import ImageEnhance, ImageFilter, ImageOps  # type: ignore

            gray = ImageOps.grayscale(image)
            contrast = ImageEnhance.Contrast(gray).enhance(1.8)
            sharp = contrast.filter(ImageFilter.SHARPEN)
            bw = sharp.point(lambda x: 255 if x > 145 else 0, mode="1")
            return bw
        except Exception:
            return image
