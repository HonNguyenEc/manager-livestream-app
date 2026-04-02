from pathlib import Path

from core.runtime import ModuleRuntime
from modules.livestream_module import LivestreamModule
from shared.logger import get_logger


def main():
    logger = get_logger("system.main")
    state_file = Path(__file__).resolve().parent / "data" / "system_state.json"

    runtime = ModuleRuntime(state_file=state_file)
    runtime.register(LivestreamModule())

    # default auto-start livestream module
    runtime.start_module("livestream")
    logger.info("system started. module status=%s", runtime.status())


if __name__ == "__main__":
    main()
