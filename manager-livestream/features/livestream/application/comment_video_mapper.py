"""Convert comments + video catalog to mapping CSV and resolve video ID."""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

from features.livestream.config import ensure_brand_data_dir


def normalize_text(value: str) -> str:
    """Normalize text and try to repair common mojibake sequences.

    Example repaired pattern: 'BÃ´ng táº©y...' -> 'Bông tẩy...'
    """

    text = str(value or "")
    # Heuristic: only attempt repair for suspicious mojibake markers.
    suspicious = ("Ã", "Â", "áº", "á»", "Ä", "Å")
    if any(mark in text for mark in suspicious):
        for src_encoding in ("latin1", "cp1252"):
            try:
                fixed = text.encode(src_encoding).decode("utf-8")
                if fixed:
                    text = fixed
                    break
            except Exception:
                continue
    return text.strip()


def _remove_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _normalize_for_match(text: str) -> str:
    raw = normalize_text(text).lower()
    raw = _remove_accents(raw)
    raw = re.sub(r"[^\w\s]", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


_STOP_WORDS = {
    "sua", "vi",
    "tuoi", "hop", "bich", "ml", "chai",
}


def _tokenize(text: str) -> set[str]:
    words = set(_normalize_for_match(text).split())
    return {w for w in words if w and w not in _STOP_WORDS}


def _score(comment: str, text: str) -> int:
    comment_n = _normalize_for_match(comment)
    text_n = _normalize_for_match(text)
    w1 = _tokenize(comment)
    w2 = _tokenize(text)
    base = len(w1 & w2)
    phrase_bonus = 5 if comment_n and comment_n in text_n else 0
    return base + phrase_bonus


class CommentVideoMapper:
    """Handle CSV mapping lifecycle and matching logic."""

    FILE_NAME = "comment_video_mapping.csv"

    def mapping_path(self, brand_id: str) -> Path:
        return ensure_brand_data_dir(brand_id) / "obs" / self.FILE_NAME

    @staticmethod
    def _read_rows_with_fallback(path: Path) -> list[dict]:
        for enc in ("utf-8-sig", "utf-8", "cp1258", "cp1252", "latin1"):
            try:
                with path.open("r", encoding=enc, newline="") as f:
                    return list(csv.DictReader(f))
            except UnicodeDecodeError:
                continue
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            return list(csv.DictReader(f))

    def ensure_mapping_csv(self, brand_id: str, catalog: list[dict]) -> Path:
        path = self.mapping_path(brand_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        existing_desc: dict[str, str] = {}
        if path.exists():
            for row in self._read_rows_with_fallback(path):
                video_id = normalize_text((row or {}).get("id", ""))
                if video_id:
                    existing_desc[video_id] = normalize_text((row or {}).get("description", ""))

        rows = []
        for item in catalog:
            video_id = normalize_text(item.get("id", ""))
            if not video_id:
                continue
            name = normalize_text(Path(str(item.get("path", "")).strip()).name)
            rows.append(
                {
                    "id": video_id,
                    "name": name,
                    "description": normalize_text(existing_desc.get(video_id, "")),
                }
            )

        # utf-8-sig helps Excel on Windows open Vietnamese text correctly.
        # If CSV is being opened by Excel, writing may fail with PermissionError.
        # In that case, keep using the existing file and avoid breaking runtime flow.
        try:
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "name", "description"])
                writer.writeheader()
                writer.writerows(rows)
        except PermissionError:
            # File is locked by another process (usually Excel). Return current path as-is.
            return path

        return path

    def resolve_video_id_from_comments(self, comments: list[str], mapping_csv_path: Path) -> str | None:
        if not mapping_csv_path.exists() or not comments:
            return None

        candidates: list[tuple[str, str, str]] = []
        for row in self._read_rows_with_fallback(mapping_csv_path):
            video_id = normalize_text((row or {}).get("id", ""))
            name = normalize_text((row or {}).get("name", ""))
            description = normalize_text((row or {}).get("description", "")).lower()
            if video_id:
                candidates.append((video_id, name, description))

        best_video_id: str | None = None
        best_score = 0

        for comment in comments:
            text = normalize_text(comment)
            if not text:
                continue
            for video_id, name, description in candidates:
                score_name = _score(text, name)
                score_desc = _score(text, description)
                final_score = (score_name * 2) + score_desc
                if final_score > best_score:
                    best_score = final_score
                    best_video_id = video_id

        return best_video_id if best_score > 0 else None
