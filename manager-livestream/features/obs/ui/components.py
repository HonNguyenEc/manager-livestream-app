"""Reusable OBS UI components."""

from pathlib import Path

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


class OBSSettingTab:
    def __init__(self, parent, on_load_scenes, on_load_sources, on_apply_scene):
        self.frame = ttk.Frame(parent, padding=10)
        self.scene_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.source_a_var = tk.StringVar(value="VideoA")
        self.source_b_var = tk.StringVar(value="VideoB")
        self.crossfade_var = tk.StringVar(value="2")

        ttk.Label(self.frame, text="Scene", width=14).grid(row=0, column=0, sticky="w", pady=3)
        self.scene_combo = ttk.Combobox(self.frame, textvariable=self.scene_var, state="readonly", width=46)
        self.scene_combo.grid(row=0, column=1, sticky="w", pady=3)
        ttk.Button(self.frame, text="Load Scenes", command=on_load_scenes).grid(row=0, column=2, padx=6)

        ttk.Label(self.frame, text="Source", width=14).grid(row=1, column=0, sticky="w", pady=3)
        self.source_combo = ttk.Combobox(self.frame, textvariable=self.source_var, state="readonly", width=46)
        self.source_combo.grid(row=1, column=1, sticky="w", pady=3)
        ttk.Button(self.frame, text="Load Sources", command=on_load_sources).grid(row=1, column=2, padx=6)

        ttk.Label(self.frame, text="Video Source A", width=14).grid(row=2, column=0, sticky="w", pady=3)
        self.source_a_combo = ttk.Combobox(self.frame, textvariable=self.source_a_var, state="readonly", width=46)
        self.source_a_combo.grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(self.frame, text="Video Source B", width=14).grid(row=3, column=0, sticky="w", pady=3)
        self.source_b_combo = ttk.Combobox(self.frame, textvariable=self.source_b_var, state="readonly", width=46)
        self.source_b_combo.grid(row=3, column=1, sticky="w", pady=3)

        ttk.Label(self.frame, text="Crossfade (s)", width=14).grid(row=4, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.crossfade_var, width=16).grid(row=4, column=1, sticky="w", pady=3)

        ttk.Button(self.frame, text="Apply Scene", command=on_apply_scene).grid(row=5, column=1, sticky="w", pady=8)


class OBSPlaylistTab:
    def __init__(
        self,
        parent,
        on_choose_folder,
        on_import,
        on_start,
        on_stop,
        on_clear,
        on_remove,
        on_move_up,
        on_move_down,
        on_skip,
    ):
        self.frame = ttk.Frame(parent, padding=10)
        self.folder_var = tk.StringVar()
        self.runner_status_var = tk.StringVar(value="Stopped")
        self.now_a_var = tk.StringVar(value="VideoA: -")
        self.now_b_var = tk.StringVar(value="VideoB: -")

        ttk.Label(self.frame, text="Video Folder", width=14).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.frame, textvariable=self.folder_var, width=62).grid(row=0, column=1, sticky="we", pady=3)
        ttk.Button(self.frame, text="Browse", command=on_choose_folder).grid(row=0, column=2, padx=6)
        ttk.Button(self.frame, text="Import", command=on_import).grid(row=0, column=3, padx=(0, 6))

        status_row = ttk.Frame(self.frame)
        status_row.grid(row=1, column=1, columnspan=3, sticky="w", pady=(2, 8))
        ttk.Label(status_row, text="Runner:").pack(side="left")
        ttk.Label(status_row, textvariable=self.runner_status_var).pack(side="left", padx=(4, 12))
        ttk.Label(status_row, textvariable=self.now_a_var).pack(side="left", padx=(0, 12))
        ttk.Label(status_row, textvariable=self.now_b_var).pack(side="left")

        lists = ttk.Frame(self.frame)
        lists.grid(row=2, column=0, columnspan=4, sticky="nsew")

        import_col = ttk.LabelFrame(lists, text="Queue 1 (Toàn bộ playlist)")
        import_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
        play_col = ttk.LabelFrame(lists, text="Queue 2 (2-3 video sắp phát)")
        play_col.pack(side="left", fill="both", expand=True)

        self.import_listbox = tk.Listbox(import_col, height=11)
        self.import_listbox.pack(fill="both", expand=True, padx=6, pady=6)

        self.play_listbox = tk.Listbox(play_col, height=11)
        self.play_listbox.pack(fill="both", expand=True, padx=6, pady=6)

        actions = ttk.Frame(self.frame)
        actions.grid(row=3, column=0, columnspan=4, sticky="w", pady=8)
        ttk.Button(actions, text="Start", command=on_start).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Stop", command=on_stop).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Skip", command=on_skip).pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Remove", command=on_remove).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Move Up", command=on_move_up).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Move Down", command=on_move_down).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Clear", command=on_clear).pack(side="left")

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)

    @staticmethod
    def _format_item(path: str) -> str:
        p = Path(path)
        return p.name

    def set_queues(self, import_queue: list[str], play_queue: list[str]):
        self.import_listbox.delete(0, tk.END)
        for item in import_queue:
            self.import_listbox.insert(tk.END, self._format_item(item))

        self.play_listbox.delete(0, tk.END)
        for i, item in enumerate(play_queue, start=1):
            self.play_listbox.insert(tk.END, f"{i:02d}. {self._format_item(item)}")

    def selected_playlist_index(self) -> int:
        selection = self.import_listbox.curselection()
        if not selection:
            return -1
        return int(selection[0])

    def set_selected_playlist_index(self, index: int):
        self.import_listbox.selection_clear(0, tk.END)
        if index >= 0 and index < self.import_listbox.size():
            self.import_listbox.selection_set(index)
            self.import_listbox.activate(index)
