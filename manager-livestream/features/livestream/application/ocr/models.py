"""Data models for OCR comment pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class OCRRegion:
    """Screen region used for OCR capture."""

    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def is_valid(self) -> bool:
        return self.width > 5 and self.height > 5

    def to_bbox(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class OCRLine:
    """Single OCR line with confidence."""

    text: str
    confidence: float


@dataclass
class OCRComment:
    """Parsed OCR comment message."""

    timestamp: str
    author: str
    content_raw: str
    content_normalized: str
    confidence: float

    @staticmethod
    def from_parts(author: str, content: str, content_normalized: str, confidence: float) -> "OCRComment":
        return OCRComment(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            author=str(author or ""),
            content_raw=str(content or ""),
            content_normalized=str(content_normalized or ""),
            confidence=float(confidence or 0.0),
        )


@dataclass
class OCRSettings:
    """Runtime settings for OCR worker."""

    interval_seconds: float = 1.0
    min_confidence: float = 0.75
    dedupe_same_user: bool = True
    dedupe_window_seconds: int = 45
