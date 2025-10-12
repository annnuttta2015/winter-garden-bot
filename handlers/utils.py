from loguru import logger
from typing import Set

_MESSAGES_LOG: Set[int] = set()
def clean_message_log() -> None:
    """Cleans the message log if it exceeds a certain size."""
    global _MESSAGES_LOG
    if len(_MESSAGES_LOG) > 1000:
        logger.info("Очистка журнала сообщений.")
        _MESSAGES_LOG = set()
