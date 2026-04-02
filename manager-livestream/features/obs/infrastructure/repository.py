"""Persistence layer for OBS feature (brand-scoped config)."""

from pathlib import Path

from features.livestream.config import ensure_brand_data_dir
from features.obs.domain.models import OBSConfig
from shared.storage import read_json, write_json


class OBSConfigRepository:
    """Read/write OBS config from/to brand-specific data directory."""

    def __init__(self, brand_id: str):
        self.brand_id = brand_id

    @property
    def config_path(self) -> Path:
        return ensure_brand_data_dir(self.brand_id) / "obs" / "config.json"

    def load(self) -> OBSConfig:
        data = read_json(self.config_path, default={})
        return OBSConfig.from_dict(data)

    def save(self, config: OBSConfig) -> None:
        write_json(self.config_path, config.to_dict())
