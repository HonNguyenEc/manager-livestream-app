"""Comment reader module with source strategies (API/OCR)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from features.livestream.config import AppConfig
from features.livestream.service import LivestreamService


@dataclass
class CommentReadResult:
    """Normalized read result for downstream comment-switch flow."""

    comments: list[str]
    source: str
    note: str


class CommentReader:
    """Read comments from selected source."""

    def __init__(self):
        self._api_service = LivestreamService()

    @staticmethod
    def _dedupe_keep_order(items: list[str]) -> list[str]:
        out: list[str] = []
        seen = set()
        for raw in items:
            text = str(raw or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return out

    def _extract_comments_from_api_result(self, payload: dict) -> list[str]:
        body = payload.get("response_body", {}) if isinstance(payload, dict) else {}
        comments: list[str] = []

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    key = str(k).lower()
                    if key in {"comment", "content", "message", "text"} and isinstance(v, (str, int, float)):
                        comments.append(str(v))
                    else:
                        walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        for key in ("comment_list", "comments", "list", "items", "data"):
            if key in body:
                walk(body.get(key))
        walk(body)
        return self._dedupe_keep_order(comments)

    def _read_from_api(self, cfg: AppConfig, session_id: str, page_size: str, cursor: str) -> CommentReadResult:
        try:
            result = self._api_service.get_comment(cfg, session_id=session_id, page_size=page_size, cursor=cursor)
            comments = self._extract_comments_from_api_result(result)
            return CommentReadResult(
                comments=comments,
                source="api",
                note=f"Đọc từ API thành công. comments={len(comments)}",
            )
        except Exception as ex:
            return CommentReadResult(
                comments=[],
                source="api",
                note=f"API get_comment lỗi hoặc chưa có quyền: {ex}",
            )

    def _read_from_ocr_file(self, file_path: str) -> CommentReadResult:
        path = Path(str(file_path or "").strip())
        if not path.exists() or not path.is_file():
            return CommentReadResult(comments=[], source="ocr_file", note="OCR file không tồn tại hoặc không hợp lệ")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")

        comments: list[str] = []
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
                comments = self._extract_comments_from_api_result({"response_body": payload})
            except Exception:
                comments = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            comments = [line.strip() for line in text.splitlines() if line.strip()]

        comments = self._dedupe_keep_order(comments)
        return CommentReadResult(comments=comments, source="ocr_file", note=f"Đọc OCR file thành công. comments={len(comments)}")

    def read_comments(
        self,
        cfg: AppConfig,
        session_id: str,
        page_size: str,
        cursor: str,
        source_type: str = "api",
        ocr_mode: str = "ui_text",
        ocr_file_path: str = "",
        ui_test_text: str = "",
        disable_ui_text: bool = False,
    ) -> CommentReadResult:
        source = str(source_type or "api").strip().lower()
        if source == "api":
            return self._read_from_api(cfg, session_id=session_id, page_size=page_size, cursor=cursor)

        mode = str(ocr_mode or "ui_text").strip().lower()
        if mode == "file":
            return self._read_from_ocr_file(ocr_file_path)

        if mode == "direct":
            return CommentReadResult(
                comments=[],
                source="ocr_direct",
                note="OCR direct chưa tích hợp adapter runtime, vui lòng dùng OCR file hoặc UI text để test.",
            )

        if disable_ui_text:
            return CommentReadResult(
                comments=[],
                source="ocr_ui_text",
                note="UI text đang bị disable.",
            )

        text = str(ui_test_text or "").strip()
        return CommentReadResult(
            comments=[text] if text else [],
            source="ocr_ui_text",
            note="Đọc comment từ UI text test.",
        )
