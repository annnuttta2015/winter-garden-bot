from messages import M
from loguru import logger
import telebot
from typing import List, Tuple, Any
from db import get_top_users
from .utils import _MESSAGES_LOG, clean_message_log

def register_top_handler(bot: telebot.TeleBot) -> None:
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
