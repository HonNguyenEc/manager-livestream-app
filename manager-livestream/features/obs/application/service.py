"""Application service for OBS feature."""

import threading
import time
from pathlib import Path

from features.obs.domain.models import OBSConfig
from features.obs.infrastructure.client import OBSWebSocketClient
from features.obs.infrastructure.repository import OBSConfigRepository
from features.obs.infrastructure.video_catalog_repository import OBSVideoCatalogRepository


class OBSService:
    """Manage OBS websocket connection and basic scene/source operations."""

    def __init__(self, brand_id: str):
        self.brand_id = brand_id
        self.client = OBSWebSocketClient()
        self.repo = OBSConfigRepository(brand_id)
        self.catalog_repo = OBSVideoCatalogRepository(brand_id)
        self._last_error = ""
        self._lock = threading.RLock()
        self._import_queue: list[dict] = []
        self._play_queue: list[dict] = []
        self._qa_queue: list[dict] = []
        self._runner_thread = None
        self._runner_stop = threading.Event()
        self._skip_requested = False
        self._priority_ids: list[str] = []
        self._id_counter = 0
        self._qa_id_counter = 0
        self._default_cooldown_seconds = 120
        self._active_slot = "A"
        self._slots = {
            "A": {"file": "", "item": None, "started": False, "prepared": False},
            "B": {"file": "", "item": None, "started": False, "prepared": False},
        }
        self._ready_size = 3
        self._next_index = 0
        self._load_catalog()

    def load_config(self) -> OBSConfig:
        return self.repo.load()

    def save_config(self, cfg: OBSConfig) -> None:
        self.repo.save(cfg)
        try:
            self._default_cooldown_seconds = max(0, int(float(cfg.default_cooldown_seconds or "120")))
        except Exception:
            self._default_cooldown_seconds = 120

    @staticmethod
    def _parse_video_list(raw_list: list) -> list[dict]:
        result = []
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            path = str(raw.get("path", "")).strip()
            video_id = str(raw.get("id", "")).strip()
            if not path or not video_id:
                continue
            result.append(
                {
                    "id": video_id,
                    "path": path,
                    "cooldown_override_seconds": raw.get("cooldown_override_seconds"),
                    "last_played_at": raw.get("last_played_at"),
                    "blocked_until": float(raw.get("blocked_until", 0.0) or 0.0),
                }
            )
        return result

    def _load_catalog(self):
        with self._lock:
            data = self.catalog_repo.load()
            self._id_counter = int(data.get("id_counter", 0) or 0)
            self._qa_id_counter = int(data.get("qa_id_counter", 0) or 0)
            self._import_queue = self._parse_video_list(list(data.get("videos", []) or []))
            self._qa_queue = self._parse_video_list(list(data.get("qa_videos", []) or []))
            all_ids = {str(item.get("id")) for item in self._import_queue} | {str(item.get("id")) for item in self._qa_queue}
            self._priority_ids = [
                str(pid)
                for pid in list(data.get("priority_ids", []) or [])
                if str(pid) in all_ids
            ]
            if self._import_queue:
                self._next_index %= len(self._import_queue)
            else:
                self._next_index = 0
            self._sync_ready_queue_locked()

    @staticmethod
    def _serialize_video_list(items: list[dict]) -> list[dict]:
        return [
            {
                "id": item.get("id"),
                "path": item.get("path"),
                "cooldown_override_seconds": item.get("cooldown_override_seconds"),
                "last_played_at": item.get("last_played_at"),
                "blocked_until": item.get("blocked_until", 0.0),
            }
            for item in items
        ]

    def _save_catalog_locked(self):
        payload = {
            "schema_version": 1,
            "id_counter": int(self._id_counter),
            "qa_id_counter": int(self._qa_id_counter),
            "priority_ids": list(self._priority_ids),
            "videos": self._serialize_video_list(self._import_queue),
            "qa_videos": self._serialize_video_list(self._qa_queue),
        }
        self.catalog_repo.save(payload)

    def get_video_catalog(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "id": item.get("id"),
                    "path": item.get("path"),
                    "cooldown_override_seconds": item.get("cooldown_override_seconds"),
                    "last_played_at": item.get("last_played_at"),
                    "blocked_until": item.get("blocked_until", 0.0),
                }
                for item in self._import_queue
            ]

    def get_qa_catalog(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "id": item.get("id"),
                    "path": item.get("path"),
                    "cooldown_override_seconds": item.get("cooldown_override_seconds"),
                    "last_played_at": item.get("last_played_at"),
                    "blocked_until": item.get("blocked_until", 0.0),
                }
                for item in self._qa_queue
            ]

    def import_qa_videos_from_folder(self, folder: str) -> int:
        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            raise ValueError("Folder QA video không hợp lệ")
        files = sorted([str(p.resolve()) for p in folder_path.iterdir() if p.is_file() and self._is_video_file(p)])
        with self._lock:
            for file_path in files:
                self._qa_id_counter += 1
                self._qa_queue.append(
                    {
                        "id": f"QA{self._qa_id_counter:04d}",
                        "path": file_path,
                        "cooldown_override_seconds": None,
                        "last_played_at": None,
                        "blocked_until": 0.0,
                    }
                )
            self._save_catalog_locked()
        return len(files)

    def remove_qa_video(self, video_id: str):
        with self._lock:
            idx = self._index_of_qa_id_locked(video_id)
            if idx < 0:
                raise ValueError("Không tìm thấy QA video ID")
            self._qa_queue.pop(idx)
            self._priority_ids = [pid for pid in self._priority_ids if pid != video_id]
            self._save_catalog_locked()

    def clear_qa_queue(self):
        with self._lock:
            qa_ids = {str(item.get("id")) for item in self._qa_queue}
            self._qa_queue.clear()
            self._priority_ids = [pid for pid in self._priority_ids if pid not in qa_ids]
            self._save_catalog_locked()

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
            for file_path in files:
                self._id_counter += 1
                self._import_queue.append(
                    {
                        "id": f"V{self._id_counter:04d}",
                        "path": file_path,
                        "cooldown_override_seconds": None,
                        "last_played_at": None,
                        "blocked_until": 0.0,
                    }
                )
            self._sync_ready_queue_locked()
            self._save_catalog_locked()
        return len(files)

    def clear_queues(self):
        with self._lock:
            self._import_queue.clear()
            self._play_queue.clear()
            self._priority_ids.clear()
            self._next_index = 0
            self._save_catalog_locked()

    def remove_from_play_queue(self, video_id: str):
        with self._lock:
            idx = self._index_of_id_locked(video_id)
            if idx < 0:
                raise ValueError("Không tìm thấy video ID trong Queue 1")
            self._import_queue.pop(idx)
            self._priority_ids = [pid for pid in self._priority_ids if pid != video_id]
            if not self._import_queue:
                self._next_index = 0
            else:
                if idx < self._next_index:
                    self._next_index -= 1
                self._next_index %= len(self._import_queue)
            self._sync_ready_queue_locked()
            self._save_catalog_locked()

    def move_play_queue_item(self, video_id: str, direction: str):
        with self._lock:
            index = self._index_of_id_locked(video_id)
            if index < 0:
                raise ValueError("Không tìm thấy video ID trong Queue 1")
            if direction == "up" and index > 0:
                self._import_queue[index - 1], self._import_queue[index] = self._import_queue[index], self._import_queue[index - 1]
                if self._next_index == index:
                    self._next_index = index - 1
                elif self._next_index == index - 1:
                    self._next_index = index
                self._sync_ready_queue_locked()
                self._save_catalog_locked()
                return index - 1
            if direction == "down" and index < len(self._import_queue) - 1:
                self._import_queue[index + 1], self._import_queue[index] = self._import_queue[index], self._import_queue[index + 1]
                if self._next_index == index:
                    self._next_index = index + 1
                elif self._next_index == index + 1:
                    self._next_index = index
                self._sync_ready_queue_locked()
                self._save_catalog_locked()
                return index + 1
            return index

    def prioritize_video_by_id(self, video_id: str):
        with self._lock:
            in_rotate = self._index_of_id_locked(video_id) >= 0
            in_qa = self._index_of_qa_id_locked(video_id) >= 0
            if not in_rotate and not in_qa:
                raise ValueError("Không tìm thấy video ID trong Queue 1 hoặc QA")
            self._priority_ids = [pid for pid in self._priority_ids if pid != video_id]
            self._priority_ids.insert(0, video_id)
            self._sync_ready_queue_locked()
            self._save_catalog_locked()

    def set_video_cooldown(self, video_id: str, cooldown_seconds: int):
        with self._lock:
            idx = self._index_of_id_locked(video_id)
            if idx < 0:
                raise ValueError("Không tìm thấy video ID trong Queue 1")
            if cooldown_seconds < 0:
                raise ValueError("Cooldown phải >= 0")
            self._import_queue[idx]["cooldown_override_seconds"] = int(cooldown_seconds)
            self._sync_ready_queue_locked()
            self._save_catalog_locked()

    def skip_current(self):
        with self._lock:
            self._skip_requested = True

    def _next_from_play_queue(self) -> dict | None:
        with self._lock:
            picked = self._pick_next_item_locked()
            self._sync_ready_queue_locked()
            return picked

    def _move_import_to_play(self):
        with self._lock:
            self._sync_ready_queue_locked()

    def _sync_ready_queue_locked(self):
        if not self._import_queue:
            self._play_queue = []
            return 
        size = min(self._ready_size, len(self._import_queue))
        ordered = []
        seen = set()
        for pid in self._priority_ids:
            idx = self._index_of_id_locked(pid)
            if idx >= 0 and idx not in seen:
                ordered.append(self._import_queue[idx])
                seen.add(idx)
        for i in range(len(self._import_queue)):
            idx = (self._next_index + i) % len(self._import_queue)
            if idx in seen:
                continue
            ordered.append(self._import_queue[idx])
        self._play_queue = [
            {"id": item["id"], "path": item["path"], "cooldown_override_seconds": item.get("cooldown_override_seconds")}
            for item in ordered[:size]
        ]

    def _reset_slots(self):
        self._slots["A"] = {"file": "", "item": None, "started": False, "prepared": False}
        self._slots["B"] = {"file": "", "item": None, "started": False, "prepared": False}
        self._active_slot = "A"

    def _index_of_id_locked(self, video_id: str) -> int:
        for idx, item in enumerate(self._import_queue):
            if str(item.get("id", "")) == str(video_id):
                return idx
        return -1

    def _index_of_qa_id_locked(self, video_id: str) -> int:
        for idx, item in enumerate(self._qa_queue):
            if str(item.get("id", "")) == str(video_id):
                return idx
        return -1

    def _effective_cooldown_locked(self, item: dict) -> int:
        override = item.get("cooldown_override_seconds")
        if override is not None:
            try:
                return max(0, int(override))
            except Exception:
                pass
        return max(0, int(self._default_cooldown_seconds))

    def _pick_next_item_locked(self) -> dict | None:
        if not self._import_queue and not self._qa_queue:
            return None
        now = time.time()
        # ordered list of (item, rotate_idx_or_None)
        candidates: list[tuple[dict, int | None]] = []
        used_rotate: set[int] = set()
        used_qa: set[int] = set()

        # Priority items first (from either queue)
        for pid in self._priority_ids:
            r_idx = self._index_of_id_locked(pid)
            if r_idx >= 0 and r_idx not in used_rotate:
                candidates.append((self._import_queue[r_idx], r_idx))
                used_rotate.add(r_idx)
                continue
            q_idx = self._index_of_qa_id_locked(pid)
            if q_idx >= 0 and q_idx not in used_qa:
                candidates.append((self._qa_queue[q_idx], None))
                used_qa.add(q_idx)

        # Round-robin rotate videos (QA never rotates)
        for i in range(len(self._import_queue)):
            r_idx = (self._next_index + i) % len(self._import_queue)
            if r_idx not in used_rotate:
                candidates.append((self._import_queue[r_idx], r_idx))

        eligible: tuple[dict, int | None] | None = None
        fallback: tuple[dict, int | None] | None = None
        best_wait = None
        for item, r_idx in candidates:
            blocked_until = float(item.get("blocked_until") or 0.0)
            wait = blocked_until - now
            if wait <= 0:
                eligible = (item, r_idx)
                break
            if best_wait is None or wait < best_wait:
                best_wait = wait
                fallback = (item, r_idx)

        chosen = eligible if eligible is not None else fallback
        if chosen is None:
            return None
        picked, r_idx = chosen
        if r_idx is not None:
            self._next_index = (r_idx + 1) % len(self._import_queue)
        self._priority_ids = [pid for pid in self._priority_ids if pid != picked.get("id")]
        return picked

    def _mark_played_locked(self, item: dict):
        now = time.time()
        cd = self._effective_cooldown_locked(item)
        item["last_played_at"] = now
        item["blocked_until"] = now + cd
        self._save_catalog_locked()

    def _source_of(self, cfg: OBSConfig, slot: str) -> str:
        return cfg.source_a_name if slot == "A" else cfg.source_b_name

    def _play_to_slot(self, cfg: OBSConfig, slot: str, item: dict):
        file_path = str(item.get("path", ""))
        source = self._source_of(cfg, slot)
        other_slot = "B" if slot == "A" else "A"
        other_source = self._source_of(cfg, other_slot)
        self.client.set_source_order(cfg.scene_name, source, 0)
        self.client.set_source_order(cfg.scene_name, other_source, 1)
        self.client.set_media_local_file(source, file_path)
        self.client.set_source_visibility(cfg.scene_name, source, True)
        self.client.play_media(source)
        self.client.restart_media(source)
        time.sleep(0.03)
        self.client.set_source_visibility(cfg.scene_name, other_source, False)
        self._slots[slot] = {"file": file_path, "item": item, "started": True, "prepared": False}
        with self._lock:
            self._mark_played_locked(item)

    def _prepare_slot(self, cfg: OBSConfig, slot: str, item: dict):
        file_path = str(item.get("path", ""))
        source = self._source_of(cfg, slot)
        self.client.set_media_local_file(source, file_path)
        self.client.set_source_visibility(cfg.scene_name, source, False)
        self._slots[slot] = {"file": file_path, "item": item, "started": False, "prepared": True}

    def _should_reprepare_standby_locked(self, standby: str) -> bool:
        """True nếu standby slot nên bị replace bởi item priority cao hơn.

        Placeholder: hiện tại trigger khi top priority_id khác prepared item.
        Future: so sánh priority score để quyết định eviction.
        """
        slot = self._slots[standby]
        if not slot["prepared"] or slot["started"]:
            return False
        if not self._priority_ids:
            return False
        prepared_id = (slot["item"] or {}).get("id")
        return self._priority_ids[0] != prepared_id

    def _reprepare_standby_if_needed(self, cfg: OBSConfig, standby: str) -> None:
        """Replace standby slot với priority item nếu priority thay đổi."""
        with self._lock:
            should = self._should_reprepare_standby_locked(standby)
        if not should:
            return
        next_item = self._next_from_play_queue()
        if next_item:
            self._prepare_slot(cfg, standby, next_item)

    def _hide_slot(self, cfg: OBSConfig, slot: str):
        source = self._source_of(cfg, slot)
        self.client.set_source_visibility(cfg.scene_name, source, False)
        self._slots[slot] = {"file": "", "item": None, "started": False, "prepared": False}

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

        preload_ms = int(crossfade * 1000)
        switch_threshold_ms = 120

        while not self._runner_stop.is_set():
            try:
                self._move_import_to_play()
                active = self._active_slot
                standby = "B" if active == "A" else "A"
                active_source = self._source_of(cfg, active)
                self._reprepare_standby_if_needed(cfg, standby)

                if not self._slots[active]["started"]:
                    next_item = self._next_from_play_queue()
                    if next_item:
                        self._play_to_slot(cfg, active, next_item)
                    time.sleep(0.15)
                    continue

                status = self.client.get_media_status(active_source)
                remaining_ms = int(status.get("duration", 0)) - int(status.get("cursor", 0))
                nearing_end = remaining_ms > 0 and remaining_ms <= preload_ms
                should_switch_now = remaining_ms <= switch_threshold_ms

                with self._lock:
                    skip_now = self._skip_requested

                if nearing_end and not self._slots[standby]["prepared"] and not self._slots[standby]["started"]:
                    next_item = self._next_from_play_queue()
                    if next_item:
                        self._prepare_slot(cfg, standby, next_item)

                if skip_now and not self._slots[standby]["started"]:
                    if not self._slots[standby]["prepared"]:
                        next_item = self._next_from_play_queue()
                        if next_item:
                            self._prepare_slot(cfg, standby, next_item)
                    if self._slots[standby]["prepared"]:
                        self._play_to_slot(cfg, standby, self._slots[standby]["item"])
                        self._active_slot = standby
                        self._hide_slot(cfg, active)
                    with self._lock:
                        self._skip_requested = False

                state = str(status.get("state", "")).lower()
                if (should_switch_now or "ended" in state or "stopped" in state) and self._slots[standby]["prepared"]:
                    self._play_to_slot(cfg, standby, self._slots[standby]["item"])
                    self._active_slot = standby
                    self._hide_slot(cfg, active)
                elif "ended" in state or "stopped" in state:
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
                "import_queue": [
                    {
                        "id": item.get("id"),
                        "path": item.get("path"),
                        "cooldown_override_seconds": item.get("cooldown_override_seconds"),
                    }
                    for item in self._import_queue
                ],
                "play_queue": list(self._play_queue),
                "runner_running": running,
                "active_slot": self._active_slot,
                "slot_a_file": self._slots["A"]["file"],
                "slot_b_file": self._slots["B"]["file"],
            }
