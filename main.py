from messages import M
import sqlite3
import csv
import io
import os
import telebot
from loguru import logger
from typing import Any
from config import TOKEN, ALLOWED_CHAT_ID, ADMIN_ID, FLOWER_THRESHOLD
from db import (
    init_db, add_user, update_stitches, get_user,
    update_flowers, reset_all, get_top_users, subtract_stitches,
    get_all_users_with_headers
)
from export import export_users_to_csv
from flowers import (
    get_random_flower, has_caterpillar,
    BASE_FLOWERS, ADVANCED_FLOWERS, ALL_FLOWERS
)

# ---------------- ИНИЦИАЛИЗАЦИЯ ----------------
bot = telebot.TeleBot(TOKEN)
init_db()
logger.add("bot.log", format="{time} {level} {message}", level="INFO", rotation="5 MB")

_MESSAGES_LOG = set()
def clean_message_log() -> None:
    global _MESSAGES_LOG
    if len(_MESSAGES_LOG) > 1000:
        _MESSAGES_LOG = set()

# ---------------- КОМАНДА /START ----------------
@bot.message_handler(commands=['start'])
def start_message(message: telebot.types.Message) -> None:
    """Send welcome message."""
    if message.message_id in _MESSAGES_LOG:
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    bot.reply_to(message, M["start"])


# ---------------- КОМАНДА /ADD ----------------
@bot.message_handler(commands=['add'])
def add_stitches(message: telebot.types.Message) -> None:
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name or "Игрок"

    # 🛡️ Проверка, что команда выполнена в нужном чате
    if chat_id != ALLOWED_CHAT_ID:
        bot.send_message(chat_id, "⛔️ Эта команда доступна только в основном чате.")
        return

    if message.message_id in _MESSAGES_LOG:
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.send_message(chat_id, M["add_prompt"])
            return

        stitches_to_add = int(args[1])
        if stitches_to_add <= 0:
            bot.send_message(chat_id, "Нельзя добавить 0 или отрицательное число крестиков 🤔")
            return

        add_user(user_id, name)
        user_data = get_user(user_id) # Получаем данные пользователя один раз
        prev_name, prev_stitches, updated_bouquet = user_data
        updated_bouquet = updated_bouquet or ""
        flower_text = ""

        # 🐛 Гусеница
        if has_caterpillar():
            subtract_stitches(user_id, 100)
            prev_stitches = max(0, prev_stitches - 100) # Обновляем prev_stitches в памяти
            flower_text += M["caterpillar"]

        # ➕ Добавляем крестики
        update_stitches(user_id, stitches_to_add)
        total_stitches = prev_stitches + stitches_to_add # Обновляем total_stitches в памяти

        # 🌸 Выдача цветочков
        flowers_to_give = total_stitches // FLOWER_THRESHOLD - prev_stitches // FLOWER_THRESHOLD

        if flowers_to_give > 0:
            current_flower_count = sum(updated_bouquet.count(f) for f in ALL_FLOWERS)
            for _ in range(flowers_to_give):
                new_flower = get_random_flower(current_flower_count)
                update_flowers(user_id, new_flower)
                updated_bouquet += " " + new_flower
                current_flower_count += 1

            if flowers_to_give == 1:
                flower_text += M["flower_gain_one"]
            else:
                flower_text += M["flower_gain_many"].format(count=flowers_to_give)

        # 📩 Ответ пользователю
        msg = (
            f"{flower_text}"
            + M["add_success"].format(
                name=name,
                stitches=total_stitches,
                bouquet=updated_bouquet.strip() or M["empty_bouquet"]
            )
        )

        # 🔐 Безопасная отправка
        try:
            bot.send_message(chat_id, msg)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения игроку: {e}")

    except Exception as e:
        logger.error(f"Ошибка в /add: {e}")
        bot.send_message(chat_id, M["add_error"])
# ---------------- КОМАНДА /TOP ----------------
@bot.message_handler(commands=['top'])
def show_top(message: telebot.types.Message) -> None:
    """Show top 10 users."""
    chat_id = message.chat.id
    if message.message_id in _MESSAGES_LOG:
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    try:
        top_users = get_top_users()
        if not top_users:
            bot.send_message(chat_id, M["top_empty"])
            return

        reply = M["top_title"]
        for i, (name, stitches, flowers) in enumerate(top_users, start=1):
            reply += M["top_item"].format(
                index=i, name=name, stitches=stitches, flowers=flowers or "без цветов"
            ) + "\n"

        bot.send_message(chat_id, reply)
    except Exception as e:
        logger.error(f"Ошибка в /top: {e}")
        bot.send_message(chat_id, "Ошибка при показе топа.")


# ---------------- КОМАНДА /BACKUP ----------------
@bot.message_handler(commands=['backup'])
def send_backup(message: telebot.types.Message) -> None:
    """Send backup CSV file."""
    chat_id = message.chat.id
    if chat_id != ALLOWED_CHAT_ID:
        bot.send_message(chat_id, M["backup_denied"])
        return

    if message.message_id in _MESSAGES_LOG:
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    try:
        headers, rows = get_all_users_with_headers()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        output.seek(0)

        bot.send_document(chat_id, ('backup.csv', output.getvalue()))
    except Exception as e:
        logger.error(f"Ошибка при /backup: {e}")
        bot.send_message(chat_id, M["backup_error"].format(error=e))


# ---------------- КОМАНДА /RESET ----------------
@bot.message_handler(commands=['reset'])
def reset_command(message: telebot.types.Message) -> None:
    """Reset all user progress."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        bot.send_message(chat_id, M["reset_denied"])
        return

    try:
        reset_all()
        bot.send_message(chat_id, M["reset_done"])
    except Exception as e:
        logger.error(f"Ошибка при /reset: {e}")
        bot.send_message(chat_id, M["reset_error"].format(error=e))


# ---------------- ЗАПУСК ----------------
if __name__ == "__main__":
    print("Бот запущен 🌿")
    logger.info("Бот запущен")

    while True:
        try:
            bot.polling(non_stop=True, interval=3, timeout=60)
        except Exception as e:
            logger.error(M["polling_error"].format(error=e))
            bot.stop_polling()
            import time
            time.sleep(5)
