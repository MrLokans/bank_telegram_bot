"""
Useful decorators
"""

import functools

import telegram

from bot.exceptions import BotLoggedError
from bot.settings import logging

logger = logging.getLogger('telegrambot')


def log_exceptions(bot_func):
    @functools.wraps(bot_func)
    def wrapper(bot, update, *args, **kwargs):
        try:
            bot_func(bot, update, *args, **kwargs)
        except BotLoggedError as e:
            chat_id = update.message.chat_id
            msg = str(e)
            bot.sendMessage(chat_id=chat_id,
                            text=msg,
                            parse_mode=telegram.ParseMode.HTML)
            return
        except Exception as e:
            logger.exception("Unknown exception occured.")
            return
    return wrapper


def log_statistics(bot_func):
    @functools.wraps(bot_func)
    def wrapper(bot, update, *args, **kwargs):
        message = update.message.text
        user_id = str(update.message.from_user.id)
        chat_id = update.message.chat_id
        msg = "{} triggered, user_id: {}, chat_id {}"
        logger.info(msg.format(message, user_id, chat_id))
        bot_func(bot, update, *args, **kwargs)
    return wrapper
