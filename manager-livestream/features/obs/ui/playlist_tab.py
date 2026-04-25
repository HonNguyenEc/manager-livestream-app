"""Playlist tab for OBS UI."""

from pathlib import Path

import tkinter as tk
from tkinter import ttk


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
        on_prioritize,
        on_set_cooldown,
        on_choose_qa_folder=None,
        on_import_qa=None,
        on_remove_qa=None,
        on_clear_qa=None,
    ):
        self.frame = ttk.Frame(parent, padding=10)
        self.folder_var = tk.StringVar()
        self.runner_status_var = tk.StringVar(value="Stopped")
        self.now_a_var = tk.StringVar(value="VideoA: -")
        self.now_b_var = tk.StringVar(value="VideoB: -")
        self.priority_id_var = tk.StringVar()
        self.cooldown_id_var = tk.StringVar()
        self.cooldown_seconds_var = tk.StringVar(value="120")
        self._import_signature = ()
        self._play_signature = ()
        self._import_row_to_id: list[str] = []
        self.qa_folder_var = tk.StringVar()
        self._qa_signature = ()
        self._qa_row_to_id: list[str] = []

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

        priority_row = ttk.Frame(self.frame)
        priority_row.grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 6))
        ttk.Label(priority_row, text="Priority ID:").pack(side="left")
        ttk.Entry(priority_row, textvariable=self.priority_id_var, width=12).pack(side="left", padx=(6, 6))
        ttk.Button(priority_row, text="Prioritize", command=on_prioritize).pack(side="left", padx=(0, 12))

        ttk.Label(priority_row, text="Cooldown ID:").pack(side="left")
        ttk.Entry(priority_row, textvariable=self.cooldown_id_var, width=12).pack(side="left", padx=(6, 6))
        ttk.Entry(priority_row, textvariable=self.cooldown_seconds_var, width=8).pack(side="left", padx=(0, 6))
        ttk.Button(priority_row, text="Set Cooldown", command=on_set_cooldown).pack(side="left")

        # QA Videos section
        qa_sep = ttk.Separator(self.frame, orient="horizontal")
        qa_sep.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(8, 4))

        qa_folder_row = ttk.Frame(self.frame)
        qa_folder_row.grid(row=6, column=0, columnspan=4, sticky="w", pady=3)
        ttk.Label(qa_folder_row, text="QA Video Folder", width=14).pack(side="left")
        ttk.Entry(qa_folder_row, textvariable=self.qa_folder_var, width=62).pack(side="left", padx=(4, 6))
        ttk.Button(qa_folder_row, text="Browse", command=on_choose_qa_folder).pack(side="left", padx=(0, 6))
        ttk.Button(qa_folder_row, text="Import QA", command=on_import_qa).pack(side="left")

        qa_list_frame = ttk.LabelFrame(self.frame, text="QA Videos")
        qa_list_frame.grid(row=7, column=0, columnspan=4, sticky="nsew", pady=(4, 0))

        self.qa_listbox = tk.Listbox(qa_list_frame, height=6)
        self.qa_listbox.pack(fill="both", expand=True, padx=6, pady=6)

        qa_actions = ttk.Frame(self.frame)
        qa_actions.grid(row=8, column=0, columnspan=4, sticky="w", pady=(4, 0))
        ttk.Button(qa_actions, text="Remove QA", command=on_remove_qa).pack(side="left", padx=(0, 6))
        ttk.Button(qa_actions, text="Clear QA", command=on_clear_qa).pack(side="left")

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)
        self.frame.rowconfigure(7, weight=1)

    @staticmethod
    def _format_item(path: str) -> str:
        p = Path(path)
        return p.name

    def set_queues(self, import_queue: list[dict], play_queue: list[dict]):
        selected_id = self.selected_video_id()

        import_signature = tuple(
            (str(item.get("id", "")), str(item.get("path", "")), str(item.get("cooldown_override_seconds", "")))
            for item in import_queue
        )
        if import_signature != self._import_signature:
            self.import_listbox.delete(0, tk.END)
            self._import_row_to_id = []
            for item in import_queue:
                video_id = str(item.get("id", ""))
                name = self._format_item(str(item.get("path", "")))
                override = item.get("cooldown_override_seconds")
                suffix = f" [cd={override}s]" if override not in (None, "", "None") else ""
                self.import_listbox.insert(tk.END, f"{video_id} | {name}{suffix}")
                self._import_row_to_id.append(video_id)
            self._import_signature = import_signature

        play_signature = tuple((str(item.get("id", "")), str(item.get("path", ""))) for item in play_queue)
        if play_signature != self._play_signature:
            self.play_listbox.delete(0, tk.END)
            for i, item in enumerate(play_queue, start=1):
                video_id = str(item.get("id", ""))
                name = self._format_item(str(item.get("path", "")))
                self.play_listbox.insert(tk.END, f"{i:02d}. {video_id} | {name}")
            self._play_signature = play_signature

        if selected_id:
            self.set_selected_video_id(selected_id)

    def set_qa_catalog(self, qa_catalog: list[dict]):
        qa_signature = tuple(
            (str(item.get("id", "")), str(item.get("path", "")))
            for item in qa_catalog
        )
        if qa_signature == self._qa_signature:
            return
        selected_id = self.selected_qa_video_id()
        self.qa_listbox.delete(0, tk.END)
        self._qa_row_to_id = []
        for item in qa_catalog:
            video_id = str(item.get("id", ""))
            name = self._format_item(str(item.get("path", "")))
            self.qa_listbox.insert(tk.END, f"{video_id} | {name}")
            self._qa_row_to_id.append(video_id)
        self._qa_signature = qa_signature
        if selected_id:
            self.set_selected_qa_video_id(selected_id)

    def selected_video_id(self) -> str:
        selection = self.import_listbox.curselection()
        if not selection:
            return ""
        row = int(selection[0])
        if row < 0 or row >= len(self._import_row_to_id):
            return ""
        return self._import_row_to_id[row]

    def set_selected_video_id(self, video_id: str):
        self.import_listbox.selection_clear(0, tk.END)
        if not video_id:
            return
        for idx, row_id in enumerate(self._import_row_to_id):
            if row_id == video_id:
                self.import_listbox.selection_set(idx)
                self.import_listbox.activate(idx)
                break

    def selected_qa_video_id(self) -> str:
        selection = self.qa_listbox.curselection()
        if not selection:
            return ""
        row = int(selection[0])
        if row < 0 or row >= len(self._qa_row_to_id):
            return ""
        return self._qa_row_to_id[row]

    def set_selected_qa_video_id(self, video_id: str):
        self.qa_listbox.selection_clear(0, tk.END)
        if not video_id:
            return
        for idx, row_id in enumerate(self._qa_row_to_id):
            if row_id == video_id:
                self.qa_listbox.selection_set(idx)
                self.qa_listbox.activate(idx)
                break
