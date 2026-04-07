"""Public API for cross-feature OBS queue interactions."""

from __future__ import annotations

import threading

from features.obs.application.service import OBSService


_services_lock = threading.RLock()
_services: dict[str, OBSService] = {}


def get_obs_service(brand_id: str) -> OBSService:
    """Get brand-scoped OBS service singleton for cross-feature calls."""
    brand_key = str(brand_id or "default").strip() or "default"
    with _services_lock:
        svc = _services.get(brand_key)
        if svc is None:
            svc = OBSService(brand_key)
            _services[brand_key] = svc
        return svc


def enqueue_priority_video(brand_id: str, video_id: str, source: str = "external", trace_id: str = "") -> dict:
    """Public function to enqueue a video ID as next priority for a brand."""
    svc = get_obs_service(brand_id)
    svc.prioritize_video_by_id(video_id)
    return {
        "ok": True,
        "brand_id": brand_id,
        "video_id": video_id,
        "source": source,
        "trace_id": trace_id,
        "queue_state": svc.get_queue_state(),
    }


def set_video_cooldown_by_id(brand_id: str, video_id: str, cooldown_seconds: int, source: str = "external", trace_id: str = "") -> dict:
    """Public function to override cooldown for a brand-scoped video ID."""
    svc = get_obs_service(brand_id)
    svc.set_video_cooldown(video_id, int(cooldown_seconds))
    return {
        "ok": True,
        "brand_id": brand_id,
        "video_id": video_id,
        "cooldown_seconds": int(cooldown_seconds),
        "source": source,
        "trace_id": trace_id,
        "queue_state": svc.get_queue_state(),
    }


def get_video_catalog(brand_id: str) -> list[dict]:
    """Get persistent brand-scoped video catalog."""
    return get_obs_service(brand_id).get_video_catalog()
