"""Persistent video ID catalog storage (brand-scoped)."""

from pathlib import Path

from features.livestream.config import ensure_brand_data_dir
from shared.storage import read_json, write_json


class OBSVideoCatalogRepository:
    """Read/write brand-scoped OBS video catalog."""

    def __init__(self, brand_id: str):
        self.brand_id = brand_id

    @property
    def catalog_path(self) -> Path:
        return ensure_brand_data_dir(self.brand_id) / "obs" / "video_catalog.json"

    def load(self) -> dict:
        data = read_json(self.catalog_path, default={})
        if not isinstance(data, dict):
            data = {}
        return {
            "schema_version": int(data.get("schema_version", 1) or 1),
            "id_counter": int(data.get("id_counter", 0) or 0),
            "qa_id_counter": int(data.get("qa_id_counter", 0) or 0),
            "videos": list(data.get("videos", []) or []),
            "qa_videos": list(data.get("qa_videos", []) or []),
        }

    def save(self, payload: dict) -> None:
        write_json(self.catalog_path, payload)
