"""Connection/config tab for OBS UI."""

import tkinter as tk
from tkinter import ttk


class OBSConfigTab:
    def __init__(self, parent, on_connect, on_disconnect, on_reload, on_load_config_file):
        self.frame = ttk.Frame(parent, padding=10)
        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="4455")
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Mất connect")

        ttk.Label(self.frame, text="Host", width=14).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.host_var, width=40).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Label(self.frame, text="Port", width=14).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.port_var, width=40).grid(row=1, column=1, sticky="w", pady=3)
        ttk.Label(self.frame, text="Password", width=14).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.password_var, width=40, show="*").grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(self.frame, text="Trạng thái", width=14).grid(row=3, column=0, sticky="w", pady=3)
        ttk.Label(self.frame, textvariable=self.status_var).grid(row=3, column=1, sticky="w", pady=3)

        btn_row = ttk.Frame(self.frame)
        btn_row.grid(row=4, column=1, sticky="w", pady=8)
        ttk.Button(btn_row, text="Connect", command=on_connect).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="Huỷ connect", command=on_disconnect).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="Reload", command=on_reload).pack(side="left")
        ttk.Button(btn_row, text="Load Config File", command=on_load_config_file).pack(side="left", padx=(6, 0))
