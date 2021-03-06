"""
This module contains actual bot commands
"""

from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import os
import uuid

import telegram
from telegram.ext.dispatcher import run_async

from bot import utils
from bot import plotting
from bot import settings
from bot.decorators import log_exceptions, log_statistics
from bot.settings import logging
from bot.adapters import default_cache, cache_proxy


# Dummy method for later localization
_ = lambda x: x


logger = logging.getLogger('telegrambot')


def result_date_saver(parser, currency_name: str,
                      date: datetime.date):
    currency = cache_proxy.get_currency(parser,
                                        currency_name=currency_name,
                                        date=date)
    return (date, currency)


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text=_("I'm a bot, please talk to me!"))


def unknown(bot, update):
    logger.info("Unknown command triggered: {}".format(update.message.text))
    chat_id = update.message.chat_id
    bot.sendMessage(chat_id=chat_id,
                    text=_("Sorry, I didn't understand that command."))


def error(bot, update, error):
    msg = _('Update "{update}" caused error "{err_msg}"').format(update=update,
                                                                 err_msg=error)
    logger.warn(msg)


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
        all_currencies = cache_proxy.get_all_currencies(parser_instance,
                                                        date=parse_date)

        all_currencies = utils.sort_currencies(all_currencies)
        displayed_values = [utils.format_currency_string(x)
                            for x in all_currencies]
        header = [_("\tBuy\tSell"), ]

        currencies_text_value = "\n".join(header + displayed_values)
        bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        bot.sendMessage(chat_id=chat_id,
                        text=_("Currencies: \n{curs}").format(
                            curs=currencies_text_value),
                        parse_mode=telegram.ParseMode.HTML)

        return

    currency = preferences['currency']
    if currency.upper() in parser.allowed_currencies:
        # TODO: unify passing currency names (lowercase or uppercase only)
        cur = cache_proxy.get_currency(parser_instance,
                                       currency_name=currency,
                                       date=parse_date)

        if cur.name == 'NoValue':
            bot.sendMessage(chat_id=chat_id,
                            text=_("Unknown currency: {}").format(args[0]))
            return
        else:
            text = utils.format_currency_string(cur)
            bot.sendMessage(chat_id=chat_id,
                            text=text,
                            parse_mode=telegram.ParseMode.HTML)
            return
    else:
        text = _("Unknown currency: {}").format(currency)
        bot.sendMessage(chat_id=chat_id,
                        text=text,
                        parse_mode=telegram.ParseMode.HTML)
        return


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
        currency = settings.DEFAULT_CURRENCY.upper()

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

    if not utils.is_image_cached(output_file):

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

    best = utils.get_best_currencies(currency)

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
                    parse_mode=telegram.ParseMode.HTML)
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
            best = utils.get_best_currencies(currency)
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

            res = telegram.InputTextMessageContent(msg,
                                                   parse_mode=telegram.ParseMode.HTML)
            result = telegram.InlineQueryResultArticle(id=uuid.uuid4(),
                                                       title=_("Best rate"),
                                                       input_message_content=res)

            bot.answerInlineQuery(update.inline_query.id, [result])
            return
        if query.upper() not in parser.allowed_currencies:
            continue
        cur_value = cache_proxy.get_currency(parser,
                                             query.upper())
        bank_name = parser.name
        text = "{}\n<b>{}</b>: {}".format(bank_name,
                                          query.upper(),
                                          cur_value.sell)
        mes_content = telegram.InputTextMessageContent(text,
                                                       parse_mode=telegram.ParseMode.HTML)

        result = telegram.InlineQueryResultArticle(id=uuid.uuid4(),
                                                   title=parser.name,
                                                   input_message_content=mes_content)
        results.append(result)

    bot.answerInlineQuery(update.inline_query.id, results)
