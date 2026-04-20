"""Notebook tabs component for livestream actions."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from features.livestream.config import AppConfig


class CreateSessionTab:
    """UI section for create_session inputs."""

    def __init__(self, parent, on_create):
        self.frame = ttk.Frame(parent, padding=10)
        self.title_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.cover_var = tk.StringVar()
        self.is_test_var = tk.BooleanVar(value=False)

        ttk.Label(self.frame, text="Title", width=16).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.title_var, width=100).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Label(self.frame, text="Description", width=16).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.desc_var, width=100).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Label(self.frame, text="Cover Image URL", width=16).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.cover_var, width=100).grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Checkbutton(self.frame, text="Is Test", variable=self.is_test_var).grid(row=3, column=1, sticky="w", pady=3)

        ttk.Label(self.frame, text="Extra JSON", width=16).grid(row=4, column=0, sticky="nw", pady=3)
        self.extra_text = tk.Text(self.frame, height=5)
        self.extra_text.grid(row=4, column=1, sticky="ew", pady=3)
        self.extra_text.insert("1.0", "{}")

        ttk.Button(self.frame, text="Create Livestream Session", command=on_create).grid(row=5, column=1, sticky="w", pady=8)
        self.frame.columnconfigure(1, weight=1)

    def set_values(self, cfg: AppConfig):
        self.title_var.set(cfg.live_title)
        self.desc_var.set(cfg.live_description)
        self.cover_var.set(cfg.live_cover_image_url)
        self.is_test_var.set(cfg.live_is_test)

    def get_live_config(self) -> dict:
        return {
            "live_title": self.title_var.get().strip(),
            "live_description": self.desc_var.get().strip(),
            "live_cover_image_url": self.cover_var.get().strip(),
            "live_is_test": bool(self.is_test_var.get()),
        }

    def get_extra_json_text(self) -> str:
        return self.extra_text.get("1.0", "end")


class EndSessionTab:
    """UI section for end_session inputs."""

    def __init__(self, parent, on_end):
        self.frame = ttk.Frame(parent, padding=10)
        self.session_id_var = tk.StringVar()

        ttk.Label(self.frame, text="Session ID", width=16).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.session_id_var, width=100).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(self.frame, text="End Livestream Session", command=on_end).grid(row=1, column=1, sticky="w", pady=8)
        self.frame.columnconfigure(1, weight=1)


class CommentTab:
    """UI section for get_comment inputs."""

    def __init__(
        self,
        parent,
        on_get_comment,
        on_test_run,
        on_open_mapping_csv,
        on_open_qa_mapping_csv,
        on_open_ocr_log,
        on_select_ocr_region,
        on_start_ocr,
        on_stop_ocr,
    ):
        self.frame = ttk.Frame(parent, padding=10)
        self.session_id_var = tk.StringVar()
        self.cursor_var = tk.StringVar()
        self.page_size_var = tk.StringVar()
        self.source_var = tk.StringVar(value="api")
        self.use_ui_text_var = tk.BooleanVar(value=True)
        self.enable_switch_var = tk.BooleanVar(value=False)
        self.test_comment_var = tk.StringVar()
        self.now_playing_var = tk.StringVar(value="-")
        self.up_next_var = tk.StringVar(value="-")
        self.switch_status_var = tk.StringVar(value="Inactive")
        self.ui_input_status_var = tk.StringVar(value="Active")
        self.ocr_status_var = tk.StringVar(value="Stopped")
        self.dedupe_same_user_var = tk.BooleanVar(value=True)

        ttk.Label(self.frame, text="Session ID", width=16).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.session_id_var, width=100).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Label(self.frame, text="Cursor (optional)", width=16).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.cursor_var, width=100).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Label(self.frame, text="Page Size", width=16).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.page_size_var, width=100).grid(row=2, column=1, sticky="ew", pady=3)

        ttk.Label(self.frame, text="Comment Source", width=16).grid(row=3, column=0, sticky="w", pady=3)
        ttk.Combobox(
            self.frame,
            textvariable=self.source_var,
            values=["api", "ocr"],
            state="readonly",
            width=20,
        ).grid(row=3, column=1, sticky="w", pady=3)

        switch_row = ttk.Frame(self.frame)
        switch_row.grid(row=4, column=1, sticky="w", pady=3)
        ttk.Label(self.frame, text="Switch", width=16).grid(row=4, column=0, sticky="w", pady=3)
        ttk.Button(switch_row, text="Activate", command=self._activate_switch).pack(side="left")
        ttk.Button(switch_row, text="Deactivate", command=self._deactivate_switch).pack(side="left", padx=(6, 8))
        ttk.Label(switch_row, textvariable=self.switch_status_var).pack(side="left")

        input_row = ttk.Frame(self.frame)
        input_row.grid(row=5, column=1, sticky="w", pady=3)
        ttk.Label(self.frame, text="UI Input", width=16).grid(row=5, column=0, sticky="w", pady=3)
        ttk.Button(input_row, text="Active", command=self._activate_ui_input).pack(side="left")
        ttk.Button(input_row, text="Inactive", command=self._deactivate_ui_input).pack(side="left", padx=(6, 8))
        ttk.Label(input_row, textvariable=self.ui_input_status_var).pack(side="left")

        ttk.Label(self.frame, text="Comment Test", width=16).grid(row=6, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.test_comment_var, width=100).grid(row=6, column=1, sticky="ew", pady=3)

        action_row = ttk.Frame(self.frame)
        action_row.grid(row=7, column=1, sticky="w", pady=8)
        ttk.Button(action_row, text="Run Switch", command=on_get_comment).pack(side="left")
        ttk.Button(action_row, text="Test Convert", command=on_test_run).pack(side="left", padx=(6, 6))
        ttk.Button(action_row, text="Open Mapping CSV", command=on_open_mapping_csv).pack(side="left")
        ttk.Button(action_row, text="Open QA Mapping CSV", command=on_open_qa_mapping_csv).pack(side="left", padx=(6, 0))
        ttk.Button(action_row, text="Open OCR Log", command=on_open_ocr_log).pack(side="left", padx=(6, 0))

        ocr_row = ttk.Frame(self.frame)
        ocr_row.grid(row=8, column=1, sticky="w", pady=(2, 8))
        ttk.Label(self.frame, text="OCR", width=16).grid(row=8, column=0, sticky="w", pady=(2, 8))
        ttk.Button(ocr_row, text="Select Region", command=on_select_ocr_region).pack(side="left")
        ttk.Button(ocr_row, text="Start OCR", command=on_start_ocr).pack(side="left", padx=(6, 0))
        ttk.Button(ocr_row, text="Stop OCR", command=on_stop_ocr).pack(side="left", padx=(6, 8))
        ttk.Checkbutton(ocr_row, text="Dedupe same user", variable=self.dedupe_same_user_var).pack(side="left")
        ttk.Label(ocr_row, textvariable=self.ocr_status_var).pack(side="left", padx=(8, 0))

        status_frame = ttk.LabelFrame(self.frame, text="Video Status", padding=8)
        status_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(status_frame, text="Now Playing:", width=16).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(status_frame, textvariable=self.now_playing_var).grid(row=0, column=1, sticky="w", pady=2)
        ttk.Label(status_frame, text="Up Next:", width=16).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(status_frame, textvariable=self.up_next_var).grid(row=1, column=1, sticky="w", pady=2)

        status_frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(1, weight=1)

    def set_values(self, cfg: AppConfig):
        self.page_size_var.set(cfg.comment_page_size)
        self._refresh_status_labels()

    def _refresh_status_labels(self):
        self.switch_status_var.set("Active" if self.enable_switch_var.get() else "Inactive")
        self.ui_input_status_var.set("Active" if self.use_ui_text_var.get() else "Inactive")

    def _activate_switch(self):
        self.enable_switch_var.set(True)
        self._refresh_status_labels()

    def _deactivate_switch(self):
        self.enable_switch_var.set(False)
        self._refresh_status_labels()

    def _activate_ui_input(self):
        self.use_ui_text_var.set(True)
        self._refresh_status_labels()

    def _deactivate_ui_input(self):
        self.use_ui_text_var.set(False)
        self._refresh_status_labels()

    def set_video_status(self, now_playing: str, up_next: str):
        self.now_playing_var.set(str(now_playing or "-"))
        self.up_next_var.set(str(up_next or "-"))

    def set_ocr_status(self, running: bool):
        self.ocr_status_var.set("Running" if running else "Stopped")


class ShopInfoTab:
    """UI section to call get_shop_info API."""

    def __init__(self, parent, on_get_shop_info):
        self.frame = ttk.Frame(parent, padding=10)
        self.frame.pack(fill="both", expand=True)
        ttk.Label(
            self.frame,
            text="Lấy thông tin shop hiện tại bằng v2.shop.get_shop_info",
            width=60,
        ).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Button(self.frame, text="Get Shop Info", command=on_get_shop_info).grid(row=1, column=0, sticky="w", pady=8)

        info_frame = ttk.LabelFrame(self.frame, text="Shop Info", padding=10)
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.shop_name_var = tk.StringVar(value="-")
        self.region_var = tk.StringVar(value="-")
        self.expire_time_var = tk.StringVar(value="-")
        self.is_main_shop_var = tk.StringVar(value="-")

        rows = [
            ("shop_name", self.shop_name_var),
            ("region", self.region_var),
            ("expire_time", self.expire_time_var),
            ("is_main_shop", self.is_main_shop_var),
        ]
        for idx, (label, var) in enumerate(rows):
            ttk.Label(info_frame, text=f"{label}:", width=16).grid(row=idx, column=0, sticky="w", pady=2)
            ttk.Label(info_frame, textvariable=var).grid(row=idx, column=1, sticky="w", pady=2)

        self.frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)

    def set_shop_info(self, payload: dict):
        body = payload.get("response_body", {}) if isinstance(payload, dict) else {}
        self.shop_name_var.set(str(body.get("shop_name", "-")))
        self.region_var.set(str(body.get("region", "-")))

        expire_time = body.get("expire_time")
        if isinstance(expire_time, int):
            try:
                self.expire_time_var.set(datetime.fromtimestamp(expire_time).strftime("%Y-%m-%d %H:%M:%S"))
            except Exception:
                self.expire_time_var.set(str(expire_time))
        else:
            self.expire_time_var.set(str(expire_time or "-"))

        is_main_shop = body.get("is_main_shop")
        self.is_main_shop_var.set(str(is_main_shop) if is_main_shop is not None else "-")


class ActionTabs:
    """Composed notebook that groups livestream action tabs."""

    def __init__(
        self,
        parent,
        on_create,
        on_end,
        on_get_comment,
        on_test_comment_switch,
        on_open_mapping_csv,
        on_open_qa_mapping_csv,
        on_open_ocr_log,
        on_select_ocr_region,
        on_start_ocr,
        on_stop_ocr,
    ):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="x", pady=(10, 10))

        self.create = CreateSessionTab(notebook, on_create)
        self.end = EndSessionTab(notebook, on_end)
        self.comment = CommentTab(
            notebook,
            on_get_comment,
            on_test_comment_switch,
            on_open_mapping_csv,
            on_open_qa_mapping_csv,
            on_open_ocr_log,
            on_select_ocr_region,
            on_start_ocr,
            on_stop_ocr,
        )

        notebook.add(self.create.frame, text="Create Session")
        notebook.add(self.end.frame, text="End Session")
        notebook.add(self.comment.frame, text="Get Comments")

    def set_values(self, cfg: AppConfig):
        self.create.set_values(cfg)
        self.comment.set_values(cfg)

    def get_live_config(self) -> dict:
        cfg = self.create.get_live_config()
        cfg["comment_page_size"] = self.comment.page_size_var.get().strip()
        return cfg
