"""
    Collection of diferent routine helpers
"""


import os
import glob
import datetime
import importlib
import itertools
import logging

from typing import Sequence, Mapping, Any, Tuple, TypeVar, Dict

import bot.settings as settings

from bot.exceptions import BotLoggedError, BotArgumentParsingError
from bot.currency import Currency


A = TypeVar('A')
T = TypeVar('T')

logger = logging.getLogger('telegrambot')


def sort_by_value(to_sort: Sequence[Tuple[A, T]],
                  sort_by: Sequence[A]) -> Sequence[T]:
    """Sorts two sequences basing on the second one"""
    to_sort_d = dict(to_sort)
    result = []
    for item in sort_by:
        result.append(to_sort_d[item])
    return result


def preferences_from_args(args: Sequence[str]) -> Mapping[str, Any]:
    """Takes a sequence of strings and tries to find settings, returning default
    values if not found:
    There are args that may be required for any request:
    -b <bank_name> - selects a bank by its short name
    -c <currency_name> - selects currency to get exchange rates for
    -d <date_diff> - parse data for the moment in the past

    In a long run we should be able to support a list of currencies supplied,
    and a recognition of parameters w/o those unfriendly CLI keys like -d or -c
    """
    preferences = {
        "days_ago": 0,
        "currency": "all",  # We want to get data about all present currencies
        "bank_name": None
    }

    for i, arg in enumerate(args):
        if arg == "-d":
            if i < len(args) - 1:
                # Handle non-int input
                try:
                    days_diff = int(args[i + 1])
                except ValueError:
                    msg = """\
Wrong day diff format, please specifiy integer number in range 2-2400
"""
                    raise BotLoggedError(msg)

                if days_diff < 2 or days_diff > 2400:
                    msg = """\
Wrong day diff format, please specify integer number in range 2-2400
"""
                    raise BotLoggedError(msg)
                preferences['days_ago'] = days_diff
        if arg == "-c":
            if i < len(args) - 1:
                # Validate currency
                currency = args[i + 1]
                preferences['currency'] = get_currency_from_arg(currency)
        if arg == "-b":
            if i < len(args) - 1:
                # Validate currency
                bank_name = args[i + 1]
                preferences['bank_name'] = bank_name
    return preferences


def get_currency_from_arg(s: str) -> str:
    """Parse argument string and extracts currency from it
    Logics moved into separate method to provide ability to parse
    multpile currency names
    """
    return s


def get_date_arg(args: Sequence[str]):
    """Return date difference from argument sequence if date flag is present"""
    date = 0
    for arg in args:
        match = settings.DATE_REGEX.match(arg)
        if match:
            date = int(match.groupdict()['date_diff'])
    return date


def get_date_from_date_diff(day_difference: int,
                            today: datetime.date) -> datetime.date:
    """Returns date that is N days from the given date."""
    return today - datetime.timedelta(days=int(day_difference))


def date_diffs_for_long_diff(day_diff: int,
                             min_n: int=12,
                             max_n: int=30) -> Sequence[int]:
    """
        Takes number of days and splits it into a list of diffs
    """

    if 1 <= day_diff <= max_n:
        return [i for i in range(day_diff + 1)]
    else:
        for i in range(min_n, max_n + 1):
            if day_diff % i == 0:
                den = day_diff // i
                return [x * den for x in range(0, i + 1)]
        portion = day_diff // (max_n - 1)
        rest = day_diff - (portion * (max_n - 1))
        result = [x * portion for x in range(0, max_n - 1)]
        result.append(rest + result[-1])
        return result


def get_default_parser_class(parsers_dir=settings.PARSERS_DIR):
    dir_components = list(filter(lambda x: x.strip(), parsers_dir.split('/')))
    dir_components.append(settings.DEFAULT_PARSER_MODULE)
    parser_path = ".".join(dir_components)
    default_module = importlib.import_module(parser_path)
    default_parser = parser_class_from_module(default_module)
    return default_parser


def get_parser_file_names():
    """
    Gets parser class names
    """
    parser_files = glob.glob("bot/parsers/*_parser.py")
    return [os.path.basename(os.path.splitext(p)[0])
            for p in parser_files]


def parser_module_name(parser_fname):
    """
    Generates module path for the given
    parser name

    >>> parser_module_name('some_parser.py')
    >>> 'bot.parsers.some_parser'
    """
    return ".".join(["bot", "parsers", parser_fname])


def get_parser_classes(active_only: bool=True):
    """
        Scans for classes that provide bank scraping and returns them as a list
    """
    parser_classes = []
    module_names = get_parser_file_names()
    for module_name in module_names:
        module_name = parser_module_name(module_name)
        module = importlib.import_module(module_name)
        parser_class = parser_class_from_module(module)
        if parser_class is not None:
            if not active_only:
                parser_classes.append(parser_class)
                continue
            has_active_field = hasattr(parser_class, "is_active")
            if has_active_field and parser_class.is_active:
                parser_classes.append(parser_class)
    # We didn't find any extra class (techncally, currently it is not possible,
    # but who cares?) so we return default one
    if len(parser_classes) == 0:
        default_parser = get_default_parser_class()
        parser_classes = [default_parser]

    return parser_classes


def get_bank_names() -> Sequence[str]:
    """Get all available bank short and full names"""
    parser_classes = get_parser_classes()
    bank_names = [c.name for c in parser_classes]
    bank_short_names = [c.short_name for c in parser_classes]
    return bank_names + bank_short_names


def parser_class_from_module(module):
    """Inspects module for having a *Parser class"""
    for k in module.__dict__:
        is_base_parser = k == "BaseParser"
        if isinstance(k, str) and k.endswith("Parser") and not is_base_parser:
            return module.__dict__[k]
    return None


def get_parser(parser_name: str):
    """Gets parser by its name or short name."""
    parser_name = parser_name.lower()
    parser_classes = get_parser_classes()
    assert len(parser_classes) > 0

    for parser_class in parser_classes:
        names_equal = parser_class.name.lower() == parser_name
        short_names_equal = parser_class.short_name == parser_name
        if names_equal or short_names_equal:
            parser = parser_class
            print("Parser found: {}".format(parser))
            return parser
    else:
        # FIXME: somehow select parser not relying on its order
        parser = parser_classes[1]
    return parser


def sort_currencies(currencies: Sequence[Currency]) -> Sequence[Currency]:
    """Return new sorted list of currencies so that some specific ones
    are always in top and other are sorted alphabetically."""
    priority = {
        "USD": 1,
        "EUR": 2,
        "RUB": 3
    }
    specific = []
    generic = []
    for item in currencies:
        if item.iso in priority:
            specific.append(item)
        else:
            generic.append(item)
    sorted_specific = sorted(specific, key=lambda x: priority[x.iso])
    sorted_generic = sorted(generic, key=lambda x: x.iso)
    return list(itertools.chain(sorted_specific, sorted_generic))


def format_currency_string(cur: Currency) -> str:
    """Formats currency to be sent to user"""
    format_s = '<b>{:<5}</b>{:<8.3f}{:<8.3f}'
    s = format_s.format(cur.iso + ":",
                        '-' if cur.buy is None else cur.buy,
                        '-' if cur.sell is None else cur.sell)
    return s


def parse_args(bot, update, args) -> Mapping[str, Any]:
    try:
        preferences = preferences_from_args(args)
    except BotArgumentParsingError as e:
        logger.exception(str(e))
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=str(e))
        return {}

    return preferences


def get_user_selected_bank(user_id: str,
                           cache: Mapping[str, str]=settings.USER_BANK_SELECTION_CACHE) -> str:
    """Finds out whether the given user has bank associated with,
    if not - returns the default one"""
    if user_id not in cache:
        bank_name = settings.DEFAULT_PARSER_NAME
    else:
        bank_name = cache[user_id]
    return bank_name


def set_user_default_bank(user_id: str,
                          bank_name: str,
                          cache: Mapping[str, str]=settings.USER_BANK_SELECTION_CACHE) -> None:
    cache[user_id] = bank_name


def is_image_cached(image_path: str, max_n: int=8) -> bool:
    """Checks whether image with the given name has already been created"""
    return os.path.exists(image_path)


def get_best_currencies(currency: str) -> Dict[str, Tuple[str, Any]]:
    """Get best sell and buy rates for available banks"""
    parser_classes = get_parser_classes()
    parsers = [parser(cache=default_cache) for parser in parser_classes
               if parser.short_name != 'nbrb']
    results = [(p.name, cache_proxy.get_currency(p, currency))
               for p in parsers]
    results = list(filter(lambda x: not x[1].is_empty(), results))
    best_sell = list(sorted(results, key=lambda x: x[1].sell))[0]
    best_buy = list(sorted(results, key=lambda x: x[1].buy))[0]

    result = {
        "buy": best_buy,
        "sell": best_sell
    }
    return result
