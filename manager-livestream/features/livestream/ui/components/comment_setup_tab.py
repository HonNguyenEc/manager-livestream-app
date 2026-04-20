"""Comment Setup tab — inline CSV mapping viewer for rotate and QA videos."""

from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path
from tkinter import ttk


def _read_csv_rows(path: Path) -> list[dict]:
    if not path or not path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8", "cp1258", "cp1252", "latin1"):
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    return []


def _make_table(parent, columns: list[tuple[str, int]]) -> ttk.Treeview:
    """Create Treeview with vertical + horizontal scrollbars."""
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)

    col_ids = [c[0] for c in columns]
    tree = ttk.Treeview(container, columns=col_ids, show="headings", height=7)
    for col_id, width in columns:
        tree.heading(col_id, text=col_id)
        tree.column(col_id, width=width, minwidth=40, stretch=True)

    ysb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    xsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    ysb.grid(row=0, column=1, sticky="ns")
    xsb.grid(row=1, column=0, sticky="ew")

    return tree


class CommentSetupTab:
    """Tab hiển thị và mở CSV mapping cho rotate videos và QA videos."""

    def __init__(
        self,
        parent,
        on_open_mapping_csv,
        on_open_qa_mapping_csv,
        on_shown=None,
    ):
        self.frame = ttk.Frame(parent, padding=10)
        self._rotate_tree = self._build_rotate_section(on_open_mapping_csv)
        self._qa_tree = self._build_qa_section(on_open_qa_mapping_csv)
        if on_shown:
            self.frame.bind("<Map>", lambda _e: on_shown())

    def _build_rotate_section(self, on_open_mapping_csv) -> ttk.Treeview:
        box = ttk.LabelFrame(self.frame, text="Rotate Mapping", padding=8)
        box.pack(fill="both", expand=True, pady=(0, 8))

        btn_row = ttk.Frame(box)
        btn_row.pack(fill="x", pady=(0, 6))
        ttk.Button(btn_row, text="Open Mapping CSV", command=on_open_mapping_csv).pack(side="left")

        cols = [("id", 70), ("name", 200), ("description", 340)]
        return _make_table(box, cols)

    def _build_qa_section(self, on_open_qa_mapping_csv) -> ttk.Treeview:
        box = ttk.LabelFrame(self.frame, text="QA Mapping", padding=8)
        box.pack(fill="both", expand=True)

        btn_row = ttk.Frame(box)
        btn_row.pack(fill="x", pady=(0, 6))
        ttk.Button(btn_row, text="Open QA Mapping CSV", command=on_open_qa_mapping_csv).pack(side="left")

        cols = [("STT", 45), ("Câu hỏi", 290), ("Trả lời", 290)]
        return _make_table(box, cols)

    def set_rotate_rows(self, rows: list[dict]) -> None:
        _populate_tree(self._rotate_tree, rows)

    def set_qa_rows(self, rows: list[dict]) -> None:
        _populate_tree(self._qa_tree, rows)

    def refresh(self, rotate_csv_path: Path, qa_csv_path: Path) -> None:
        self.set_rotate_rows(_read_csv_rows(rotate_csv_path))
        self.set_qa_rows(_read_csv_rows(qa_csv_path))


def _populate_tree(tree: ttk.Treeview, rows: list[dict]) -> None:
    tree.delete(*tree.get_children())
    cols = tree["columns"]
    for row in rows:
        tree.insert("", tk.END, values=[str(row.get(c, "")) for c in cols])
