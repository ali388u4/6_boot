import logging

from pythonjsonlogger import jsonlogger

from src.infrastructure.settings import Settings


def setup_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(handler)
