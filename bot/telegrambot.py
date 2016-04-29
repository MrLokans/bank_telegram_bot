# coding: utf-8

import os
import glob
import datetime
import importlib

import logging

import telegram
from telegram import Updater
from telegram.ext.dispatcher import run_async

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

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
DEFAULT_PARSER_NAME = "bgp"
PARSERS_DIR = "parsers"
DEFAULT_PARSER_MODULE = "belgazprombank_parser"

api_token = os.environ.get(API_ENV_NAME, '')

if not api_token:
    raise ValueError("No API token specified.")


def get_parser_classes():
    """
        Scans for classes that provide bank scraping and returns them as a list
    """
    parser_classes = []
    parser_files = glob.glob("parsers/*_parser.py")
    module_names = [os.path.basename(os.path.splitext(p)[0])
                    for p in parser_files]
    for module_name in module_names:
        module = importlib.import_module(".".join(["parsers", module_name]))
        parser_class = parser_class_from_module(module)
        if parser_class is not None:
            parser_classes.append(parser_class)

    # We didn't find any extra class (techncally, currently it is not possible,
    # but who cares?) so we return default one
    if len(parser_classes) == 0:
        parser_path = ".".join(["parsers", DEFAULT_PARSER_MODULE])
        default_module = importlib.import_module(parser_path)
        default_class = parser_class_from_module(default_module)
        parser_classes = [default_class]

    return parser_classes


def parser_class_from_module(module):
    """Inspects module for having a *Parser class"""
    for k in module.__dict__:
        if isinstance(k, str) and k.endswith("Parser"):
            return module.__dict__[k]
    return None


def get_parser(parser_name):
    """Gets parser by its name or short name."""
    parser = None
    parser_classes = get_parser_classes()
    assert len(parser_classes) > 0
    for parser_class in parser_classes:
        names_equal = parser_class.name.lower() == parser_name.lower()
        short_names_equal = parser_class.short_name == parser_name.lower
        if names_equal or short_names_equal:
            parser = parser_class
            break
    else:
        parser = parser_classes[0]
    return parser


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
        parser = get_parser("bgp")
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
        parser = get_parser("bgp")

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

    parser = get_parser("bgp")
    parser_instance = parser()

    for i, arg in enumerate(args):
        if arg == "-d":
            if i < len(args) - 1:
                # Handle non-int input
                try:
                    days_diff = int(args[i + 1])
                except ValueError:
                    msg = """\
Wrong day diff format, please specifiy integerr number in range 2-2400
"""
                    bot.sendMessage(chat_id=chat_id,
                                    text=msg)
                    return
                if days_diff < 2 or days_diff > 2400:
                    msg = """\
Wrong day diff format, please specifiy integerr number in range 2-2400
"""
                    bot.sendMessage(chat_id=chat_id,
                                    text=msg)
                    return
        if arg == "-c":
            if i < len(args) - 1:
                # Validate currency
                currency = args[i + 1]
                if currency not in parser.allowed_currencies:
                    msg = """\
Invalid currency, valid options are: [{}]
""".format(", ".join(parser.allowed_currencies))
                    bot.sendMessage(chat_id=chat_id,
                                    text=msg)
                    return

    date_diffs = date_diffs_for_long_diff(days_diff)

    dates = [get_date_from_date_diff(d) for d in date_diffs]
    past_date, future_date = dates[0], dates[-1]

    plot_image_name = generate_plot_name(parser.short_name, currency,
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
/banks - list names of currently supported banks.
"""
    bot.sendMessage(chat_id=chat_id,
                    text=help_message)

    return


def list_banks(bot, update, args):
    """Show user names of banks that are supported"""
    chat_id = update.message.chat_id
    parser_classes = get_parser_classes()

    bank_names = "\n".join(
        parser_cls.name for parser_cls in parser_classes
    )

    msg = "Current banks are now supported: \n {}".format(bank_names)
    bot.sendMessage(chat_id=chat_id,
                    text=msg)
    return


def is_image_cached(image_path, max_n=8):
    """Checks whether image with the given name has already been created"""
    return os.path.exists(image_path)


def main():
    updater = Updater(token=api_token)

    dispatcher = updater.dispatcher

    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('help', help_user)
    dispatcher.addTelegramCommandHandler('course', course)
    dispatcher.addTelegramCommandHandler('graph', show_currency_graph)
    dispatcher.addTelegramCommandHandler('banks', list_banks)

    dispatcher.addUnknownTelegramCommandHandler(unknown)
    # log all errors
    dispatcher.addErrorHandler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
