"""Brand management UI component."""

import re
import tkinter as tk
from tkinter import ttk


class BrandPanel:
    """Panel to create and manage brand profiles."""

    def __init__(self, parent, on_create_brand, on_delete_brand):
        self.frame = ttk.LabelFrame(parent, text="Brand Management", padding=10)
        self.frame.pack(fill="x", pady=(0, 8))

        self.brand_name_var = tk.StringVar()
        ttk.Label(self.frame, text="Brand ID", width=12).grid(row=0, column=0, sticky="w")

        vcmd = (self.frame.register(self._validate_brand_id), "%P")
        self.brand_entry = ttk.Entry(
            self.frame,
            textvariable=self.brand_name_var,
            width=40,
            validate="key",
            validatecommand=vcmd,
        )
        self.brand_entry.grid(row=0, column=1, sticky="w")

        ttk.Button(self.frame, text="Create Brand", command=on_create_brand).grid(row=0, column=2, padx=8)
        ttk.Button(self.frame, text="Delete Active Brand", command=on_delete_brand).grid(row=0, column=3, padx=8)

        self.hint_label = ttk.Label(
            self.frame,
            text="Chỉ cho phép: a-z, 0-9, -, _",
            foreground="#666666",
        )
        self.hint_label.grid(row=1, column=1, sticky="w", pady=(4, 0))

    def _validate_brand_id(self, proposed: str) -> bool:
        """Realtime validate brand id. Only allow a-z, 0-9, -, _."""
        if re.fullmatch(r"[a-z0-9_-]*", proposed or "") is None:
            self.frame.bell()
            return False
        return True
