"""Main livestream UI assembled from reusable components."""

import json
import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from features.livestream.config import (
    AppConfig,
    create_brand,
    delete_brand,
    ensure_brand_data_dir,
    get_active_brand,
    list_brands,
    load_brand_config,
    migrate_legacy_env,
    save_brand_config,
    set_active_brand,
)
from features.livestream.application import CommentSwitchService
from features.livestream.application.ocr import OCRRegion, OCRSettings
from features.livestream.application.comment_video_mapper import normalize_text
from features.livestream.service import LivestreamService
from features.livestream.ui.components.action_tabs import ActionTabs, ShopInfoTab
from features.livestream.ui.components.brand_panel import BrandPanel
from features.livestream.ui.components.config_panel import ConfigPanel
from features.livestream.ui.components.output_panel import OutputPanel
from features.obs.application.service import OBSService
from features.obs.domain.models import OBSConfig
from features.obs.ui.panel import OBSPanel
from shared.logger import get_logger
from shared.messages import UI_MESSAGES
from shared.storage import read_json, write_json


logger = get_logger("feature.livestream.ui")


class LiveShopeeManagerUI:
    """Feature root UI class orchestrating components + async service calls."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Shopee Livestream Manager")
        self.root.geometry("1080x760")

        self.service = LivestreamService()
        self.comment_switch_service = CommentSwitchService()
        self._result_queue: queue.Queue = queue.Queue()
        self.brand_sessions: dict[str, dict] = {}
        self.obs_services: dict[str, OBSService] = {}
        self.active_brand = "default"
        migrate_legacy_env()

        self._build_ui()
        self._load_defaults()
        self._poll_queue()
        self._poll_obs_queue_state()

    def _build_ui(self):
        self._setup_styles()

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        header = tk.Label(
            container,
            text="Shopee Manager • Livestream Console",
            font=("Segoe UI", 16, "bold"),
            bg="#1f6aa5",
            fg="white",
            padx=12,
            pady=10,
        )
        header.pack(fill="x", pady=(0, 10))

        toolbar = ttk.Frame(container)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Label(toolbar, text="Active Brand:").pack(side="left")
        self.brand_var = tk.StringVar()
        self.brand_combo = ttk.Combobox(toolbar, textvariable=self.brand_var, state="readonly", width=24)
        self.brand_combo.pack(side="left", padx=6)
        self.brand_combo.bind("<<ComboboxSelected>>", self._on_switch_brand)

        root_tabs = ttk.Notebook(container, style="App.TNotebook")
        root_tabs.pack(fill="both", expand=True)

        config_tab = ttk.Frame(root_tabs, style="Card.TFrame", padding=10)
        livestream_tab = ttk.Frame(root_tabs, style="Card.TFrame", padding=10)
        shop_tab = ttk.Frame(root_tabs, style="Card.TFrame", padding=10)
        obs_tab = ttk.Frame(root_tabs, style="Card.TFrame", padding=10)

        root_tabs.add(config_tab, text="Config")
        root_tabs.add(livestream_tab, text="Livestream")
        root_tabs.add(shop_tab, text="Shop")
        root_tabs.add(obs_tab, text="OBS")

        self.config_panel = ConfigPanel(
            config_tab,
            on_save=self.save_env,
            on_refresh_token=self.refresh_access_token_async,
        )
        self.brand_panel = BrandPanel(config_tab, on_create_brand=self.create_brand_action, on_delete_brand=self.delete_brand_action)
        self.action_tabs = ActionTabs(
            livestream_tab,
            on_create=self.create_session_async,
            on_end=self.end_session_async,
            on_get_comment=self.get_comment_async,
            on_test_comment_switch=self.test_comment_switch_async,
            on_open_mapping_csv=self.open_mapping_csv,
            on_open_ocr_log=self.open_ocr_log,
            on_select_ocr_region=self.select_ocr_region,
            on_start_ocr=self.start_ocr,
            on_stop_ocr=self.stop_ocr,
        )
        self.shop_info_tab = ShopInfoTab(shop_tab, on_get_shop_info=self.get_shop_info_async)
        self.obs_panel = OBSPanel(
            obs_tab,
            on_connect=self.obs_connect,
            on_disconnect=self.obs_disconnect,
            on_reload=self.obs_reload,
            on_load_config_file=self.obs_load_config_file,
            on_load_scenes=self.obs_load_scenes,
            on_load_sources=self.obs_load_sources,
            on_apply_scene=self.obs_apply_scene,
            on_choose_folder=self.obs_choose_video_folder,
            on_import_videos=self.obs_import_videos,
            on_start_queue=self.obs_start_queue,
            on_stop_queue=self.obs_stop_queue,
            on_clear_queue=self.obs_clear_queue,
            on_remove_video=self.obs_remove_video,
            on_move_up_video=self.obs_move_up_video,
            on_move_down_video=self.obs_move_down_video,
            on_skip_video=self.obs_skip_video,
            on_prioritize_video=self.obs_prioritize_video,
            on_set_video_cooldown=self.obs_set_video_cooldown,
        )
        self.obs_panel.frame.pack(fill="both", expand=True)
        self.output_panel = OutputPanel(container)

    def _setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TNotebook", background="#f2f6fb", borderwidth=0)
        style.configure("App.TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 10, "bold"))
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", "#1f6aa5"), ("!selected", "#d9e6f5")],
            foreground=[("selected", "white"), ("!selected", "#1f2d3d")],
        )
        style.configure("Card.TFrame", background="#f7f9fc")

    def _load_defaults(self):
        brands = list_brands()
        self.brand_combo["values"] = brands
        self.active_brand = get_active_brand()
        if self.active_brand not in brands:
            self.active_brand = brands[0]
        self.brand_var.set(self.active_brand)
        self._load_brand_to_ui(self.active_brand)

    def _snapshot_ui(self) -> dict:
        return {
            "config": self._current_config(),
            "output": self.output_panel.get_text(),
            "extra_json": self.action_tabs.create.get_extra_json_text(),
            "end_session_id": self.action_tabs.end.session_id_var.get(),
            "comment_session_id": self.action_tabs.comment.session_id_var.get(),
            "comment_cursor": self.action_tabs.comment.cursor_var.get(),
            "comment_enable_switch": bool(self.action_tabs.comment.enable_switch_var.get()),
            "comment_test_text": self.action_tabs.comment.test_comment_var.get(),
            "comment_source": self.action_tabs.comment.source_var.get(),
            "comment_use_ui_text": bool(self.action_tabs.comment.use_ui_text_var.get()),
            "comment_dedupe_same_user": bool(self.action_tabs.comment.dedupe_same_user_var.get()),
        }

    def _restore_session(self, session: dict):
        cfg: AppConfig = session["config"]
        self.config_panel.set_values(cfg)
        self.action_tabs.set_values(cfg)
        self.output_panel.set_text(session.get("output", ""))
        self.action_tabs.create.extra_text.delete("1.0", "end")
        self.action_tabs.create.extra_text.insert("1.0", session.get("extra_json", "{}"))
        self.action_tabs.end.session_id_var.set(session.get("end_session_id", ""))
        self.action_tabs.comment.session_id_var.set(session.get("comment_session_id", ""))
        self.action_tabs.comment.cursor_var.set(session.get("comment_cursor", ""))
        self.action_tabs.comment.enable_switch_var.set(bool(session.get("comment_enable_switch", False)))
        self.action_tabs.comment.test_comment_var.set(session.get("comment_test_text", ""))
        self.action_tabs.comment.source_var.set(session.get("comment_source", "api"))
        self.action_tabs.comment.use_ui_text_var.set(bool(session.get("comment_use_ui_text", True)))
        self.action_tabs.comment.dedupe_same_user_var.set(bool(session.get("comment_dedupe_same_user", True)))
        self.action_tabs.comment._refresh_status_labels()
        self.action_tabs.comment.set_ocr_status(self.comment_switch_service.is_ocr_running())

    def _load_brand_to_ui(self, brand_id: str):
        if brand_id in self.brand_sessions:
            self._restore_session(self.brand_sessions[brand_id])
            self._load_shop_info_view(brand_id)
            self._load_obs_view(brand_id)
            return
        cfg = load_brand_config(brand_id)
        self.config_panel.set_values(cfg)
        self.action_tabs.set_values(cfg)
        self.output_panel.clear()
        self._load_shop_info_view(brand_id)
        self._load_obs_view(brand_id)

    def _shop_info_path(self, brand_id: str) -> Path:
        return ensure_brand_data_dir(brand_id) / "shop_info.json"

    def _load_shop_info_view(self, brand_id: str):
        payload = read_json(self._shop_info_path(brand_id), default={})
        self.shop_info_tab.set_shop_info(payload)

    def _obs_service(self, brand_id: str) -> OBSService:
        svc = self.obs_services.get(brand_id)
        if svc is None:
            svc = OBSService(brand_id)
            self.obs_services[brand_id] = svc
        return svc

    def _load_obs_view(self, brand_id: str):
        svc = self._obs_service(brand_id)
        self.obs_panel.set_config(svc.load_config())
        self.obs_panel.set_status(svc.status_text())
        queue_state = svc.get_queue_state()
        self.obs_panel.set_queue_state(queue_state)
        self._set_comment_video_status(queue_state)

    @staticmethod
    def _basename_or_dash(path_text: str) -> str:
        text = str(path_text or "").strip()
        if not text:
            return "-"
        return normalize_text(os.path.basename(text))

    def _set_comment_video_status(self, queue_state: dict):
        active_slot = str((queue_state or {}).get("active_slot", "A")).upper()
        slot_a = str((queue_state or {}).get("slot_a_file", ""))
        slot_b = str((queue_state or {}).get("slot_b_file", ""))
        now_file = slot_a if active_slot == "A" else slot_b

        play_queue = list((queue_state or {}).get("play_queue", []) or [])
        up_next_file = ""
        if play_queue:
            first = play_queue[0] if isinstance(play_queue[0], dict) else {}
            up_next_file = str(first.get("path", ""))
            if up_next_file and os.path.normcase(up_next_file) == os.path.normcase(now_file) and len(play_queue) > 1:
                second = play_queue[1] if isinstance(play_queue[1], dict) else {}
                up_next_file = str(second.get("path", ""))

        self.action_tabs.comment.set_video_status(
            now_playing=self._basename_or_dash(now_file),
            up_next=self._basename_or_dash(up_next_file),
        )

    def _current_config(self) -> AppConfig:
        return self.config_panel.to_config(self.action_tabs.get_live_config())

    def _append(self, text: str):
        self.output_panel.append(text)

    def _poll_queue(self):
        try:
            while True:
                kind, brand_id, data = self._result_queue.get_nowait()
                session = self.brand_sessions.setdefault(brand_id, {"config": self._current_config(), "output": ""})
                if kind == "token_update":
                    session["config"] = data
                    save_brand_config(brand_id, data)
                    msg = f"[SUCCESS][{brand_id}]\n{UI_MESSAGES['token_refresh_success']}"
                    session["output"] = (session.get("output", "") + "\n" + msg).strip()
                    if brand_id == self.active_brand:
                        self.config_panel.update_tokens(data)
                        self._append(msg)
                elif kind == "shop_info":
                    session["shop_info"] = data
                    if brand_id == self.active_brand:
                        self.shop_info_tab.set_shop_info(data)
                elif kind == "ocr_comment":
                    payload = data if isinstance(data, dict) else {"raw": str(data)}
                    text = f"[OCR][{brand_id}]\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
                    session["output"] = (session.get("output", "") + "\n" + text).strip()
                    if brand_id == self.active_brand:
                        self._append(text)
                        action = str(payload.get("action", "")).strip()
                        matched = str(payload.get("matched_video_id", "") or "-")
                        self._append(
                            f"[OCR-DEBUG][{brand_id}] action={action or '-'} | matched_video_id={matched} | "
                            "log fields: timestamp, author, content, normalized, confidence, action, note"
                        )
                else:
                    prefix = "[SUCCESS]" if kind == "ok" else "[ERROR]"
                    text = f"{prefix}[{brand_id}]\n{data}"
                    session["output"] = (session.get("output", "") + "\n" + text).strip()
                    if brand_id == self.active_brand:
                        self._append(text)
        except queue.Empty:
            pass
        finally:
            self.root.after(120, self._poll_queue)

    def _poll_obs_queue_state(self):
        try:
            svc = self._obs_service(self.active_brand)
            queue_state = svc.get_queue_state()
            self.obs_panel.set_queue_state(queue_state)
            self._set_comment_video_status(queue_state)
        except Exception:
            pass
        finally:
            self.root.after(350, self._poll_obs_queue_state)

    def open_mapping_csv(self):
        try:
            brand_id = self.active_brand
            catalog = self._obs_service(brand_id).get_video_catalog()
            mapping_path = self.comment_switch_service.mapper.ensure_mapping_csv(brand_id, catalog)

            if os.name == "nt":
                os.startfile(str(mapping_path))  # type: ignore[attr-defined]
            elif os.name == "posix":
                subprocess.Popen(["xdg-open", str(mapping_path)])
            else:
                subprocess.Popen(["open", str(mapping_path)])

            self._append(f"[SUCCESS][{brand_id}] Đã mở file mapping CSV: {mapping_path}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Mở mapping CSV lỗi: {ex}")

    def open_ocr_log(self):
        try:
            brand_id = self.active_brand
            log_path = self.comment_switch_service.ensure_ocr_log_file(brand_id)

            if os.name == "nt":
                os.startfile(str(log_path))  # type: ignore[attr-defined]
            elif os.name == "posix":
                subprocess.Popen(["xdg-open", str(log_path)])
            else:
                subprocess.Popen(["open", str(log_path)])

            self._append(f"[SUCCESS][{brand_id}] Đã mở OCR log: {log_path}")
            self._append(
                "[OCR-DEBUG] Log gồm: timestamp, author, content_raw, content_normalized, confidence, "
                "action (accept/skip_duplicate/no_match/enqueue), dedupe settings."
            )
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Mở OCR log lỗi: {ex}")

    def _on_switch_brand(self, _event=None):
        selected = self.brand_var.get().strip()
        if not selected:
            return
        self.brand_sessions[self.active_brand] = self._snapshot_ui()
        self.active_brand = set_active_brand(selected)
        self._load_brand_to_ui(self.active_brand)

    def create_brand_action(self):
        try:
            brand_id = self.brand_panel.brand_name_var.get().strip()
            if not brand_id:
                raise ValueError("Brand ID không được để trống")

            current_values = list(self.brand_combo["values"])
            if brand_id in current_values:
                raise ValueError(f"Brand '{brand_id}' đã tồn tại")

            cfg = AppConfig(
                host="https://partner.shopeemobile.com",
                partner_id="",
                partner_key="",
                shop_id="",
                user_id="",
                access_token="",
                refresh_token="",
                live_title="Livestream test",
                live_description="",
                live_cover_image_url="",
                live_is_test=False,
                comment_page_size="20",
            )
            brand_id = create_brand(brand_id, cfg)
            ensure_brand_data_dir(brand_id)

            if brand_id not in current_values:
                current_values.append(brand_id)
            self.brand_combo["values"] = sorted(current_values)
            self.brand_var.set(brand_id)
            self._on_switch_brand()
            self.brand_panel.brand_name_var.set("")
        except Exception as ex:
            messagebox.showerror("Create Brand Error", str(ex))

    def delete_brand_action(self):
        if self.active_brand == "default":
            messagebox.showwarning("Cảnh báo", "Không thể xoá brand default")
            return
        to_delete = self.active_brand
        confirmed = messagebox.askyesno(
            "Xác nhận xoá brand",
            f"Bạn có chắc muốn xoá brand '{to_delete}' không?\nThao tác này sẽ xoá file env của brand.",
        )
        if not confirmed:
            return
        delete_brand(to_delete)
        if to_delete in self.brand_sessions:
            del self.brand_sessions[to_delete]
        values = [v for v in self.brand_combo["values"] if v != to_delete]
        if not values:
            values = ["default"]
            create_brand("default", load_brand_config("default"))
        self.brand_combo["values"] = values
        self.brand_var.set(values[0])
        self._on_switch_brand()

    def _run_async(self, worker):
        threading.Thread(target=worker, daemon=True).start()

    def create_session_async(self):
        self._run_async(self._create_session_worker)

    def _create_session_worker(self):
        brand_id = self.active_brand
        try:
            cfg = self._current_config()
            result = self.service.create_session(cfg, self.action_tabs.create.get_extra_json_text())
            self._result_queue.put(("ok", brand_id, json.dumps(result, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("create_session failed")
            self._result_queue.put(("err", brand_id, str(ex)))

    def end_session_async(self):
        self._run_async(self._end_session_worker)

    def _end_session_worker(self):
        brand_id = self.active_brand
        try:
            cfg = self._current_config()
            result = self.service.end_session(cfg, self.action_tabs.end.session_id_var.get())
            self._result_queue.put(("ok", brand_id, json.dumps(result, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("end_session failed")
            self._result_queue.put(("err", brand_id, str(ex)))

    def get_comment_async(self):
        self._run_async(self._get_comment_worker)

    def _pick_screen_region(self) -> OCRRegion | None:
        """Interactive region picker using fullscreen transparent overlay."""

        picker = tk.Toplevel(self.root)
        picker.attributes("-fullscreen", True)
        picker.attributes("-alpha", 0.25)
        picker.attributes("-topmost", True)
        picker.configure(bg="black")

        canvas = tk.Canvas(picker, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        state = {"x1": 0, "y1": 0, "x2": 0, "y2": 0, "rect": None}

        def on_press(event):
            state["x1"], state["y1"] = int(event.x), int(event.y)
            state["x2"], state["y2"] = int(event.x), int(event.y)
            if state["rect"]:
                canvas.delete(state["rect"])
            state["rect"] = canvas.create_rectangle(
                state["x1"],
                state["y1"],
                state["x2"],
                state["y2"],
                outline="red",
                width=2,
            )

        def on_drag(event):
            state["x2"], state["y2"] = int(event.x), int(event.y)
            if state["rect"]:
                canvas.coords(state["rect"], state["x1"], state["y1"], state["x2"], state["y2"])

        def on_release(_event):
            picker.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        picker.bind("<Escape>", lambda _e: picker.destroy())

        self.root.wait_window(picker)

        x1, y1, x2, y2 = state["x1"], state["y1"], state["x2"], state["y2"]
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)
        region = OCRRegion(x=left, y=top, width=width, height=height)
        if not region.is_valid():
            return None
        return region

    def select_ocr_region(self):
        try:
            region = self._pick_screen_region()
            if not region:
                self._append(f"[ERROR][{self.active_brand}] OCR region không hợp lệ hoặc đã huỷ")
                return
            self.comment_switch_service.set_ocr_region(self.active_brand, region)
            self._append(
                f"[SUCCESS][{self.active_brand}] Đã lưu OCR region x={region.x}, y={region.y}, w={region.width}, h={region.height}"
            )
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Chọn OCR region lỗi: {ex}")

    def start_ocr(self):
        try:
            engine_status = self.comment_switch_service.get_ocr_engine_status()
            log_path = self.comment_switch_service.ensure_ocr_log_file(self.active_brand)
            region = self.comment_switch_service.get_ocr_region(self.active_brand)
            self._append(f"[OCR-DEBUG][{self.active_brand}] engine_status={json.dumps(engine_status, ensure_ascii=False)}")
            self._append(f"[OCR-DEBUG][{self.active_brand}] log_path={log_path}")
            self._append(
                f"[OCR-DEBUG][{self.active_brand}] region=x={region.x}, y={region.y}, w={region.width}, h={region.height}"
            )

            settings = OCRSettings(
                interval_seconds=1.0,
                min_confidence=0.80,
                dedupe_same_user=bool(self.action_tabs.comment.dedupe_same_user_var.get()),
                dedupe_window_seconds=45,
            )

            def _on_comment(comment):
                try:
                    payload = self.comment_switch_service.process_ocr_comment(
                        brand_id=self.active_brand,
                        comment=comment,
                    )
                    self._result_queue.put(("ocr_comment", self.active_brand, payload))
                    return payload
                except Exception as callback_ex:
                    self._result_queue.put(("err", self.active_brand, f"OCR callback lỗi: {callback_ex}"))
                    return {"action": "error", "note": str(callback_ex)}

            started = self.comment_switch_service.start_ocr(
                brand_id=self.active_brand,
                settings=settings,
                on_comment=_on_comment,
            )
            self.action_tabs.comment.set_ocr_status(self.comment_switch_service.is_ocr_running())
            if not started:
                self._append(f"[ERROR][{self.active_brand}] OCR chưa start. Hãy chọn region trước.")
                return
            self._append(f"[SUCCESS][{self.active_brand}] OCR started")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Start OCR lỗi: {ex}")

    def stop_ocr(self):
        try:
            self.comment_switch_service.stop_ocr()
            self.action_tabs.comment.set_ocr_status(False)
            self._append(f"[SUCCESS][{self.active_brand}] OCR stopped")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Stop OCR lỗi: {ex}")

    def _get_comment_worker(self):
        brand_id = self.active_brand
        try:
            cfg = self._current_config()
            result = self.comment_switch_service.run_comment_switch(
                brand_id=brand_id,
                cfg=cfg,
                session_id=self.action_tabs.comment.session_id_var.get(),
                page_size=self.action_tabs.comment.page_size_var.get(),
                cursor=self.action_tabs.comment.cursor_var.get(),
                enabled=bool(self.action_tabs.comment.enable_switch_var.get()),
                source_type=self.action_tabs.comment.source_var.get(),
                ocr_mode="ui_text",
                ocr_file_path="",
                ui_test_text=self.action_tabs.comment.test_comment_var.get(),
                disable_ui_text=not bool(self.action_tabs.comment.use_ui_text_var.get()),
            )
            self._result_queue.put(("ok", brand_id, json.dumps(result, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("get_comment failed")
            self._result_queue.put(("err", brand_id, str(ex)))

    def test_comment_switch_async(self):
        self._run_async(self._test_comment_switch_worker)

    def _test_comment_switch_worker(self):
        brand_id = self.active_brand
        try:
            result = self.comment_switch_service.run_test_comment_switch(
                brand_id=brand_id,
                test_comment=self.action_tabs.comment.test_comment_var.get(),
            )
            self._result_queue.put(("ok", brand_id, json.dumps(result, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("test_comment_switch failed")
            self._result_queue.put(("err", brand_id, str(ex)))

    def refresh_access_token_async(self):
        self._run_async(self._refresh_access_token_worker)

    def _refresh_access_token_worker(self):
        brand_id = self.active_brand
        try:
            cfg = self._current_config()
            new_cfg, detail = self.service.refresh_access_token(cfg)
            self._result_queue.put(("token_update", brand_id, new_cfg))
            self._result_queue.put(("ok", brand_id, json.dumps(detail, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("refresh_access_token failed")
            self._result_queue.put(("err", brand_id, str(ex)))

    def get_shop_info_async(self):
        self._run_async(self._get_shop_info_worker)

    def _get_shop_info_worker(self):
        brand_id = self.active_brand
        try:
            cfg = self._current_config()
            result = self.service.get_shop_info(cfg)
            brand_dir = ensure_brand_data_dir(brand_id)
            write_json(brand_dir / "shop_info.json", result)
            self._result_queue.put(("shop_info", brand_id, result))
            self._result_queue.put(("ok", brand_id, json.dumps(result, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("get_shop_info failed")
            self._result_queue.put(("err", brand_id, str(ex)))

    def save_env(self):
        save_brand_config(self.active_brand, self._current_config())
        messagebox.showinfo("Đã lưu", UI_MESSAGES["save_success"])

    def obs_connect(self):
        try:
            svc = self._obs_service(self.active_brand)
            cfg = self.obs_panel.get_config()
            info = svc.connect(cfg)
            svc.save_config(cfg)
            self.obs_panel.set_status(svc.status_text())
            self._append(f"[SUCCESS][{self.active_brand}] OBS connect: {json.dumps(info, ensure_ascii=False)}")
        except Exception as ex:
            self.obs_panel.set_status(self._obs_service(self.active_brand).status_text())
            self._append(f"[ERROR][{self.active_brand}] OBS connect lỗi: {ex}")

    def obs_load_config_file(self):
        """Load OBS config from external json file and apply to current brand UI."""
        file_path = filedialog.askopenfilename(
            title="Chọn file OBS config",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            data = read_json(Path(file_path), default={})
            cfg = OBSConfig.from_dict(data)
            self.obs_panel.set_config(cfg)
            self._obs_service(self.active_brand).save_config(cfg)
            self._append(f"[SUCCESS][{self.active_brand}] Đã load OBS config từ file: {file_path}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Load OBS config file lỗi: {ex}")

    def obs_disconnect(self):
        svc = self._obs_service(self.active_brand)
        svc.stop_queue_runner()
        svc.disconnect()
        self.obs_panel.set_status(svc.status_text())
        self.obs_panel.set_queue_state(svc.get_queue_state())
        self._append(f"[SUCCESS][{self.active_brand}] OBS đã huỷ connect")

    def obs_reload(self):
        try:
            svc = self._obs_service(self.active_brand)
            cfg = self.obs_panel.get_config()
            info = svc.reload(cfg)
            svc.save_config(cfg)
            self.obs_panel.set_status(svc.status_text())
            self._append(f"[SUCCESS][{self.active_brand}] OBS reload: {json.dumps(info, ensure_ascii=False)}")
        except Exception as ex:
            self.obs_panel.set_status(self._obs_service(self.active_brand).status_text())
            self._append(f"[ERROR][{self.active_brand}] OBS reload lỗi: {ex}")

    def obs_load_scenes(self):
        try:
            svc = self._obs_service(self.active_brand)
            scenes = svc.list_scenes()
            self.obs_panel.set_scenes(scenes)
            self._append(f"[SUCCESS][{self.active_brand}] OBS scenes: {len(scenes)}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Load scenes lỗi: {ex}")

    def obs_load_sources(self):
        try:
            svc = self._obs_service(self.active_brand)
            scene = self.obs_panel.setting_component.scene_var.get().strip()
            if not scene:
                raise ValueError("Vui lòng chọn scene trước")
            sources = svc.list_sources(scene)
            self.obs_panel.set_sources(sources)
            cfg = self.obs_panel.get_config()
            svc.save_config(cfg)
            self._append(f"[SUCCESS][{self.active_brand}] OBS sources: {len(sources)}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Load sources lỗi: {ex}")

    def obs_apply_scene(self):
        try:
            svc = self._obs_service(self.active_brand)
            scene = self.obs_panel.setting_component.scene_var.get().strip()
            if not scene:
                raise ValueError("Vui lòng chọn scene")
            svc.set_current_scene(scene)
            cfg = self.obs_panel.get_config()
            svc.save_config(cfg)
            self._append(f"[SUCCESS][{self.active_brand}] Đã chuyển scene: {scene}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Apply scene lỗi: {ex}")

    def obs_choose_video_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa video")
        if not folder:
            return
        self.obs_panel.playlist_component.folder_var.set(folder)
        cfg = self.obs_panel.get_config()
        self._obs_service(self.active_brand).save_config(cfg)

    def obs_import_videos(self):
        try:
            svc = self._obs_service(self.active_brand)
            cfg = self.obs_panel.get_config()
            if not cfg.video_folder:
                raise ValueError("Vui lòng chọn thư mục video")
            imported = svc.import_videos_from_folder(cfg.video_folder)
            svc.save_config(cfg)
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Import {imported} video vào Queue 1")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Import video lỗi: {ex}")

    def obs_start_queue(self):
        try:
            svc = self._obs_service(self.active_brand)
            cfg = self.obs_panel.get_config()
            svc.start_queue_runner(cfg)
            svc.save_config(cfg)
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Đã start queue runner")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Start queue lỗi: {ex}")

    def obs_stop_queue(self):
        try:
            svc = self._obs_service(self.active_brand)
            svc.stop_queue_runner()
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Đã stop queue runner")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Stop queue lỗi: {ex}")

    def obs_clear_queue(self):
        try:
            svc = self._obs_service(self.active_brand)
            svc.clear_queues()
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Đã clear Queue 1 và Queue 2")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Clear queue lỗi: {ex}")

    def obs_remove_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            video_id = self.obs_panel.get_selected_video_id().strip()
            if not video_id:
                raise ValueError("Vui lòng chọn video trong Queue 1")
            svc.remove_from_play_queue(video_id)
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Đã remove video khỏi Queue 1")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Remove video lỗi: {ex}")

    def obs_move_up_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            video_id = self.obs_panel.get_selected_video_id().strip()
            if not video_id:
                raise ValueError("Vui lòng chọn video trong Queue 1")
            svc.move_play_queue_item(video_id, "up")
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self.obs_panel.set_selected_video_id(video_id)
            self._append(f"[SUCCESS][{self.active_brand}] Đã move up video")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Move up lỗi: {ex}")

    def obs_move_down_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            video_id = self.obs_panel.get_selected_video_id().strip()
            if not video_id:
                raise ValueError("Vui lòng chọn video trong Queue 1")
            svc.move_play_queue_item(video_id, "down")
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self.obs_panel.set_selected_video_id(video_id)
            self._append(f"[SUCCESS][{self.active_brand}] Đã move down video")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Move down lỗi: {ex}")

    def obs_skip_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            svc.skip_current()
            self._append(f"[SUCCESS][{self.active_brand}] Đã yêu cầu skip video hiện tại")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Skip video lỗi: {ex}")

    def obs_prioritize_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            video_id = self.obs_panel.playlist_component.priority_id_var.get().strip()
            if not video_id:
                raise ValueError("Vui lòng nhập Priority ID")
            svc.prioritize_video_by_id(video_id)
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Đã ưu tiên video ID: {video_id}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Prioritize lỗi: {ex}")

    def obs_set_video_cooldown(self):
        try:
            svc = self._obs_service(self.active_brand)
            video_id = self.obs_panel.playlist_component.cooldown_id_var.get().strip()
            if not video_id:
                raise ValueError("Vui lòng nhập Cooldown ID")
            seconds_text = self.obs_panel.playlist_component.cooldown_seconds_var.get().strip()
            seconds = int(float(seconds_text or "0"))
            if seconds < 0:
                raise ValueError("Cooldown phải >= 0")
            svc.set_video_cooldown(video_id, seconds)
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Set cooldown {seconds}s cho ID: {video_id}")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Set cooldown lỗi: {ex}")
