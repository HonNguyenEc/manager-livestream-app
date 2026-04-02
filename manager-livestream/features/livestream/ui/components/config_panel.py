"""Configuration panel component for livestream UI."""

import tkinter as tk
from tkinter import ttk

from features.livestream.config import AppConfig


class ConfigPanel:
    """Top panel containing all credential/config fields."""

    def __init__(self, parent, on_save, on_refresh_token):
        self.host_var = tk.StringVar()
        self.partner_id_var = tk.StringVar()
        self.partner_key_var = tk.StringVar()
        self.shop_id_var = tk.StringVar()
        self.user_id_var = tk.StringVar()
        self.access_token_var = tk.StringVar()
        self.refresh_token_var = tk.StringVar()

        frame = ttk.LabelFrame(parent, text="Config (.env)", padding=10)
        frame.pack(fill="x")

        fields = [
            ("Host", self.host_var, False),
            ("Partner ID", self.partner_id_var, False),
            ("Partner Key", self.partner_key_var, True),
            ("Shop ID", self.shop_id_var, False),
            ("User ID", self.user_id_var, False),
            ("Access Token", self.access_token_var, True),
            ("Refresh Token", self.refresh_token_var, True),
        ]

        for i, (label, var, secret) in enumerate(fields):
            ttk.Label(frame, text=label, width=14).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Entry(frame, textvariable=var, show="*" if secret else "", width=110).grid(
                row=i,
                column=1,
                sticky="ew",
                pady=3,
            )

        frame.columnconfigure(1, weight=1)
        ttk.Button(frame, text="Save .env", command=on_save).grid(row=0, column=2, rowspan=2, padx=8)
        ttk.Button(frame, text="Refresh Access Token", command=on_refresh_token).grid(row=2, column=2, rowspan=2, padx=8)

    def set_values(self, cfg: AppConfig):
        self.host_var.set(cfg.host)
        self.partner_id_var.set(cfg.partner_id)
        self.partner_key_var.set(cfg.partner_key)
        self.shop_id_var.set(cfg.shop_id)
        self.user_id_var.set(cfg.user_id)
        self.access_token_var.set(cfg.access_token)
        self.refresh_token_var.set(cfg.refresh_token)

    def update_tokens(self, cfg: AppConfig):
        self.access_token_var.set(cfg.access_token)
        self.refresh_token_var.set(cfg.refresh_token)

    def to_config(self, live_cfg: dict) -> AppConfig:
        return AppConfig(
            host=self.host_var.get().strip(),
            partner_id=self.partner_id_var.get().strip(),
            partner_key=self.partner_key_var.get().strip(),
            shop_id=self.shop_id_var.get().strip(),
            user_id=self.user_id_var.get().strip(),
            access_token=self.access_token_var.get().strip(),
            refresh_token=self.refresh_token_var.get().strip(),
            live_title=live_cfg["live_title"],
            live_description=live_cfg["live_description"],
            live_cover_image_url=live_cfg["live_cover_image_url"],
            live_is_test=live_cfg["live_is_test"],
            comment_page_size=live_cfg["comment_page_size"],
        )
