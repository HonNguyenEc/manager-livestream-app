"""Main livestream UI assembled from reusable components."""

import json
import queue
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
        self.obs_panel.set_queue_state(svc.get_queue_state())

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
            self.obs_panel.set_queue_state(svc.get_queue_state())
        except Exception:
            pass
        finally:
            self.root.after(350, self._poll_obs_queue_state)

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

    def _get_comment_worker(self):
        brand_id = self.active_brand
        try:
            cfg = self._current_config()
            result = self.service.get_comment(
                cfg,
                self.action_tabs.comment.session_id_var.get(),
                self.action_tabs.comment.page_size_var.get(),
                self.action_tabs.comment.cursor_var.get(),
            )
            self._result_queue.put(("ok", brand_id, json.dumps(result, ensure_ascii=False, indent=2)))
        except Exception as ex:
            logger.exception("get_comment failed")
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
            index = self.obs_panel.get_selected_playlist_index()
            if index < 0:
                raise ValueError("Vui lòng chọn video trong Queue 1")
            svc.remove_from_play_queue(index)
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self._append(f"[SUCCESS][{self.active_brand}] Đã remove video khỏi Queue 1")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Remove video lỗi: {ex}")

    def obs_move_up_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            index = self.obs_panel.get_selected_playlist_index()
            if index < 0:
                raise ValueError("Vui lòng chọn video trong Queue 1")
            new_index = svc.move_play_queue_item(index, "up")
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self.obs_panel.set_selected_playlist_index(new_index)
            self._append(f"[SUCCESS][{self.active_brand}] Đã move up video")
        except Exception as ex:
            self._append(f"[ERROR][{self.active_brand}] Move up lỗi: {ex}")

    def obs_move_down_video(self):
        try:
            svc = self._obs_service(self.active_brand)
            index = self.obs_panel.get_selected_playlist_index()
            if index < 0:
                raise ValueError("Vui lòng chọn video trong Queue 1")
            new_index = svc.move_play_queue_item(index, "down")
            self.obs_panel.set_queue_state(svc.get_queue_state())
            self.obs_panel.set_selected_playlist_index(new_index)
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
