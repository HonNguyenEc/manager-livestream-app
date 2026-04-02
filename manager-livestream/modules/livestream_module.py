import subprocess
import sys
from pathlib import Path

from modules.base import ModuleBase
from shared.logger import get_logger


class LivestreamModule(ModuleBase):
    """System module wrapper that starts the livestream UI as isolated process."""

    def __init__(self):
        self._logger = get_logger("module.livestream")
        self._process = None

    @property
    def name(self) -> str:
        return "livestream"

    def start(self) -> None:
        if self._process and self._process.poll() is None:
            self._logger.info("livestream module already running")
            return

        app_path = Path(__file__).resolve().parent.parent / "app.py"
        self._process = subprocess.Popen([sys.executable, str(app_path)])
        self._logger.info("livestream module started pid=%s", self._process.pid)

    def stop(self) -> None:
        if not self._process:
            return
        if self._process.poll() is None:
            self._process.terminate()
            self._logger.info("livestream module terminated")

    def status(self) -> dict:
        running = self._process is not None and self._process.poll() is None
        return {
            "name": self.name,
            "running": running,
            "pid": self._process.pid if running else None,
        }
