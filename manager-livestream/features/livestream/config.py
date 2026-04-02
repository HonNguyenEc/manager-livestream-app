"""Livestream feature configuration and .env persistence."""

from dataclasses import dataclass
from pathlib import Path

from shared.helpers import to_bool
from shared.storage import read_json, write_json


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
ENV_DIR = BASE_DIR / "envs"
DATA_BRANDS_DIR = BASE_DIR / "data" / "brands"
STATE_PATH = BASE_DIR / "data" / "brand_state.json"
DEFAULT_BRAND = "default"


def load_env(path: Path = ENV_PATH) -> dict:
    env = {}
    if not path.exists():
        return env

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _safe_brand_id(brand_id: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in (brand_id or "").strip().lower())
    return clean or DEFAULT_BRAND


def get_brand_env_path(brand_id: str) -> Path:
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    return ENV_DIR / f"{_safe_brand_id(brand_id)}.env"


def list_brands() -> list[str]:
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    brands = sorted(p.stem for p in ENV_DIR.glob("*.env"))
    return brands or [DEFAULT_BRAND]


def get_active_brand() -> str:
    state = read_json(STATE_PATH, default={})
    active = _safe_brand_id(state.get("active_brand", DEFAULT_BRAND))
    return active


def set_active_brand(brand_id: str) -> str:
    brand_id = _safe_brand_id(brand_id)
    write_json(STATE_PATH, {"active_brand": brand_id})
    return brand_id


def migrate_legacy_env() -> None:
    """Move legacy .env to envs/default.env once if brand envs do not exist."""
    ENV_DIR.mkdir(parents=True, exist_ok=True)
    if any(ENV_DIR.glob("*.env")):
        return
    target = get_brand_env_path(DEFAULT_BRAND)
    if ENV_PATH.exists():
        target.write_text(ENV_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        target.write_text("", encoding="utf-8")
    set_active_brand(DEFAULT_BRAND)


def load_brand_config(brand_id: str) -> "AppConfig":
    path = get_brand_env_path(brand_id)
    return AppConfig.from_env(load_env(path))


def save_brand_config(brand_id: str, config: "AppConfig") -> Path:
    path = get_brand_env_path(brand_id)
    save_config(config, path)
    return path


def ensure_brand_data_dir(brand_id: str) -> Path:
    brand_dir = DATA_BRANDS_DIR / _safe_brand_id(brand_id)
    brand_dir.mkdir(parents=True, exist_ok=True)
    return brand_dir


def create_brand(brand_id: str, config: "AppConfig") -> str:
    brand_id = _safe_brand_id(brand_id)
    save_brand_config(brand_id, config)
    ensure_brand_data_dir(brand_id)
    return brand_id


def delete_brand(brand_id: str) -> None:
    path = get_brand_env_path(brand_id)
    if path.exists():
        path.unlink()


@dataclass
class AppConfig:
    host: str
    partner_id: str
    partner_key: str
    shop_id: str
    user_id: str
    access_token: str
    refresh_token: str
    live_title: str
    live_description: str
    live_cover_image_url: str
    live_is_test: bool
    comment_page_size: str

    @staticmethod
    def from_env(env: dict) -> "AppConfig":
        return AppConfig(
            host=env.get("SHOPEE_HOST", "https://partner.shopeemobile.com"),
            partner_id=env.get("SHOPEE_PARTNER_ID", ""),
            partner_key=env.get("SHOPEE_PARTNER_KEY", ""),
            shop_id=env.get("SHOP_ID", ""),
            user_id=env.get("USER_ID", ""),
            access_token=env.get("ACCESS_TOKEN", ""),
            refresh_token=env.get("REFRESH_TOKEN", ""),
            live_title=env.get("LIVE_TITLE", "Livestream test"),
            live_description=env.get("LIVE_DESCRIPTION", ""),
            live_cover_image_url=env.get("LIVE_COVER_IMAGE_URL", ""),
            live_is_test=to_bool(env.get("LIVE_IS_TEST", "false")),
            comment_page_size=env.get("COMMENT_PAGE_SIZE", "20"),
        )

    def to_env_string(self) -> str:
        return (
            f"SHOPEE_HOST={self.host}\n"
            f"SHOPEE_PARTNER_ID={self.partner_id}\n"
            f"SHOPEE_PARTNER_KEY={self.partner_key}\n"
            f"SHOP_ID={self.shop_id}\n"
            f"USER_ID={self.user_id}\n"
            f"ACCESS_TOKEN={self.access_token}\n"
            f"REFRESH_TOKEN={self.refresh_token}\n"
            f"LIVE_TITLE={self.live_title}\n"
            f"LIVE_DESCRIPTION={self.live_description}\n"
            f"LIVE_COVER_IMAGE_URL={self.live_cover_image_url}\n"
            f"LIVE_IS_TEST={str(bool(self.live_is_test)).lower()}\n"
            f"COMMENT_PAGE_SIZE={self.comment_page_size}\n"
        )


def save_config(config: AppConfig, path: Path = ENV_PATH) -> None:
    path.write_text(config.to_env_string(), encoding="utf-8")
