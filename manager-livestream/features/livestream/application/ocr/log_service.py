"""OCR event logging service."""

from __future__ import annotations

from pathlib import Path

from shared.storage import read_json, write_json


class OCRLogService:
    """Append OCR process events for traceability.

    Stored as JSON array for easy inspection in dev/debug stage.
    """

    def append_event(self, log_path: Path, event: dict, *, max_items: int = 5000) -> None:
        items = read_json(log_path, default=[])
        if not isinstance(items, list):
            items = []
        items.append(dict(event or {}))
        if len(items) > max_items:
            items = items[-max_items:]
        write_json(log_path, items)
