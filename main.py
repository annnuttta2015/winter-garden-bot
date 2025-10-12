from messages import M
import sqlite3
import csv
import io
import os
import telebot
from loguru import logger
from typing import Any
from config import TOKEN, ALLOWED_CHAT_ID
from db import (
    init_db, add_user, update_stitches, get_user,
    update_flowers, reset_all, get_top_users, subtract_stitches
)
from export import export_users_to_csv
from flowers import (
    get_random_flower, has_caterpillar,
    BASE_FLOWERS, ADVANCED_FLOWERS
)

# ---------------- ИНИЦИАЛИЗАЦИЯ ----------------
bot = telebot.TeleBot(TOKEN)
init_db()
logger.add("bot.log", format="{time} {level} {message}", level="INFO", rotation="5 MB")

ALLOWED_CHAT_ID = -1003158914747  # основной чат

# ---------------- КОМАНДА /START ----------------
@bot.message_handler(commands=['start'])
def start_message(message: telebot.types.Message) -> None:
    """Send welcome message."""
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

        # Получаем текущие данные (до гусеницы)
        prev_data = get_user(user_id)
        updated_bouquet = prev_data[2] or ""
        flower_text = ""

        # 🐛 Гусеница (до добавления крестиков)
        if has_caterpillar():
            subtract_stitches(user_id, 100)
            flower_text += M["caterpillar"]

        # prev_stitches — уже после гусеницы
        prev_stitches = get_user(user_id)[1]

        # ➕ Добавляем крестики
        update_stitches(user_id, stitches_to_add)

        # Получаем новое общее значение
        total_stitches = get_user(user_id)[1]

        # 🌸 Выдача цветочков
        prev_level = prev_stitches // 500
        new_level = total_stitches // 500
        flowers_to_give = new_level - prev_level

        if flowers_to_give > 0:
            all_flowers = BASE_FLOWERS + ADVANCED_FLOWERS
            current_flower_count = sum(updated_bouquet.count(f) for f in all_flowers)
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

    try:
        conn = sqlite3.connect('garden.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        headers = [description[0] for description in cursor.description]
        conn.close()

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

    ADMIN_ID = 5839958791  #  ID мой

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

    try:
        from keep_alive import keep_alive
        keep_alive()  #потом удалю
    except ImportError:
        logger.warning("keep_alive не найден — запуск без Flask")

    while True:
        try:
            bot.polling(non_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(M["polling_error"].format(error=e))
            bot.stop_polling()
            import time
            time.sleep(5)
