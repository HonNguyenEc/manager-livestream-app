"""Application layer for OBS feature."""

from features.obs.application.public_api import (
    enqueue_priority_video,
    get_obs_service,
    get_video_catalog,
    set_video_cooldown_by_id,
)
from features.obs.application.service import OBSService

__all__ = [
    "OBSService",
    "get_obs_service",
    "enqueue_priority_video",
    "set_video_cooldown_by_id",
    "get_video_catalog",
]
