"""Orchestrate comment -> mapping -> priority enqueue flow."""

from __future__ import annotations

from features.livestream.application.comment_reader import CommentReader
from features.livestream.application.comment_video_mapper import CommentVideoMapper
from features.livestream.application.ocr import OCRComment, OCRRegion, OCRRunner, OCRSettings
from features.livestream.config import AppConfig
from features.obs import enqueue_priority_video, get_video_catalog
from shared.storage import read_json, write_json


class CommentSwitchService:
    """High-level service for comment-driven video switching."""

    def __init__(self):
        self.reader = CommentReader()
        self.mapper = CommentVideoMapper()
        self.ocr_runner = OCRRunner()

    def _ocr_region_path(self, brand_id: str):
        from features.livestream.config import ensure_brand_data_dir

        return ensure_brand_data_dir(brand_id) / "obs" / "ocr_region.json"

    def ocr_log_path(self, brand_id: str):
        """Return per-brand OCR debug log file path."""
        from features.livestream.config import ensure_brand_data_dir

        return ensure_brand_data_dir(brand_id) / "obs" / "ocr_comment_log.json"

    def ensure_ocr_log_file(self, brand_id: str):
        """Ensure OCR log file exists so UI can open it immediately."""
        path = self.ocr_log_path(brand_id)
        if not path.exists():
            write_json(path, [])
        return path

    def set_ocr_region(self, brand_id: str, region: OCRRegion) -> None:
        write_json(self._ocr_region_path(brand_id), {
            "x": int(region.x),
            "y": int(region.y),
            "width": int(region.width),
            "height": int(region.height),
        })

    def get_ocr_region(self, brand_id: str) -> OCRRegion:
        payload = read_json(self._ocr_region_path(brand_id), default={})
        return OCRRegion(
            x=int((payload or {}).get("x", 0) or 0),
            y=int((payload or {}).get("y", 0) or 0),
            width=int((payload or {}).get("width", 0) or 0),
            height=int((payload or {}).get("height", 0) or 0),
        )

    def start_ocr(self, *, brand_id: str, settings: OCRSettings, on_comment) -> bool:
        region = self.get_ocr_region(brand_id)
        return self.ocr_runner.start(
            brand_id=brand_id,
            region=region,
            settings=settings,
            on_comment=on_comment,
        )

    def stop_ocr(self):
        self.ocr_runner.stop()

    def is_ocr_running(self) -> bool:
        return self.ocr_runner.is_running()

    def get_ocr_engine_status(self) -> dict:
        """Return OCR engine health status for UI debug output."""
        return self.ocr_runner.engine_status()

    def process_ocr_comment(self, *, brand_id: str, comment: OCRComment) -> dict:
        """Map one OCR comment to video and enqueue priority if matched."""

        catalog = get_video_catalog(brand_id)
        mapping_path = self.mapper.ensure_mapping_csv(brand_id, catalog)
        video_id = self.mapper.resolve_video_id_from_comments([comment.content_normalized], mapping_path)

        result = {
            "mode": "ocr_auto",
            "timestamp": comment.timestamp,
            "author": comment.author,
            "content": comment.content_raw,
            "normalized": comment.content_normalized,
            "confidence": comment.confidence,
            "mapping_csv": str(mapping_path),
            "matched_video_id": video_id,
            "enqueued": False,
            "action": "pending",
        }
        if not video_id:
            result["note"] = "OCR comment chưa match sản phẩm trong CSV mapping."
            result["action"] = "no_match"
            return result

        enqueue_result = enqueue_priority_video(
            brand_id=brand_id,
            video_id=video_id,
            source="comment_switch_ocr",
            trace_id="comment-switch-ocr",
        )
        result["enqueued"] = True
        result["enqueue_result"] = enqueue_result
        result["action"] = "enqueue"
        return result

    def run_comment_switch(
        self,
        *,
        brand_id: str,
        cfg: AppConfig,
        session_id: str,
        page_size: str,
        cursor: str,
        enabled: bool,
        source_type: str = "api",
        ocr_mode: str = "ui_text",
        ocr_file_path: str = "",
        ui_test_text: str = "",
        disable_ui_text: bool = False,
    ) -> dict:
        read_result = self.reader.read_comments(
            cfg,
            session_id=session_id,
            page_size=page_size,
            cursor=cursor,
            source_type=source_type,
            ocr_mode=ocr_mode,
            ocr_file_path=ocr_file_path,
            ui_test_text=ui_test_text,
            disable_ui_text=disable_ui_text,
        )
        comments = list(read_result.comments or [])
        catalog = get_video_catalog(brand_id)
        mapping_path = self.mapper.ensure_mapping_csv(brand_id, catalog)

        result = {
            "mode": "comment_api_stub",
            "enabled": bool(enabled),
            "reader_source": read_result.source,
            "reader_note": read_result.note,
            "source_type": str(source_type or "api"),
            "ocr_mode": str(ocr_mode or "ui_text"),
            "disable_ui_text": bool(disable_ui_text),
            "comments_count": len(comments),
            "mapping_csv": str(mapping_path),
            "matched_video_id": None,
            "enqueued": False,
        }
        if not enabled:
            result["note"] = "Comment switch đang tắt (Enable = false), chỉ cập nhật CSV mapping."
            return result

        video_id = self.mapper.resolve_video_id_from_comments(comments, mapping_path)
        result["matched_video_id"] = video_id
        if not video_id:
            result["note"] = (
                "Không match được video_id từ comment. "
                "Hãy mở CSV mapping và điền description chứa keyword cần bắt (id,name,description)."
            )
            return result

        enqueue_result = enqueue_priority_video(
            brand_id=brand_id,
            video_id=video_id,
            source="comment_switch",
            trace_id="comment-switch-auto",
        )
        result["enqueued"] = True
        result["enqueue_result"] = enqueue_result
        return result

    def run_test_comment_switch(self, *, brand_id: str, test_comment: str) -> dict:
        comments = [str(test_comment or "").strip()]
        catalog = get_video_catalog(brand_id)
        mapping_path = self.mapper.ensure_mapping_csv(brand_id, catalog)

        video_id = self.mapper.resolve_video_id_from_comments(comments, mapping_path)
        result = {
            "mode": "test_run",
            "input_comment": comments[0] if comments else "",
            "mapping_csv": str(mapping_path),
            "matched_video_id": video_id,
            "enqueued": False,
        }
        if not video_id:
            result["note"] = (
                "Test run chưa match được video_id. "
                "Hãy cập nhật cột description trong CSV mapping với keyword tương ứng comment test."
            )
            return result

        enqueue_result = enqueue_priority_video(
            brand_id=brand_id,
            video_id=video_id,
            source="comment_switch_test",
            trace_id="comment-switch-test",
        )
        result["enqueued"] = True
        result["enqueue_result"] = enqueue_result
        return result
