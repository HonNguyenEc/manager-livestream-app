"""Parse OCR lines into normalized comment objects."""

from __future__ import annotations

import re
import unicodedata

from .models import OCRComment, OCRLine


class OCRParserService:
    """Convert OCR lines to structured comments (author + content)."""

    @staticmethod
    def normalize_text(text: str) -> str:
        raw = str(text or "").strip()
        raw = unicodedata.normalize("NFC", raw)
        raw = re.sub(r"\s+", " ", raw)
        return raw.strip()

    def parse_lines(self, lines: list[OCRLine]) -> list[OCRComment]:
        out: list[OCRComment] = []
        for line in lines:
            raw = self.normalize_text(line.text)
            if not raw:
                continue

            author = ""
            content = raw
            # Common chat shape: "username: comment"
            if ":" in raw:
                left, right = raw.split(":", 1)
                if left.strip() and right.strip():
                    author = self.normalize_text(left)
                    content = self.normalize_text(right)

            normalized = self.normalize_text(content)
            out.append(
                OCRComment.from_parts(
                    author=author,
                    content=content,
                    content_normalized=normalized,
                    confidence=float(line.confidence),
                )
            )
        return out
