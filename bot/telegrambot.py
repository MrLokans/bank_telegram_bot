# coding: utf-8

import os
import datetime


import logging

import telegram
from telegram import Updater
from telegram.ext.dispatcher import run_async

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from parsers.belgazprombank import BelgazpromParser

from utils import (
    get_date_arg, get_date_from_date_diff, str_from_date,
    date_diffs_for_long_diff
)
from settings import logger

# add extra styling for our graphs
sns.set_style("darkgrid")


API_ENV_NAME = 'BANK_BOT_AP_TOKEN'
CACHE_EXPIRACY_MINUTES = 60
IMAGES_FOLDER = "img"

cache = {}
parsers = []
default_parser = None


api_token = os.environ.get(API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")


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


def unknown(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Sorry, I didn't understand that command.")


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


@run_async
def course(bot, update, args, **kwargs):
    chat_id = update.message.chat_id

    # By default show data for the current day
    if not args:
        parser = get_parser(default_parser.short_name)
        parser_instance = parser()
        all_currencies = parser_instance.get_all_currencies()
        displayed_values = ['{}: {} {}'.format(x.iso, x.sell, x.buy)
                            for x in all_currencies]

        currencies_text_value = "\n".join(displayed_values)
        bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        bot.sendMessage(chat_id=chat_id,
                        text="Currencies: \n{}".format(currencies_text_value))
        return
    if len(args) >= 1:
        parser = get_parser(default_parser.short_name)

        days_diff = get_date_arg(args)

        old_date = get_date_from_date_diff(days_diff)
        parser_instance = parser()

        if args[0].upper() in parser.allowed_currencies:
            cur = parser_instance.get_currency(currency_name=args[0],
                                               date=old_date)

            if cur.name == 'NoValue':
                bot.sendMessage(chat_id=chat_id,
                                text="Unknown currency: {}".format(args[0]))
                return
            else:
                text = "{}: {} {}".format(cur.iso, cur.sell, cur.buy)
                bot.sendMessage(chat_id=chat_id,
                                text=text)
                return
        all_currencies = parser_instance.get_all_currencies()
        displayed_values = ['{}: {} {}'.format(x.iso, x.sell, x.buy)
                            for x in all_currencies]

        currencies_text_value = "\n".join(displayed_values)
        bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        bot.sendMessage(chat_id=chat_id,
                        text="Currencies: \n{}".format(currencies_text_value))
        return


def show_currency_graph(bot, update, args):
    """Sends user currency graph changes for the specified period of time.
    E.g. user wants to get exchange rates for the US currency for 10 last days,
    he needs to send something like '/graph USD -d 10' """
    chat_id = update.message.chat_id
    bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)

    # TODO: find out what data are we looking for:
    # sell or buy rates or display both

    # if len(args) == 0:
    #     bot.sendMessage(chat_id=chat_id,
    #                     text="Incorrect parameters")
    #     return

    days_diff = 10
    currency = "USD"

    parser = get_parser(default_parser.short_name)
    parser_instance = parser()

    for i, arg in enumerate(args):
        if arg == "-d":
            if i < len(args) - 1:
                # Handle non-int input
                try:
                    days_diff = int(args[i+1])
                except ValueError:
                    bot.sendMessage(chat_id=chat_id,
                                    text="Wrong day diff format, please specifiy integerr number in range 2-2400")
                    return
                if days_diff < 2 or days_diff > 2400:
                    bot.sendMessage(chat_id=chat_id,
                                    text="Wrong day diff format, please specifiy integerr number in range 2-2400")
                    return
        if arg == "-c":
            if i < len(args) - 1:
                # Validate currency
                currency = args[i+1]
                if currency not in parser.allowed_currencies:
                    bot.sendMessage(chat_id=chat_id,
                                    text="Invalid currency, valid options are: [{}]".format(", ".join(parser.allowed_currencies)))
                    return

    date_diffs = date_diffs_for_long_diff(days_diff)

    dates = [get_date_from_date_diff(d) for d in date_diffs]
    past_date, future_date = dates[0], dates[-1]
    plot_image_name = generate_plot_name(default_parser.short_name, currency,
                                         past_date, future_date)

    if not os.path.exists(IMAGES_FOLDER):
        try:
            os.mkdir(IMAGES_FOLDER)
        except OSError as e:
            logger.error("Error creating images folder: ".format(e))
    output_file = os.path.join(IMAGES_FOLDER, plot_image_name)

    if not is_image_cached(output_file):

        currencies = [parser_instance.get_currency(currency_name=currency,
                                                   date=d)
                      for d in dates]

        logging.info("Creating a plot.")
        x = [d for d in dates]
        y_buy = [c.buy for c in currencies]
        y_sell = [c.sell for c in currencies]
        render_exchange_rate_plot(x, y_buy, y_sell, output_file)
        reset_plot(plt)

    bot.sendPhoto(chat_id=chat_id,
                  photo=open(output_file, 'rb'))
    return


def reset_plot(plot):
    """Resets all data on the given plot"""
    plt.clf()
    plt.cla()


# TODO: This function should be less specific
def render_exchange_rate_plot(x_axe, y_buy, y_sell, output_file):
    """Renders plot to the given file"""
    # Extra setupto orrectly display dates on X-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(x_axe, y_buy, label='Buy')
    plt.plot(x_axe, y_sell, label='Sell')
    plt.legend()
    plt.gcf().autofmt_xdate()

    plt.savefig(output_file)
    return plt


def generate_plot_name(bank_name, currency_name, start_date, end_date):
    if isinstance(start_date, datetime.date) or\
       isinstance(start_date, datetime.datetime):
        start_date = start_date.strftime("%d-%m-%Y")

    if isinstance(end_date, datetime.date) or\
       isinstance(end_date, datetime.datetime):
        end_date = end_date.strftime("%d-%m-%Y")

    name = "{}_{}_{}_{}.png".format(bank_name,
                                    currency_name,
                                    end_date,
                                    start_date)

    return name


def help_user(bot, update, args):
    chat_id = update.message.chat_id
    help_message = """Use following commands:
/course [<currency_short_name>] - display current exchange rate for the
given currency or for all available currencies.
/graph -d <days ago> -c <currency name> - plot currency exchange
rate dynamincs for the specified period of time
"""
    bot.sendMessage(chat_id=chat_id,
                    text=help_message)

    return


def is_image_cached(image_path, max_n=8):
    """Checks whether image with the given name has already been created"""
    return os.path.exists(image_path)


def main():
    updater = Updater(token=api_token)

    dispatcher = updater.dispatcher

    global parsers
    parsers = [BelgazpromParser]

    global default_parser
    default_parser = BelgazpromParser

    # We initialise cache for different parsers
    global cache
    cache = {p.short_name: {} for p in parsers}

    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('help', help_user)
    dispatcher.addTelegramCommandHandler('course', course)
    dispatcher.addTelegramCommandHandler('graph', show_currency_graph)

    dispatcher.addUnknownTelegramCommandHandler(unknown)
    # log all errors
    dispatcher.addErrorHandler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()