import os
from dotenv import load_dotenv
from typing import Any, Callable

"""Configuration settings for the Winter Garden Telegram Bot.

This module loads environment variables for sensitive data and configurable parameters.
"""

load_dotenv()

def _get_env_variable(key: str, default: Any = None, type_cast: Callable = str) -> Any:
    value = os.getenv(key)
    if value is None and default is None:
        raise ValueError(f"Переменная окружения '{key}' не установлена.")
    if value is None:
        return default
    try:
        return type_cast(value)
    except ValueError:
        raise ValueError(f"Не удалось преобразовать переменную окружения '{key}' ('{value}') к типу {type_cast.__name__}.")

TOKEN: str = _get_env_variable("TOKEN")
ALLOWED_CHAT_ID: int = _get_env_variable("ALLOWED_CHAT_ID", type_cast=int)
ADMIN_ID: int = _get_env_variable("ADMIN_ID", type_cast=int)
FLOWER_THRESHOLD: int = _get_env_variable("FLOWER_THRESHOLD", default=500, type_cast=int)
