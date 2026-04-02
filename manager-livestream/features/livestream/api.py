"""HTTP client for Shopee livestream APIs (feature-scoped)."""

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from shared.helpers import to_num
from shared.logger import get_logger
from shared.messages import ErrorCode, err


logger = get_logger("feature.livestream.api")


class ShopeeAPIClient:
    """Low-level API client that signs requests and returns rich debug payload."""

    def __init__(self, host: str, partner_id: str, partner_key: str, shop_id: str, access_token: str, user_id: str):
        self.host = host.rstrip("/")
        self.partner_id = partner_id
        self.partner_key = partner_key
        self.shop_id = shop_id
        self.access_token = access_token
        self.user_id = user_id

    def _principal(self, require_user: bool = False):
        if require_user:
            if not self.user_id:
                raise ValueError(err(ErrorCode.USER_ID_REQUIRED))
            return "user_id", self.user_id
        if self.user_id:
            return "user_id", self.user_id
        return "shop_id", self.shop_id

    def _sign(self, path: str, timestamp: int, access_token: str = "", principal_id: str = "") -> str:
        base = f"{self.partner_id}{path}{timestamp}"
        if access_token and principal_id:
            base += f"{access_token}{principal_id}"
        return hmac.new(self.partner_key.encode(), base.encode(), hashlib.sha256).hexdigest()

    def _request(self, url: str, payload: dict | None = None, method: str = "POST"):
        """Execute HTTP request and return normalized debug response."""
        logger.info("%s %s", method, url)
        data = None
        headers = {}
        if method.upper() == "POST":
            payload = payload or {}
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method.upper(),
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                status = resp.status
                reason = getattr(resp, "reason", "OK")
                headers = dict(resp.headers.items())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            status = e.code
            reason = e.reason
            headers = dict(e.headers.items()) if e.headers else {}

        try:
            body_json = json.loads(body)
        except json.JSONDecodeError:
            body_json = {"raw_text": body}

        return {
            "request_url": url,
            "request_payload": payload or {},
            "response_status": f"{status} {reason}",
            "response_headers": headers,
            "response_body": body_json,
            "request_id": body_json.get("request_id") if isinstance(body_json, dict) else None,
        }

    def post_livestream(self, path: str, payload: dict, require_user: bool = False):
        timestamp = int(time.time())
        principal_key, principal_id = self._principal(require_user=require_user)
        sign = self._sign(path, timestamp, self.access_token, principal_id)
        url = (
            f"{self.host}{path}?partner_id={self.partner_id}&timestamp={timestamp}"
            f"&access_token={self.access_token}&sign={sign}&{principal_key}={principal_id}"
        )
        return self._request(url, payload)

    def refresh_access_token(self, refresh_token: str):
        path = "/api/v2/auth/access_token/get"
        timestamp = int(time.time())
        principal_key, principal_id = self._principal()
        sign = self._sign(path, timestamp)
        url = f"{self.host}{path}?partner_id={self.partner_id}&timestamp={timestamp}&sign={sign}"
        payload = {
            "refresh_token": refresh_token,
            "partner_id": to_num(self.partner_id),
            "shop_id": to_num(self.shop_id),
        }
        return self._request(url, payload)

    def get_shop_info(self):
        """Call v2.shop.get_shop_info via GET.

        Sign base string: partner_id + path + timestamp + access_token + shop_id
        """
        path = "/api/v2/shop/get_shop_info"
        timestamp = int(time.time())
        sign = self._sign(path, timestamp, self.access_token, self.shop_id)
        url = (
            f"{self.host}{path}?partner_id={self.partner_id}&timestamp={timestamp}"
            f"&access_token={self.access_token}&shop_id={self.shop_id}&sign={sign}"
        )
        return self._request(url, payload={}, method="GET")


class APIClientSingleton:
    """Singleton accessor to avoid recreating client for same credential set."""

    _instance = None
    _key = None

    @classmethod
    def get_client(cls, host: str, partner_id: str, partner_key: str, shop_id: str, access_token: str, user_id: str):
        key = (host, partner_id, partner_key, shop_id, access_token, user_id)
        if cls._instance is None or cls._key != key:
            cls._instance = ShopeeAPIClient(host, partner_id, partner_key, shop_id, access_token, user_id)
            cls._key = key
        return cls._instance
