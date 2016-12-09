# coding: utf-8

from telegram.ext import (
    Updater,
    RegexHandler,
    CommandHandler,
    InlineQueryHandler
)

import bot.commands as commands


class TelegramBot(object):

    def __init__(self, token):
        self._token = token
        self._updater = Updater(token=token)
        self._dispatcher = self._create_dispatcher(self._updater)

    def add_handler(self, handler, *args, **kwargs):
        self._dispatcher.add_handler(handler, *args, **kwargs)

    def add_error_handler(self, error_handler, *args, **kwargs):
        self._dispatcher.add_error_handler(error_handler, *args, **kwargs)

    def start_polling(self, *args, **kwargs):
        return self._updater.start_polling(*args, **kwargs)

    def idle(self, *args, **kwargs):
        return self._updater.idle(*args, **kwargs)

    def _create_dispatcher(self, updater):
        return updater.dispatcher


def create_bot(api_token):
    bot = TelegramBot(token=api_token)

    bot.add_handler(CommandHandler('start', commands.start))
    bot.add_handler(CommandHandler('help', commands.help_user))
    bot.add_handler(CommandHandler('course', commands.course,
                                   pass_args=True))
    bot.add_handler(CommandHandler('graph', commands.show_currency_graph,
                                   pass_args=True))
    bot.add_handler(CommandHandler('banks', commands.list_banks))
    bot.add_handler(CommandHandler('set', commands.set_default_bank,
                                   pass_args=True))
    bot.add_handler(CommandHandler('best', commands.best_course,
                                   pass_args=True))
    inline_rate_handler = InlineQueryHandler(commands.inline_rate)
    bot.add_handler(inline_rate_handler)

    # log all errors
    bot.add_error_handler(commands.error)

    unknown_handler = RegexHandler(r'/.*', commands.unknown)
    bot.add_handler(unknown_handler)
    return bot
