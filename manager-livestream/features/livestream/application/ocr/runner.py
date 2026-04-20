"""OCR runner orchestrates capture -> preprocess -> read -> parse pipeline."""

from __future__ import annotations

import threading
import time
from dataclasses import asdict
from typing import Callable

from features.livestream.config import ensure_brand_data_dir
from shared.logger import get_logger

from .capture_service import OCRCaptureService
from .dedupe_service import OCRDedupeService
from .log_service import OCRLogService
from .models import OCRComment, OCRRegion, OCRSettings
from .parser_service import OCRParserService
from .preprocess_service import OCRPreprocessService
from .reader_service import OCRReaderService


class OCRRunner:
    """Background OCR loop with callback for each valid new comment."""

    def __init__(self):
        self.capture_service = OCRCaptureService()
        self.preprocess_service = OCRPreprocessService()
        self.reader_service = OCRReaderService()
        self.parser_service = OCRParserService()
        self.dedupe_service = OCRDedupeService()
        self.log_service = OCRLogService()

        self._running = False
        self._thread: threading.Thread | None = None
        self._log = get_logger("ocr.runner")
        status = self.reader_service.check_engine()
        if status.get("ok"):
            self._log.passed(f"Tesseract ready version={status.get('version', '?')}")  # type: ignore[attr-defined]
        else:
            self._log.error(f"Tesseract not available — {status.get('reason', '')} {status.get('error', '')}")

    def is_running(self) -> bool:
        return bool(self._running)

    def engine_status(self) -> dict:
        return self.reader_service.check_engine()

    def start(
        self,
        *,
        brand_id: str,
        region: OCRRegion,
        settings: OCRSettings,
        on_comment: Callable[[OCRComment], dict | None],
    ) -> bool:
        if self._running:
            return True
        if not region.is_valid():
            return False

        self._running = True
        self._log.info(f"OCR started brand={brand_id} region={region}")
        self._thread = threading.Thread(
            target=self._run_loop,
            kwargs={
                "brand_id": brand_id,
                "region": region,
                "settings": settings,
                "on_comment": on_comment,
            },
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        self._log.info("OCR stopped")

    def _run_loop(self, *, brand_id: str, region: OCRRegion, settings: OCRSettings, on_comment: Callable[[OCRComment], dict | None]):
        log_path = ensure_brand_data_dir(brand_id) / "obs" / "ocr_comment_log.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        while self._running:
            try:
                image = self.capture_service.capture(region)
                if image is None:
                    time.sleep(max(0.3, float(settings.interval_seconds or 1.0)))
                    continue
                image = self.preprocess_service.process(image)
                lines = self.reader_service.read_lines(image, lang="vie", min_confidence=settings.min_confidence)
                comments = self.parser_service.parse_lines(lines)

                for c in comments:
                    is_dup = self.dedupe_service.is_duplicate(
                        c,
                        dedupe_same_user=settings.dedupe_same_user,
                        window_seconds=settings.dedupe_window_seconds,
                    )
                    if is_dup:
                        # Duplicate comments are intentionally suppressed from logs.
                        continue

                    self._log.info(f"Comment [{c.author}]: {c.content_normalized}")
                    self.log_service.append_event(
                        log_path,
                        {
                            **asdict(c),
                            "action": "comment_detected",
                        },
                    )

                    process_result = on_comment(c) or {}
                    action = str((process_result or {}).get("action", "")).strip().lower()
                    if action == "enqueue":
                        self.log_service.append_event(
                            log_path,
                            {
                                **asdict(c),
                                "action": "comment_enqueued",
                                "matched_video_id": process_result.get("matched_video_id"),
                            },
                        )
                    elif action == "no_match":
                        self.log_service.append_event(
                            log_path,
                            {
                                **asdict(c),
                                "action": "comment_no_match",
                                "reason": process_result.get("note", ""),
                            },
                        )

            except Exception as ex:
                self._log.error(f"OCR loop error: {ex}")

            time.sleep(max(0.3, float(settings.interval_seconds or 1.0)))
