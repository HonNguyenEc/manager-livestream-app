"""Application service for OBS feature."""

import threading
import time
from pathlib import Path

from features.obs.domain.models import OBSConfig
from features.obs.infrastructure.client import OBSWebSocketClient
from features.obs.infrastructure.repository import OBSConfigRepository


class OBSService:
    """Manage OBS websocket connection and basic scene/source operations."""

    def __init__(self, brand_id: str):
        self.brand_id = brand_id
        self.client = OBSWebSocketClient()
        self.repo = OBSConfigRepository(brand_id)
        self._last_error = ""
        self._lock = threading.RLock()
        self._import_queue: list[str] = []
        self._play_queue: list[str] = []
        self._runner_thread = None
        self._runner_stop = threading.Event()
        self._skip_requested = False
        self._active_slot = "A"
        self._slots = {
            "A": {"file": "", "started": False},
            "B": {"file": "", "started": False},
        }
        self._ready_size = 3
        self._next_index = 0

    def load_config(self) -> OBSConfig:
        return self.repo.load()

    def save_config(self, cfg: OBSConfig) -> None:
        self.repo.save(cfg)

    def status_text(self) -> str:
        if self.client.connected:
            return "Đang connect"
        if self._last_error:
            return f"Mất connect ({self._last_error})"
        return "Mất connect"

    def connect(self, cfg: OBSConfig) -> dict:
        try:
            version = self.client.connect(host=cfg.host.strip(), port=int(cfg.port.strip()), password=cfg.password.strip(), timeout=3)
            self._last_error = ""
            self.save_config(cfg)
            return version
        except Exception as ex:
            self.client.disconnect()
            self._last_error = str(ex)
            raise RuntimeError(f"Connect OBS thất bại: {ex}") from ex

    def disconnect(self):
        self.client.disconnect()

    def reload(self, cfg: OBSConfig) -> dict:
        self.disconnect()
        return self.connect(cfg)

    def list_scenes(self) -> list[str]:
        return self.client.list_scenes()

    def list_sources(self, scene_name: str) -> list[str]:
        return self.client.list_sources(scene_name)

    def set_current_scene(self, scene_name: str) -> None:
        self.client.set_current_scene(scene_name)

    @staticmethod
    def _is_video_file(path: Path) -> bool:
        return path.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}

    def import_videos_from_folder(self, folder: str) -> int:
        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError("Folder video không hợp lệ")
        files = sorted([str(p.resolve()) for p in folder_path.iterdir() if p.is_file() and self._is_video_file(p)])
        with self._lock:
            self._import_queue.extend(files)
            self._sync_ready_queue_locked()
        return len(files)

    def clear_queues(self):
        with self._lock:
            self._import_queue.clear()
            self._play_queue.clear()
            self._next_index = 0

    def remove_from_play_queue(self, index: int):
        with self._lock:
            if index < 0 or index >= len(self._import_queue):
                raise ValueError("Vị trí video không hợp lệ")
            self._import_queue.pop(index)
            if not self._import_queue:
                self._next_index = 0
            else:
                if index < self._next_index:
                    self._next_index -= 1
                self._next_index %= len(self._import_queue)
            self._sync_ready_queue_locked()

    def move_play_queue_item(self, index: int, direction: str):
        with self._lock:
            if index < 0 or index >= len(self._import_queue):
                raise ValueError("Vị trí video không hợp lệ")
            next_file = self._import_queue[self._next_index] if self._import_queue else None
            if direction == "up" and index > 0:
                self._import_queue[index - 1], self._import_queue[index] = self._import_queue[index], self._import_queue[index - 1]
                if next_file in self._import_queue:
                    self._next_index = self._import_queue.index(next_file)
                self._sync_ready_queue_locked()
                return index - 1
            if direction == "down" and index < len(self._import_queue) - 1:
                self._import_queue[index + 1], self._import_queue[index] = self._import_queue[index], self._import_queue[index + 1]
                if next_file in self._import_queue:
                    self._next_index = self._import_queue.index(next_file)
                self._sync_ready_queue_locked()
                return index + 1
            return index

    def skip_current(self):
        with self._lock:
            self._skip_requested = True

    def _next_from_play_queue(self) -> str:
        with self._lock:
            if self._import_queue:
                picked = self._import_queue[self._next_index]
                self._next_index = (self._next_index + 1) % len(self._import_queue)
                self._sync_ready_queue_locked()
                return picked
            return ""

    def _move_import_to_play(self):
        with self._lock:
            self._sync_ready_queue_locked()

    def _sync_ready_queue_locked(self):
        if not self._import_queue:
            self._play_queue = []
            return
        size = min(self._ready_size, len(self._import_queue))
        self._play_queue = [self._import_queue[(self._next_index + i) % len(self._import_queue)] for i in range(size)]

    def _reset_slots(self):
        self._slots["A"] = {"file": "", "started": False}
        self._slots["B"] = {"file": "", "started": False}
        self._active_slot = "A"

    def _source_of(self, cfg: OBSConfig, slot: str) -> str:
        return cfg.source_a_name if slot == "A" else cfg.source_b_name

    def _play_to_slot(self, cfg: OBSConfig, slot: str, file_path: str):
        source = self._source_of(cfg, slot)
        other_slot = "B" if slot == "A" else "A"
        other_source = self._source_of(cfg, other_slot)
        self.client.set_media_local_file(source, file_path)
        self.client.set_source_visibility(cfg.scene_name, source, True)
        self.client.play_media(source)
        self.client.restart_media(source)
        self.client.set_source_visibility(cfg.scene_name, other_source, False)
        self._slots[slot] = {"file": file_path, "started": True}

    def _hide_slot(self, cfg: OBSConfig, slot: str):
        source = self._source_of(cfg, slot)
        self.client.set_source_visibility(cfg.scene_name, source, False)
        self._slots[slot] = {"file": "", "started": False}

    def _validate_sources(self, cfg: OBSConfig):
        scenes = self.list_scenes()
        if cfg.scene_name not in scenes:
            raise RuntimeError(f"Scene '{cfg.scene_name}' không tồn tại")
        sources = self.list_sources(cfg.scene_name)
        if cfg.source_a_name not in sources:
            raise RuntimeError(f"Source A '{cfg.source_a_name}' không tồn tại trong scene")
        if cfg.source_b_name not in sources:
            raise RuntimeError(f"Source B '{cfg.source_b_name}' không tồn tại trong scene")

    def start_queue_runner(self, cfg: OBSConfig):
        if not self.client.connected:
            raise RuntimeError("OBS chưa connect")
        self._validate_sources(cfg)
        with self._lock:
            if self._runner_thread and self._runner_thread.is_alive():
                return
            self._runner_stop.clear()
            self._skip_requested = False
            self._reset_slots()
            self._runner_thread = threading.Thread(target=self._runner_loop, args=(cfg,), daemon=True)
            self._runner_thread.start()

    def stop_queue_runner(self):
        self._runner_stop.set()
        t = self._runner_thread
        if t and t.is_alive():
            t.join(timeout=1.2)
        self._runner_thread = None

    def _runner_loop(self, cfg: OBSConfig):
        try:
            crossfade = max(0.2, float(cfg.crossfade_seconds or "2"))
        except Exception:
            crossfade = 2.0

        while not self._runner_stop.is_set():
            try:
                self._move_import_to_play()
                active = self._active_slot
                standby = "B" if active == "A" else "A"
                active_source = self._source_of(cfg, active)

                if not self._slots[active]["started"]:
                    next_file = self._next_from_play_queue()
                    if next_file:
                        self._play_to_slot(cfg, active, next_file)
                    time.sleep(0.15)
                    continue

                status = self.client.get_media_status(active_source)
                remaining_ms = int(status.get("duration", 0)) - int(status.get("cursor", 0))
                nearing_end = remaining_ms > 0 and remaining_ms <= int(crossfade * 1000)

                with self._lock:
                    skip_now = self._skip_requested

                if (nearing_end or skip_now) and not self._slots[standby]["started"]:
                    next_file = self._next_from_play_queue()
                    if next_file:
                        self._play_to_slot(cfg, standby, next_file)
                        self._active_slot = standby
                        self._hide_slot(cfg, active)
                        with self._lock:
                            self._skip_requested = False
                    elif skip_now:
                        with self._lock:
                            self._skip_requested = False

                state = str(status.get("state", "")).lower()
                if "ended" in state or "stopped" in state:
                    self._hide_slot(cfg, active)

            except Exception as ex:
                self._last_error = str(ex)
            time.sleep(0.15)

        try:
            self._hide_slot(cfg, "A")
            self._hide_slot(cfg, "B")
        except Exception:
            pass

    def get_queue_state(self) -> dict:
        with self._lock:
            running = self._runner_thread is not None and self._runner_thread.is_alive()
            return {
                "import_queue": list(self._import_queue),
                "play_queue": list(self._play_queue),
                "runner_running": running,
                "active_slot": self._active_slot,
                "slot_a_file": self._slots["A"]["file"],
                "slot_b_file": self._slots["B"]["file"],
            }
