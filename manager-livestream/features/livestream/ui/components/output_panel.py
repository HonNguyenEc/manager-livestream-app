"""Output text area component for request/response logs."""

from tkinter import ttk
import tkinter as tk


class OutputPanel:
    """Bottom panel to print operation results and errors."""

    def __init__(self, parent):
        frame = ttk.LabelFrame(parent, text="Output", padding=10)
        frame.pack(fill="both", expand=True)
        self.text = tk.Text(frame, wrap="word", font=("Consolas", 10))
        self.text.pack(fill="both", expand=True)

    def append(self, text: str):
        self.text.insert("end", text + "\n")
        self.text.see("end")

    def clear(self):
        self.text.delete("1.0", "end")

    def set_text(self, content: str):
        self.clear()
        if content:
            self.text.insert("end", content)
            self.text.see("end")

    def get_text(self) -> str:
        return self.text.get("1.0", "end").rstrip()
