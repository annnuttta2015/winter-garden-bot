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
    update_flowers, reset_all, get_top_users, subtract_stitches,
    get_all_users_with_headers
)
from export import export_users_to_csv
from flowers import (
    get_random_flower, has_caterpillar,
    BASE_FLOWERS, ADVANCED_FLOWERS, ALL_FLOWERS
)

# ---------------- ИНИЦИАЛИЗАЦИЯ ----------------
bot: telebot.TeleBot = telebot.TeleBot(TOKEN)
init_db()
logger.add("bot.log", format="{time} {level} {message}", level="INFO", rotation="5 MB")

_MESSAGES_LOG: Set[int] = set()
def clean_message_log() -> None:
    """Cleans the message log if it exceeds a certain size."""
    global _MESSAGES_LOG
    if len(_MESSAGES_LOG) > 1000:
        logger.info("Очистка журнала сообщений.")
        _MESSAGES_LOG = set()

# ---------------- КОМАНДА /START ----------------
@bot.message_handler(commands=['start'])
def start_message(message: telebot.types.Message) -> None:
    """Sends a welcome message to the user.
    Args:
        message (telebot.types.Message): The message object.
    """
    if message.message_id in _MESSAGES_LOG:
        logger.debug(f"Сообщение {message.message_id} уже обработано, пропуск.")
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    bot.reply_to(message, M["start"])
    logger.info(f"Отправлено сообщение о старте пользователю {message.from_user.id}")


# ---------------- КОМАНДА /ADD ----------------
@bot.message_handler(commands=['add'])
def add_stitches(message: telebot.types.Message) -> None:
    """Adds stitches to a user's progress and potentially gives flowers or caterpillars.
    Args:
        message (telebot.types.Message): The message object containing the /add command and amount.
    """
    chat_id: int = message.chat.id
    user_id: int = message.from_user.id
    name: str = message.from_user.first_name or "Игрок"

    if chat_id != ALLOWED_CHAT_ID:
        logger.warning(f"Пользователь {user_id} попытался использовать /add в неразрешенном чате {chat_id}.")
        bot.send_message(chat_id, "⛔️ Эта команда доступна только в основном чате.")
        return

    if message.message_id in _MESSAGES_LOG:
        logger.debug(f"Сообщение {message.message_id} уже обработано, пропуск.")
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    try:
        args: List[str] = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.send_message(chat_id, M["add_prompt"])
            logger.warning(f"Неверный формат команды /add от пользователя {user_id}: {message.text}")
            return

        stitches_to_add: int = int(args[1])
        if stitches_to_add <= 0:
            bot.send_message(chat_id, "Нельзя добавить 0 или отрицательное число крестиков 🤔")
            logger.warning(f"Пользователь {user_id} попытался добавить {stitches_to_add} крестиков.")
            return

        add_user(user_id, name)
        user_data: Tuple[str, int, str] = get_user(user_id) # Получаем данные пользователя один раз
        prev_name: str = user_data[0]
        prev_stitches: int = user_data[1]
        updated_bouquet: str = user_data[2] or ""
        flower_text: str = ""

        # 🐛 Гусеница
        if has_caterpillar():
            subtract_stitches(user_id, 100)
            prev_stitches = max(0, prev_stitches - 100) # Обновляем prev_stitches в памяти
            flower_text += M["caterpillar"]
            logger.info(f"Пользователь {user_id} получил гусеницу. Крестики уменьшены на 100.")

        # ➕ Добавляем крестики
        update_stitches(user_id, stitches_to_add)
        total_stitches: int = prev_stitches + stitches_to_add # Обновляем total_stitches в памяти
        logger.info(f"Пользователю {user_id} добавлено {stitches_to_add} крестиков. Всего: {total_stitches}")

        # 🌸 Выдача цветочков
        flowers_to_give: int = total_stitches // FLOWER_THRESHOLD - prev_stitches // FLOWER_THRESHOLD

        if flowers_to_give > 0:
            current_flower_count: int = sum(updated_bouquet.count(f) for f in ALL_FLOWERS)
            for _ in range(flowers_to_give):
                new_flower: str = get_random_flower(current_flower_count)
                update_flowers(user_id, new_flower)
                updated_bouquet += " " + new_flower
                current_flower_count += 1
            logger.info(f"Пользователь {user_id} получил {flowers_to_give} новых цветов.")

            if flowers_to_give == 1:
                flower_text += M["flower_gain_one"]
            else:
                flower_text += M["flower_gain_many"].format(count=flowers_to_give)

        # 📩 Ответ пользователю
        msg: str = (
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
            logger.info(f"Сообщение о добавлении крестиков отправлено пользователю {user_id}.")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения о добавлении крестиков игроку {user_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка в /add для пользователя {user_id}: {e}", exc_info=True)
        bot.send_message(chat_id, M["add_error"])
# ---------------- КОМАНДА /TOP ----------------
@bot.message_handler(commands=['top'])
def show_top(message: telebot.types.Message) -> None:
    """Shows the top users by stitches.
    Args:
        message (telebot.types.Message): The message object.
    """
    chat_id: int = message.chat.id
    if message.message_id in _MESSAGES_LOG:
        logger.debug(f"Сообщение {message.message_id} уже обработано, пропуск.")
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    try:
        top_users: List[Tuple[str, int, str]] = get_top_users()
        if not top_users:
            bot.send_message(chat_id, M["top_empty"])
            logger.info(f"Запрошен топ, но список пуст.")
            return

        reply: str = M["top_title"]
        for i, (name, stitches, flowers) in enumerate(top_users, start=1):
            reply += M["top_item"].format(
                index=i, name=name, stitches=stitches, flowers=flowers or "без цветов"
            ) + "\n"

        bot.send_message(chat_id, reply)
        logger.info(f"Топ пользователей отправлен в чат {chat_id}.")
    except Exception as e:
        logger.error(f"Ошибка в /top для чата {chat_id}: {e}", exc_info=True)
        bot.send_message(chat_id, "Ошибка при показе топа.")


# ---------------- КОМАНДА /BACKUP ----------------
@bot.message_handler(commands=['backup'])
def send_backup(message: telebot.types.Message) -> None:
    """Sends a CSV backup of user data to the allowed chat.
    Args:
        message (telebot.types.Message): The message object.
    """
    chat_id: int = message.chat.id
    if chat_id != ALLOWED_CHAT_ID:
        logger.warning(f"Пользователь {message.from_user.id} попытался запросить бэкап в неразрешенном чате {chat_id}.")
        bot.send_message(chat_id, M["backup_denied"])
        return

    if message.message_id in _MESSAGES_LOG:
        logger.debug(f"Сообщение {message.message_id} уже обработано, пропуск.")
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    try:
        headers: List[str]
        rows: List[Tuple[Any, ...]]
        headers, rows = get_all_users_with_headers()

        output: io.StringIO = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        output.seek(0)

        bot.send_document(chat_id, ('backup.csv', output.getvalue()))
        logger.info(f"Резервная копия отправлена в чат {chat_id}.")
    except Exception as e:
        logger.error(f"Ошибка при /backup в чате {chat_id}: {e}", exc_info=True)
        bot.send_message(chat_id, M["backup_error"].format(error=e))


# ---------------- КОМАНДА /RESET ----------------
@bot.message_handler(commands=['reset'])
def reset_command(message: telebot.types.Message) -> None:
    """Resets all user progress. Only callable by the ADMIN_ID.
    Args:
        message (telebot.types.Message): The message object.
    """
    chat_id: int = message.chat.id
    user_id: int = message.from_user.id

    if message.message_id in _MESSAGES_LOG:
        logger.debug(f"Сообщение {message.message_id} уже обработано, пропуск.")
        return
    _MESSAGES_LOG.add(message.message_id)
    clean_message_log()

    if user_id != ADMIN_ID:
        logger.warning(f"Пользователь {user_id} попытался выполнить /reset без прав администратора.")
        bot.send_message(chat_id, M["reset_denied"])
        return

    try:
        reset_all()
        bot.send_message(chat_id, M["reset_done"])
        logger.info(f"Все данные пользователей были сброшены администратором {user_id}.")
    except Exception as e:
        logger.error(f"Ошибка при /reset для администратора {user_id}: {e}", exc_info=True)
        bot.send_message(chat_id, M["reset_error"].format(error=e))


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
