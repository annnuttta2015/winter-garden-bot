from messages import M
from loguru import logger
import telebot
import io
import csv
from typing import List, Tuple, Any
from config import ALLOWED_CHAT_ID
from db import get_all_users_with_headers
from .utils import _MESSAGES_LOG, clean_message_log

def register_backup_handler(bot: telebot.TeleBot) -> None:
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
