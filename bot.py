# TODO:
#  [ ] add 'help' function that displays usage
#  [ ] add '/course bank list' option to dispay banks choices
#  [ ] add /course bank <bank name> to see data about courses in the given bank
#  [ ] add /compare <currency name> see data about currency from diffrent bank
#  [ ] add parsers autodiscovery (provide some common interface)
#  [*] add some kind of memoization 

import os
import time
import datetime
import logging

from telegram import Updater

from bank_parsers import BelgazpromParser

API_ENV_NAME = 'BANK_BOT_AP_TOKEN'
CACHE_EXPIRACY_MINUTES = 60


api_token = os.environ.get(API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")

updater = Updater(token=api_token)

dispatcher = updater.dispatcher

parsers = [BelgazpromParser]
default_parser = BelgazpromParser
cache = {p.short_name: {} for p in parsers}


def get_parser(parser_name):

    if cache.get(parser_name, ''):
        parser_dict = cache.get(parser_name)
        cached_at = parser_dict['cached_at']
        now = datetime.datetime.now()
        is_valid = (now - cached_at).seconds / 60 < CACHE_EXPIRACY_MINUTES
        cached_parser = parser_dict.get('parser', None)
        if is_valid and cached_parser:
            logging.info("Using cached parser.")
            return cached_parser

    for parser in parsers:
        if parser.short_name == parser_name:
            selected_parser = parser()
            logging.info("Parser found. Caching.")
            cache[parser_name] = {'cached_at': datetime.datetime.now(),
                                  'parser': selected_parser}
            return selected_parser
    raise ValueError("Incorrect parser name: {}".format(parser_name))


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=update.message.text)


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Sorry, I didn't understand that command.")


def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.sendMessage(chat_id=update.message.chat_id, text=text_caps)


def course(bot, update, args):
    if not args:
        parser = get_parser(default_parser.short_name)
        all_currencies = parser.currencies
        displayed_values = ['{}: {} {}'.format(x.iso, x.sell, x.buy)
                            for x in all_currencies]

        currencies_text_value = "\n".join(displayed_values)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Currencies: \n{}".format(currencies_text_value))
        return
    if len(args) == 1:
        parser = get_parser(default_parser.short_name)
        cur = parser.get_currency(currency_name=args[0])
        if cur.name == 'NoValue':
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Unknown currency: {}".format(args[0]))
        else:
            text = "{}: {} {}".format(cur.iso, cur.sell, cur.buy)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=text)


dispatcher.addTelegramCommandHandler('caps', caps)
dispatcher.addTelegramCommandHandler('start', start)
dispatcher.addTelegramCommandHandler('echo', echo)
dispatcher.addTelegramCommandHandler('course', course)
dispatcher.addUnknownTelegramCommandHandler(unknown)
updater.start_polling()
