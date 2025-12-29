import sys

from loguru import logger

from .settings import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.ai_log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
