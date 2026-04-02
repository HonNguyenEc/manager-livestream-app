"""Notebook tabs component for livestream actions."""

import tkinter as tk
from tkinter import ttk

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

    def __init__(self, parent, on_get_comment):
        self.frame = ttk.Frame(parent, padding=10)
        self.session_id_var = tk.StringVar()
        self.cursor_var = tk.StringVar()
        self.page_size_var = tk.StringVar()

        ttk.Label(self.frame, text="Session ID", width=16).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.session_id_var, width=100).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Label(self.frame, text="Cursor (optional)", width=16).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.cursor_var, width=100).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Label(self.frame, text="Page Size", width=16).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.page_size_var, width=100).grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Button(self.frame, text="Get Livestream Comments", command=on_get_comment).grid(row=3, column=1, sticky="w", pady=8)
        self.frame.columnconfigure(1, weight=1)

    def set_values(self, cfg: AppConfig):
        self.page_size_var.set(cfg.comment_page_size)


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


class ActionTabs:
    """Composed notebook that groups livestream action tabs."""

    def __init__(self, parent, on_create, on_end, on_get_comment):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="x", pady=(10, 10))

        self.create = CreateSessionTab(notebook, on_create)
        self.end = EndSessionTab(notebook, on_end)
        self.comment = CommentTab(notebook, on_get_comment)

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
