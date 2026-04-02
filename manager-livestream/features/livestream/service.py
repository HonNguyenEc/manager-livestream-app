"""Business layer for livestream feature.

This module isolates validation and payload composition from UI.
"""

import json
from dataclasses import replace

from features.livestream.api import APIClientSingleton
from features.livestream.config import AppConfig
from shared.helpers import to_num
from shared.logger import get_logger
from shared.messages import ErrorCode, err


logger = get_logger("feature.livestream.service")


class LivestreamService:
    """Use-case service for Shopee livestream actions."""

    def _client(self, cfg: AppConfig):
        return APIClientSingleton.get_client(
            cfg.host,
            cfg.partner_id,
            cfg.partner_key,
            cfg.shop_id,
            cfg.access_token,
            cfg.user_id,
        )

    @staticmethod
    def validate_base_config(cfg: AppConfig):
        if not (cfg.host and cfg.partner_id and cfg.partner_key and cfg.shop_id and cfg.access_token):
            raise ValueError(err(ErrorCode.CONFIG_MISSING))

    def create_session(self, cfg: AppConfig, extra_json_text: str = "{}"):
        self.validate_base_config(cfg)
        if not cfg.user_id:
            raise ValueError(err(ErrorCode.USER_ID_REQUIRED))
        if not cfg.live_title.strip():
            raise ValueError(err(ErrorCode.TITLE_REQUIRED))
        if not cfg.live_cover_image_url.strip():
            raise ValueError(err(ErrorCode.COVER_URL_REQUIRED))

        payload = {
            "title": cfg.live_title.strip(),
            "cover_image_url": cfg.live_cover_image_url.strip(),
            "is_test": bool(cfg.live_is_test),
        }
        if cfg.live_description.strip():
            payload["description"] = cfg.live_description.strip()

        extra = json.loads(extra_json_text.strip() or "{}")
        if not isinstance(extra, dict):
            raise ValueError(err(ErrorCode.EXTRA_JSON_INVALID))
        payload.update(extra)

        logger.info("create_session payload prepared")
        return self._client(cfg).post_livestream("/api/v2/livestream/create_session", payload, require_user=True)

    def end_session(self, cfg: AppConfig, session_id: str):
        self.validate_base_config(cfg)
        return self._client(cfg).post_livestream("/api/v2/livestream/end_session", {"session_id": to_num(session_id.strip())})

    def get_comment(self, cfg: AppConfig, session_id: str, page_size: str, cursor: str):
        self.validate_base_config(cfg)
        payload = {
            "session_id": to_num(session_id.strip()),
            "page_size": to_num((page_size or "20").strip()),
        }
        if cursor.strip():
            payload["cursor"] = cursor.strip()
        return self._client(cfg).post_livestream("/api/v2/livestream/get_comment", payload)

    def refresh_access_token(self, cfg: AppConfig):
        if not (cfg.host and cfg.partner_id and cfg.partner_key and cfg.shop_id and cfg.refresh_token):
            raise ValueError(err(ErrorCode.REFRESH_CONFIG_MISSING))

        temp_cfg = replace(cfg, access_token="")
        result = self._client(temp_cfg).refresh_access_token(cfg.refresh_token)
        body = result.get("response_body", {})
        if isinstance(body, dict) and body.get("access_token"):
            return (
                replace(
                    cfg,
                    access_token=body.get("access_token", ""),
                    refresh_token=body.get("refresh_token", cfg.refresh_token),
                ),
                result,
            )
        raise ValueError(json.dumps(result, ensure_ascii=False, indent=2))

    def get_shop_info(self, cfg: AppConfig):
        """Get current shop information via v2.shop.get_shop_info."""
        self.validate_base_config(cfg)
        return self._client(cfg).get_shop_info()
