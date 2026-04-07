"""OCR engine integration layer.

This service is intentionally optional: if pytesseract/Tesseract is missing,
it fails gracefully and returns no OCR lines.
"""

from __future__ import annotations

from .models import OCRLine


class OCRReaderService:
    """Read text lines from preprocessed image using OCR engine."""

    def __init__(self):
        self._last_status: dict = {"ok": False, "reason": "not_started"}
        self._last_raw_debug: dict = {
            "raw_words_all": [],
            "raw_conf_all": [],
            "raw_count_all": 0,
            "raw_joined_all": "",
            "raw_text_fallback": "",
        }

    def check_engine(self) -> dict:
        """Quick health check for pytesseract import/runtime availability."""
        try:
            import pytesseract  # type: ignore

            version = str(getattr(pytesseract, "get_tesseract_version", lambda: "unknown")())
            self._last_status = {"ok": True, "reason": "engine_ready", "version": version}
            return dict(self._last_status)
        except Exception as ex:
            self._last_status = {"ok": False, "reason": "engine_missing", "error": str(ex)}
            return dict(self._last_status)

    def last_status(self) -> dict:
        return dict(self._last_status)

    def last_raw_debug(self) -> dict:
        return dict(self._last_raw_debug)

    def read_lines(self, image, *, lang: str = "vie", min_confidence: float = 0.75) -> list[OCRLine]:
        if image is None:
            self._last_status = {"ok": False, "reason": "capture_none"}
            return []
        try:
            import pytesseract  # type: ignore
            from pytesseract import Output  # type: ignore
        except Exception as ex:
            self._last_status = {"ok": False, "reason": "engine_missing", "error": str(ex)}
            return []

        try:
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config="--oem 3 --psm 6",
                output_type=Output.DICT,
            )
        except Exception as ex:
            self._last_status = {"ok": False, "reason": "ocr_failed", "error": str(ex)}
            return []

        # Raw OCR debug (before confidence filtering)
        raw_words_all: list[str] = []
        raw_conf_all: list[float] = []
        n_raw = len(data.get("text", []))
        for i in range(n_raw):
            token = str(data.get("text", [""])[i] or "").strip()
            if not token:
                continue
            raw_words_all.append(token)
            try:
                conf_raw = float(data.get("conf", ["-1"])[i])
            except Exception:
                conf_raw = -1.0
            raw_conf_all.append(conf_raw)

        try:
            raw_text_fallback = str(
                pytesseract.image_to_string(image, lang=lang, config="--oem 3 --psm 6") or ""
            ).strip()
        except Exception:
            raw_text_fallback = ""

        self._last_raw_debug = {
            "raw_words_all": raw_words_all,
            "raw_conf_all": raw_conf_all,
            "raw_count_all": len(raw_words_all),
            "raw_joined_all": " | ".join(raw_words_all),
            "raw_text_fallback": raw_text_fallback,
        }

        lines: list[OCRLine] = []
        text_chunks: list[str] = []
        conf_chunks: list[float] = []

        def flush_line():
            if not text_chunks:
                return
            text = " ".join(chunk for chunk in text_chunks if chunk).strip()
            if not text:
                text_chunks.clear()
                conf_chunks.clear()
                return
            conf = sum(conf_chunks) / max(len(conf_chunks), 1)
            if conf >= float(min_confidence):
                lines.append(OCRLine(text=text, confidence=conf))
            text_chunks.clear()
            conf_chunks.clear()

        n = len(data.get("text", []))
        for i in range(n):
            raw = str(data.get("text", [""])[i] or "").strip()
            try:
                conf_val = float(data.get("conf", ["-1"])[i])
            except Exception:
                conf_val = -1.0

            if not raw:
                flush_line()
                continue
            if conf_val < 0:
                continue

            # pytesseract confidence is usually 0..100
            norm_conf = conf_val / 100.0 if conf_val > 1 else conf_val
            text_chunks.append(raw)
            conf_chunks.append(max(0.0, min(1.0, norm_conf)))

        flush_line()
        self._last_status = {
            "ok": True,
            "reason": "read_ok",
            "lines": len(lines),
            "lang": lang,
            "min_confidence": float(min_confidence),
            "raw_count_all": len(raw_words_all),
            "has_fallback_text": bool(raw_text_fallback),
        }
        return lines
