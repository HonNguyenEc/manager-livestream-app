from pathlib import Path

from modules.base import ModuleBase
from shared.logger import get_logger
from shared.messages import ErrorCode, err
from shared.storage import read_json, write_json


class ModuleRuntime:
    def __init__(self, state_file: Path):
        self.logger = get_logger("core.runtime")
        self.state_file = state_file
        self.modules: dict[str, ModuleBase] = {}

    def register(self, module: ModuleBase) -> None:
        self.modules[module.name] = module
        self.logger.info("registered module=%s", module.name)

    def start_module(self, name: str) -> None:
        module = self.modules.get(name)
        if not module:
            raise ValueError(err(ErrorCode.MODULE_NOT_FOUND))
        try:
            module.start()
            self._persist()
        except Exception as ex:
            self.logger.exception("start module failed: %s", name)
            raise RuntimeError(f"{err(ErrorCode.MODULE_START_FAILED)}: {name}") from ex

    def stop_module(self, name: str) -> None:
        module = self.modules.get(name)
        if not module:
            raise ValueError(err(ErrorCode.MODULE_NOT_FOUND))
        try:
            module.stop()
            self._persist()
        except Exception as ex:
            self.logger.exception("stop module failed: %s", name)
            raise RuntimeError(f"{err(ErrorCode.MODULE_STOP_FAILED)}: {name}") from ex

    def status(self) -> dict:
        return {name: module.status() for name, module in self.modules.items()}

    def _persist(self) -> None:
        current = read_json(self.state_file, default={})
        current["modules"] = self.status()
        write_json(self.state_file, current)
