from messages import M
from loguru import logger
import telebot
from typing import Any, Tuple, List
from config import ALLOWED_CHAT_ID, FLOWER_THRESHOLD
from db import (
    add_user, update_stitches, get_user,
    add_flower_to_user, get_user_flowers_list, subtract_stitches
)
from flowers import (
    get_random_flower, has_caterpillar, ALL_FLOWERS
)
from .utils import _MESSAGES_LOG, clean_message_log

def register_add_handler(bot: telebot.TeleBot) -> None:
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
            user_data: Tuple[str, int, int] | None = get_user(user_id) # Получаем данные пользователя один раз
            if user_data is None:
                logger.error(f"Ошибка: данные пользователя {user_id} не найдены после добавления.")
                bot.send_message(chat_id, M["add_error"])
                return

            prev_name: str = user_data[0]
            prev_stitches: int = user_data[1]
            caterpillars_count: int = user_data[2]
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
            current_flowers_list: List[str] = get_user_flowers_list(user_id)
            current_flower_count: int = len(current_flowers_list)

            flowers_to_give: int = total_stitches // FLOWER_THRESHOLD - current_flower_count

            if flowers_to_give > 0:
               
                for _ in range(flowers_to_give):
                    new_flower: str = get_random_flower(current_flower_count)
                    add_flower_to_user(user_id, new_flower)
                    current_flowers_list.append(new_flower) # Обновляем список в памяти
                    current_flower_count += 1
                logger.info(f"Пользователь {user_id} получил {flowers_to_give} новых цветов.")

                if flowers_to_give == 1:
                    flower_text += M["flower_gain_one"]
                else:
                    flower_text += M["flower_gain_many"].format(count=flowers_to_give)
            
            updated_bouquet: str = " ".join(get_user_flowers_list(user_id)).strip()

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
