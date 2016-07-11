# coding: utf-8

import os
from uuid import uuid4
import datetime
import functools
from typing import Mapping, Any, Dict, Tuple
from collections import deque, namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import gettext


import telegram
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    ParseMode)

from telegram.ext import (
    Updater,
    RegexHandler,
    CommandHandler,
    InlineQueryHandler
)

from telegram.ext.dispatcher import run_async


from bot_exceptions import BotLoggedError
from currency import Currency
import plotting
import utils

import settings
from settings import (
    DEFAULT_CURRENCY,
    DEFAULT_PARSER_NAME,
    LOCALIZATION_PATH,
    USER_BANK_SELECTION_CACHE,
    logging
)
from cache import RedisCache
from cache.adapters import StrCacheAdapter


BankCurrencyPair = namedtuple('BankCurrencyPair', ['name', 'currency'])

lang = gettext.translation('telegrambot',
                           localedir=LOCALIZATION_PATH,
                           languages=['ru_RU'])
lang.install()

_ = lang.gettext


default_cache = StrCacheAdapter(RedisCache(Currency, __name__),
                                Currency)

api_token = os.environ.get(settings.API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")


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
                            parse_mode=ParseMode.HTML)
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


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=_("I'm a bot, please talk to me!"))


def unknown(bot, update):
    logger.info("Unknown command triggered: {}".format(update.message.text))
    chat_id = update.message.chat_id
    bot.sendMessage(chat_id=chat_id,
                    text=_("Sorry, I didn't understand that command."))


def error(bot, update, error):
    logger.info("Error triggered for message {}".format(update.message.text))
    msg = _('Update "{update}" caused error "{err_msg}"').format(update=update,
                                                                 err_msg=error)
    logger.warn(msg)


@run_async
@log_statistics
@log_exceptions
def course(bot, update, args, **kwargs):
    user_id = str(update.message.from_user.id)
    chat_id = update.message.chat_id

    preferences = utils.parse_args(bot, update, args)
    if not preferences:
        return

    days_diff = preferences['days_ago']
    bank_name = preferences['bank_name']
    if not bank_name:
        bank_name = utils.get_user_selected_bank(user_id)

    parser = utils.get_parser(bank_name)
    parser_instance = parser(cache=default_cache)

    parse_date = utils.get_date_from_date_diff(days_diff,
                                               datetime.date.today())
    if preferences['currency'] == 'all':
        # We need to send data about all of the currencies
        all_currencies = parser_instance.get_all_currencies(date=parse_date)

        all_currencies = utils.sort_currencies(all_currencies)
        displayed_values = [utils.format_currency_string(x)
                            for x in all_currencies]
        header = [_("\tBuy\tSell"), ]

        currencies_text_value = "\n".join(header + displayed_values)
        bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        bot.sendMessage(chat_id=chat_id,
                        text=_("Currencies: \n{curs}").format(
                            curs=currencies_text_value),
                        parse_mode=ParseMode.HTML)

        return

    currency = preferences['currency']
    if currency.upper() in parser.allowed_currencies:
        # TODO: unify passing currency names (lowercase or uppercase only)
        cur = parser_instance.get_currency(currency_name=currency,
                                           date=parse_date)

        if cur.name == 'NoValue':
            bot.sendMessage(chat_id=chat_id,
                            text=_("Unknown currency: {}").format(args[0]))
            return
        else:
            text = utils.format_currency_string(cur)
            bot.sendMessage(chat_id=chat_id,
                            text=text,
                            parse_mode=ParseMode.HTML)
            return
    else:
        text = _("Unknown currency: {}").format(currency)
        bot.sendMessage(chat_id=chat_id,
                        text=text,
                        parse_mode=ParseMode.HTML)
        return


def result_date_saver(parser, currency, date):
    return (date, parser.get_currency(currency, date))


@run_async
@log_statistics
@log_exceptions
def show_currency_graph(bot, update, args, **kwargs):
    """Sends user currency graph changes for the specified period of time.
    E.g. user wants to get exchange rates for the US currency for 10 last days,
    he needs to send something like '/graph USD -d 10' """

    user_id = str(update.message.from_user.id)
    chat_id = update.message.chat_id

    bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)

    preferences = utils.parse_args(bot, update, args)
    if not preferences:
        return

    days_diff = preferences['days_ago']
    if days_diff == 0:
        # Well, it's dirty
        days_diff = 30
    currency = preferences['currency']
    bank_name = preferences['bank_name']
    if not bank_name:
        bank_name = utils.get_user_selected_bank(user_id)

    parser = utils.get_parser(bank_name)
    parser_instance = parser(cache=default_cache)

    if currency == 'all':
        currency = DEFAULT_CURRENCY.upper()

    date_diffs = utils.date_diffs_for_long_diff(days_diff)

    today = datetime.date.today()
    dates = [utils.get_date_from_date_diff(d, today) for d in date_diffs]
    past_date, future_date = dates[0], dates[-1]

    plot_image_name = plotting.generate_plot_name(parser.short_name, currency,
                                                  past_date, future_date)

    if not os.path.exists(settings.IMAGES_FOLDER):
        try:
            os.mkdir(settings.IMAGES_FOLDER)
        except OSError as e:
            logger.error("Error creating images folder: ".format(e))
    output_file = os.path.join(settings.IMAGES_FOLDER, plot_image_name)

    if not is_image_cached(output_file):

        # We use thread pool to asyncronously get pages
        currencies_deque = deque()
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_date = {executor.submit(result_date_saver,
                                              parser_instance,
                                              currency, date): date
                              for date in dates}
            for future in as_completed(future_to_date):
                data = future.result()
                currencies_deque.append(data)

        currencies = utils.sort_by_value(currencies_deque, dates)
        logging.info("Creating a plot.")
        x = [d for d in dates]
        y_buy = [c.buy / c.multiplier for c in currencies]
        y_sell = [c.sell / c.multiplier for c in currencies]
        plotting.render_exchange_rate_plot(x, y_buy, y_sell, output_file)
        plotting.reset_plot()

    bot.sendPhoto(chat_id=chat_id,
                  photo=open(output_file, 'rb'))
    return


@log_statistics
@log_exceptions
def help_user(bot, update):
    chat_id = update.message.chat_id

    help_message = _("""Use following commands:
/course -d <days ago> -c <currency name>  - display current exchange rate for the
given currency or for all available currencies.
/graph -d <days ago> -c <currency name> - plot currency exchange
rate dynamincs for the specified period of time
/banks - list names of currently supported banks.
/set <bank_name> - sets default bank name for all of the operations
/best -c <cur_name> -d <date diff> - best exchange rate for the given currency
""")
    bot.sendMessage(chat_id=chat_id,
                    text=help_message)

    return


@log_exceptions
def list_banks(bot, update):
    """Show user names of banks that are supported"""
    chat_id = update.message.chat_id

    parser_classes = utils.get_parser_classes()

    bank_names = "\n".join(
        parser_cls.name + "\t:\t" + parser_cls.short_name
        for parser_cls in parser_classes
    )

    msg = _("Supported banks: \n{}").format(bank_names)
    bot.sendMessage(chat_id=chat_id,
                    text=msg)
    return


@log_statistics
@log_exceptions
def set_default_bank(bot, update, args):
    chat_id = update.message.chat_id
    user_id = str(update.message.from_user.id)

    if len(args) != 1:
        # Send user data about the bank he is currently associated with
        if len(args) == 0:
            default_bank = utils.get_user_selected_bank(user_id)
            msg = _("Your currently selected bank is {}").format(default_bank)
            bot.sendMessage(chat_id=chat_id,
                            text=msg)
            return
        else:
            msg = _("Incorrect number of arguments, please specify bank name")
            bot.sendMessage(chat_id=chat_id,
                            text=msg)
            return
    bank_name = args[0].upper()

    available_names = utils.get_bank_names()
    bank_names_lower = set(map(lambda x: x.lower(), available_names))
    if bank_name.lower() not in bank_names_lower:
        bank_names = ", ".join(available_names)
        msg = _("Incorrect bank name specified, available names are: {}")
        bot.sendMessage(chat_id=chat_id,
                        text=msg.format(bank_names))
        return
    utils.set_user_default_bank(user_id, bank_name)
    msg = _("Default bank succesfully set to {}")
    bot.sendMessage(chat_id=chat_id,
                    text=msg.format(bank_name))


def get_best_currencies(currency: str) -> Dict[str, Tuple[str, Any]]:
    """Get best sell and buy rates for available banks"""
    parser_classes = utils.get_parser_classes()
    parsers = [parser(cache=default_cache) for parser in parser_classes
               if parser.short_name != 'nbrb']
    results = [(p.name, p.get_currency(currency)) for p in parsers]
    results = list(filter(lambda x: not x[1].is_empty(), results))
    best_sell = list(sorted(results, key=lambda x: x[1].sell))[0]
    best_buy = list(sorted(results, key=lambda x: x[1].buy))[0]

    result = {
        "buy": best_buy,
        "sell": best_sell
    }
    return result


@run_async
@log_statistics
@log_exceptions
def best_course(bot, update, args, **kwargs):
    """Gets the best course rate for available banks."""
    chat_id = update.message.chat_id

    bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)

    preferences = utils.parse_args(bot, update, args)
    if not preferences:
        return
    currency = preferences['currency']
    if currency == 'all':
        currency = 'USD'

    best = get_best_currencies(currency)

    buy_msg = _("Buy {}: <b>{}</b> - {}")
    buy_msg = buy_msg.format(best["buy"][1].iso,
                             best["buy"][0],
                             best["buy"][1].buy)
    # TODO: add allignment
    sell_msg = _("Sell {}: <b>{}</b> - {}")
    sell_msg = sell_msg.format(best["sell"][1].iso,
                               best["sell"][0],
                               best["sell"][1].sell)
    msg = "\n".join([buy_msg, sell_msg])
    bot.sendMessage(chat_id=chat_id,
                    text=msg,
                    parse_mode=ParseMode.HTML)
    return


def inline_rate(bot, update):
    query = update.inline_query.query
    query_list = query.split(" ")

    results = list()

    parser_classes = utils.get_parser_classes()
    parsers = [parser(cache=default_cache)
               for parser in parser_classes]

    for parser in parsers:
        # Best exchange rate in inline mode
        # TODO: write wrapper function to handle inputs like this one
        if len(query_list) == 2 and "best" in query_list:
            # TODO: this feature is experimental and
            # not-optimized at all, it is SLOW
            # Mutating original list is not a great ideas
            temp_list = query_list[:]
            temp_list.remove("best")
            currency = temp_list[0]
            if currency.upper() not in parser.allowed_currencies:
                continue
            best = get_best_currencies(currency)
            buy_msg = _("Buy {}: <b>{}</b> - {}")
            buy_msg = buy_msg.format(best["buy"][1].iso,
                                     best["buy"][0],
                                     best["buy"][1].buy)
            # TODO: add allignment
            sell_msg = _("Sell {}: <b>{}</b> - {}")
            sell_msg = sell_msg.format(best["sell"][1].iso,
                                       best["sell"][0],
                                       best["sell"][1].sell)
            msg = "\n".join([buy_msg, sell_msg])

            res = InputTextMessageContent(msg,
                                          parse_mode=ParseMode.HTML)
            result = InlineQueryResultArticle(id=uuid4(),
                                              title=_("Best rate"),
                                              input_message_content=res)

            bot.answerInlineQuery(update.inline_query.id, [result])
            return
        if query.upper() not in parser.allowed_currencies:
            continue
        cur_value = parser.get_currency(query.upper())
        bank_name = parser.name
        text = "{}\n<b>{}</b>: {}".format(bank_name,
                                          query.upper(),
                                          cur_value.sell)
        mes_content = InputTextMessageContent(text,
                                              parse_mode=ParseMode.HTML)

        result = InlineQueryResultArticle(id=uuid4(),
                                          title=parser.name,
                                          input_message_content=mes_content)
        results.append(result)

    bot.answerInlineQuery(update.inline_query.id, results)


def is_image_cached(image_path: str, max_n: int=8) -> bool:
    """Checks whether image with the given name has already been created"""
    return os.path.exists(image_path)


def main():
    updater = Updater(token=api_token)

    dispatcher = updater.dispatcher

    dispatcher.addHandler(CommandHandler('start', start))
    dispatcher.addHandler(CommandHandler('help', help_user))
    dispatcher.addHandler(CommandHandler('course', course,
                                         pass_args=True))
    dispatcher.addHandler(CommandHandler('graph', show_currency_graph,
                                         pass_args=True))
    dispatcher.addHandler(CommandHandler('banks', list_banks))
    dispatcher.addHandler(CommandHandler('set', set_default_bank,
                                         pass_args=True))
    dispatcher.addHandler(CommandHandler('best', best_course,
                                         pass_args=True))
    inline_rate_handler = InlineQueryHandler(inline_rate)
    dispatcher.addHandler(inline_rate_handler)

    # log all errors
    dispatcher.addErrorHandler(error)

    unknown_handler = RegexHandler(r'/.*', unknown)
    dispatcher.addHandler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
