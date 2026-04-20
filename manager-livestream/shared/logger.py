import logging

from shared.log_handler import get_ui_handler

_PASS_LEVEL = 25
logging.addLevelName(_PASS_LEVEL, "PASS")


def _log_pass(self, msg, *args, **kw):
    if self.isEnabledFor(_PASS_LEVEL):
        self._log(_PASS_LEVEL, msg, args, **kw)


logging.Logger.passed = _log_pass  # type: ignore[attr-defined]

_FORMATTER = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    stream = logging.StreamHandler()
    stream.setFormatter(_FORMATTER)
    logger.addHandler(stream)
    logger.addHandler(get_ui_handler())

    logger.propagate = False
    return logger
