import os
from dotenv import load_dotenv

"""Configuration settings for the Winter Garden Telegram Bot.

This module loads environment variables for sensitive data and configurable parameters.
"""

load_dotenv()

TOKEN: str | None = os.getenv("TOKEN")
ALLOWED_CHAT_ID: int | None = int(os.getenv("ALLOWED_CHAT_ID")) if os.getenv("ALLOWED_CHAT_ID") else None
ADMIN_ID: int | None = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
FLOWER_THRESHOLD: int = int(os.getenv("FLOWER_THRESHOLD", 500))
