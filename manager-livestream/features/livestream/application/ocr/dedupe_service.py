"""Dedupe service for OCR comments."""

from __future__ import annotations

import time

from .models import OCRComment


class OCRDedupeService:
    """Filter duplicate comments by (author, content) within time window."""

    def __init__(self):
        self._seen: dict[tuple[str, str], float] = {}

    def is_duplicate(self, comment: OCRComment, *, dedupe_same_user: bool, window_seconds: int) -> bool:
        if not dedupe_same_user:
            return False
        key = (
            str(comment.author or "").strip().lower(),
            str(comment.content_normalized or "").strip().lower(),
        )
        now = time.time()
        last = self._seen.get(key)
        self._seen[key] = now
        if last is None:
            return False
        return (now - last) <= max(1, int(window_seconds or 1))
