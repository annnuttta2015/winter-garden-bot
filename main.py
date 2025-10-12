from messages import M
import sqlite3
import csv
import io
import os
import telebot
from loguru import logger
from typing import Any, Set, Tuple, List
from config import TOKEN, ALLOWED_CHAT_ID, ADMIN_ID, FLOWER_THRESHOLD
from db import (
    init_db, add_user, update_stitches, get_user,
    reset_all, get_top_users, subtract_stitches,
    get_all_users_with_headers
)
from export import export_users_to_csv
from flowers import (
    get_random_flower, has_caterpillar,
    BASE_FLOWERS, ADVANCED_FLOWERS, ALL_FLOWERS
)

from handlers.start import register_start_handler
from handlers.add import register_add_handler
from handlers.top import register_top_handler
from handlers.backup import register_backup_handler
from handlers.reset import register_reset_handler

# ---------------- ИНИЦИАЛИЗАЦИЯ ----------------
bot: telebot.TeleBot = telebot.TeleBot(TOKEN)
init_db()
logger.add("bot.log", format="{time} {level} {message}", level="INFO", rotation="5 MB")

def handle_error(update: telebot.types.Update, error: Exception) -> None:
    """Global error handler for the bot. Sends error details to the admin.

    Args:
        update (telebot.types.Update): The update object that caused the error.
        error (Exception): The exception that was raised.
    """
    logger.error(f"Произошла необработанная ошибка: {error}", exc_info=True)
    error_message = f"Произошла ошибка: {error}"

    if ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID, f"Критическая ошибка бота: {error_message}\nОбновление: {update}")
            logger.info(f"Сообщение об ошибке отправлено администратору {ADMIN_ID}.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке администратору {ADMIN_ID}: {e}", exc_info=True)

# Зарегистрировать обработчики команд
register_start_handler(bot)
register_add_handler(bot)
register_top_handler(bot)
register_backup_handler(bot)
register_reset_handler(bot)

# Зарегистрировать глобальный обработчик ошибок
bot.callback_query_handler(func=lambda call: True)(handle_error) # Это для перехвата ошибок из колбэков, но не из сообщений

# ---------------- ЗАПУСК ----------------
if __name__ == "__main__":
    print("Бот запущен 🌿")
    logger.info("Бот запущен")

    while True:
        try:
            logger.info("Начинаем опрос Telegram API...")
            bot.polling(non_stop=True, interval=3, timeout=60)
        except Exception as e:
            logger.error(M["polling_error"].format(error=e), exc_info=True)
            bot.stop_polling()
            import time
            time.sleep(5)
            logger.info("Перезапуск опроса через 5 секунд.")
