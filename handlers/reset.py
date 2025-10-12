from messages import M
from loguru import logger
import telebot
from typing import Any
from config import ADMIN_ID
from db import reset_all
from .utils import _MESSAGES_LOG, clean_message_log

def register_reset_handler(bot: telebot.TeleBot) -> None:
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
