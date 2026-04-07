"""Scene/settings tab for OBS UI."""

import tkinter as tk
from tkinter import ttk


class OBSSettingTab:
    def __init__(self, parent, on_load_scenes, on_load_sources, on_apply_scene):
        self.frame = ttk.Frame(parent, padding=10)
        self.scene_var = tk.StringVar()
        self.source_a_var = tk.StringVar(value="VideoA")
        self.source_b_var = tk.StringVar(value="VideoB")
        self.crossfade_var = tk.StringVar(value="2")
        self.default_cooldown_var = tk.StringVar(value="120")

        ttk.Label(self.frame, text="Scene", width=14).grid(row=0, column=0, sticky="w", pady=5)
        self.scene_combo = ttk.Combobox(self.frame, textvariable=self.scene_var, state="readonly", width=44)
        self.scene_combo.grid(row=0, column=1, sticky="we", pady=5)

        scene_actions = ttk.Frame(self.frame)
        scene_actions.grid(row=0, column=2, sticky="w", padx=(8, 0), pady=5)
        ttk.Button(scene_actions, text="Load Scenes", command=on_load_scenes).pack(side="left", padx=(0, 6))
        ttk.Button(scene_actions, text="Load Sources", command=on_load_sources).pack(side="left")

        ttk.Separator(self.frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 8))

        ttk.Label(self.frame, text="Video Source A", width=14).grid(row=2, column=0, sticky="w", pady=5)
        self.source_a_combo = ttk.Combobox(self.frame, textvariable=self.source_a_var, state="readonly", width=46)
        self.source_a_combo.grid(row=2, column=1, sticky="we", pady=5)

        ttk.Label(self.frame, text="Video Source B", width=14).grid(row=3, column=0, sticky="w", pady=5)
        self.source_b_combo = ttk.Combobox(self.frame, textvariable=self.source_b_var, state="readonly", width=46)
        self.source_b_combo.grid(row=3, column=1, sticky="we", pady=5)

        ttk.Label(self.frame, text="Crossfade (s)", width=14).grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame, textvariable=self.crossfade_var, width=16).grid(row=4, column=1, sticky="w", pady=5)

        ttk.Label(self.frame, text="Cooldown mặc định (s)", width=14).grid(row=5, column=0, sticky="w", pady=5)
        ttk.Entry(self.frame, textvariable=self.default_cooldown_var, width=16).grid(row=5, column=1, sticky="w", pady=5)

        ttk.Button(self.frame, text="Apply Scene", command=on_apply_scene).grid(row=6, column=1, sticky="w", pady=(10, 6))

        self.frame.columnconfigure(1, weight=1)
