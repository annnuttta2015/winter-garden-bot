from messages import M
from loguru import logger
import telebot
from .utils import _MESSAGES_LOG, clean_message_log

def register_start_handler(bot: telebot.TeleBot) -> None:
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
