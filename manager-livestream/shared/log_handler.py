"""Shared in-memory log handler for UI debug tab."""

import logging
from collections import deque

_MAX_RECORDS = 2000


class UILogHandler(logging.Handler):
    """Captures log records into a buffer and notifies registered callbacks."""

    def __init__(self):
        super().__init__()
        self._records: deque = deque(maxlen=_MAX_RECORDS)
        self._callbacks: list = []

    def emit(self, record: logging.LogRecord) -> None:
        self._records.append(record)
        for cb in list(self._callbacks):
            try:
                cb(record)
            except Exception:
                pass

    def add_callback(self, cb) -> None:
        self._callbacks.append(cb)

    def remove_callback(self, cb) -> None:
        self._callbacks = [c for c in self._callbacks if c is not cb]

    def all_records(self) -> list[logging.LogRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()


_instance = UILogHandler()
_instance.setLevel(logging.DEBUG)


def get_ui_handler() -> UILogHandler:
    return _instance
