# TODO:
#  [ ] add 'help' function that displays usage
#  [ ] add '/course bank list' option to dispay banks choices
#  [ ] add /course bank <bank name> to see data about courses in the given bank
#  [ ] add /compare <currency name> see data about currency from diffrent bank
#  [ ] add parsers autodiscovery (provide some common interface)
#  [*] add some kind of memoization
#  [ ] display exchange change rates
#      e.g. /diff <bank name> -c<currency name> -d<number of days since now> -t<type (text by default)>
#  [*] add exchange rate display for the given date
import os
import datetime
import logging

from telegram import Updater

from bank_parsers import BelgazpromParser

from utils import (
    get_date_arg, get_date_from_date_diff, str_from_date, debug_msg
)

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
            selected_parser = parser
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
        parser_instance = parser()
        all_currencies = parser_instance.currencies
        displayed_values = ['{}: {} {}'.format(x.iso, x.sell, x.buy)
                            for x in all_currencies]

        currencies_text_value = "\n".join(displayed_values)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Currencies: \n{}".format(currencies_text_value))
        return
    if len(args) >= 1:
        parser = get_parser(default_parser.short_name)

        days_diff = get_date_arg(args)

        old_date = get_date_from_date_diff(days_diff)
        old_date = str_from_date(old_date)
        parser_instance = parser(date=old_date)

        if args[0].upper() in parser.allowed_currencies:
            cur = parser_instance.get_currency(currency_name=args[0])

            if cur.name == 'NoValue':
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="Unknown currency: {}".format(args[0]))
                return
            else:
                text = "{}: {} {}".format(cur.iso, cur.sell, cur.buy)
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=text)
                return
        all_currencies = parser_instance.currencies
        displayed_values = ['{}: {} {}'.format(x.iso, x.sell, x.buy)
                            for x in all_currencies]

        currencies_text_value = "\n".join(displayed_values)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Currencies: \n{}".format(currencies_text_value))
        return


dispatcher.addTelegramCommandHandler('caps', caps)
dispatcher.addTelegramCommandHandler('start', start)
dispatcher.addTelegramCommandHandler('echo', echo)
dispatcher.addTelegramCommandHandler('course', course)
dispatcher.addUnknownTelegramCommandHandler(unknown)
updater.start_polling()
