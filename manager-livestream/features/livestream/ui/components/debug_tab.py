"""Debug tab — realtime log viewer with per-category filtering."""

from __future__ import annotations

import logging
import time
import tkinter as tk
from tkinter import scrolledtext, ttk

from shared.log_handler import get_ui_handler

_CATEGORIES = [
    ("obs.client",      "OBS Client"),
    ("obs.runner",      "OBS Runner"),
    ("comment.switch",  "Comment Switch"),
    ("comment.mapper",  "Comment Mapper"),
    ("ocr.runner",      "OCR"),
]

_LEVEL_TAG = {
    "ERROR":   "error",
    "WARNING": "warning",
    "INFO":    "info",
    "DEBUG":   "debug",
    "PASS":    "pass",
}


def _format(record: logging.LogRecord) -> str:
    ts = time.strftime("%H:%M:%S", time.localtime(record.created))
    return f"{ts} | {record.levelname:<7} | {record.name:<20} | {record.getMessage()}\n"


class DebugTab:
    """Realtime log viewer with per-category checkbox filtering."""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=6)
        self._handler = get_ui_handler()

        self._cat_vars: dict[str, tk.BooleanVar] = {}
        self._build_filter_row()
        self._build_log_area()

        self._cb = self._on_new_record
        self._handler.add_callback(self._cb)
        self._rerender()

    def _build_filter_row(self) -> None:
        row = ttk.Frame(self.frame)
        row.pack(fill="x", pady=(0, 6))

        ttk.Label(row, text="Filter:").pack(side="left", padx=(0, 8))
        for name, label in _CATEGORIES:
            var = tk.BooleanVar(value=True)
            self._cat_vars[name] = var
            ttk.Checkbutton(
                row, text=label, variable=var,
                command=self._on_filter_change,
            ).pack(side="left", padx=(0, 8))

        ttk.Button(row, text="Clear", command=self._clear).pack(side="right")

    def _build_log_area(self) -> None:
        self._text = scrolledtext.ScrolledText(
            self.frame,
            height=18,
            wrap="word",
            state="disabled",
            font=("Courier", 9),
            background="#ffffff",
            foreground="#000000",
            insertbackground="#000000",
        )
        self._text.pack(fill="both", expand=True)
        self._text.tag_configure("pass",    foreground="#006600")
        self._text.tag_configure("error",   foreground="#cc0000")
        self._text.tag_configure("warning", foreground="#cc7700")
        self._text.tag_configure("info",    foreground="#111111")
        self._text.tag_configure("debug",   foreground="#888888")

    def _enabled(self, name: str) -> bool:
        var = self._cat_vars.get(name)
        return var.get() if var else True

    def _on_new_record(self, record: logging.LogRecord) -> None:
        try:
            self.frame.after(0, self._append_record, record)
        except Exception:
            pass

    def _append_record(self, record: logging.LogRecord) -> None:
        if not self._enabled(record.name):
            return
        tag = _LEVEL_TAG.get(record.levelname, "info")
        self._text.configure(state="normal")
        self._text.insert("end", _format(record), tag)
        self._text.see("end")
        self._text.configure(state="disabled")

    def _rerender(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        for record in self._handler.all_records():
            if not self._enabled(record.name):
                continue
            tag = _LEVEL_TAG.get(record.levelname, "info")
            self._text.insert("end", _format(record), tag)
        self._text.see("end")
        self._text.configure(state="disabled")

    def _on_filter_change(self) -> None:
        self._rerender()

    def _clear(self) -> None:
        self._handler.clear()
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")

    def detach(self) -> None:
        self._handler.remove_callback(self._cb)
