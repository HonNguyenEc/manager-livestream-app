"""Domain models for OBS feature."""

from dataclasses import dataclass


@dataclass
class OBSConfig:
    """Configuration required to connect and control OBS websocket."""

    host: str = "127.0.0.1"
    port: str = "4455"
    password: str = ""
    scene_name: str = ""
    source_name: str = ""
    source_a_name: str = "VideoA"
    source_b_name: str = "VideoB"
    video_folder: str = ""
    crossfade_seconds: str = "2"
    default_cooldown_seconds: str = "120"

    @staticmethod
    def from_dict(data: dict) -> "OBSConfig":
        return OBSConfig(
            host=str(data.get("host", "127.0.0.1")),
            port=str(data.get("port", "4455")),
            password=str(data.get("password", "")),
            scene_name=str(data.get("scene_name", "")),
            source_name=str(data.get("source_name", "")),
            source_a_name=str(data.get("source_a_name", "VideoA")),
            source_b_name=str(data.get("source_b_name", "VideoB")),
            video_folder=str(data.get("video_folder", "")),
            crossfade_seconds=str(data.get("crossfade_seconds", "2")),
            default_cooldown_seconds=str(data.get("default_cooldown_seconds", "120")),
        )

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "password": self.password,
            "scene_name": self.scene_name,
            "source_name": self.source_name,
            "source_a_name": self.source_a_name,
            "source_b_name": self.source_b_name,
            "video_folder": self.video_folder,
            "crossfade_seconds": self.crossfade_seconds,
            "default_cooldown_seconds": self.default_cooldown_seconds,
        }
