"""
    Collection of diferent routine helpers
"""


import re
import os
import glob
import datetime
import importlib

from typing import Sequence, Mapping, Any, Tuple, TypeVar

import settings

from bot_exceptions import BotArgumentParsingError

DATE_REGEX = re.compile(r"-d(?P<date_diff>[\d]+)")


A = TypeVar('A')
T = TypeVar('T')


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
                    raise BotArgumentParsingError(msg)

                if days_diff < 2 or days_diff > 2400:
                    msg = """\
Wrong day diff format, please specify integer number in range 2-2400
"""
                    raise BotArgumentParsingError(msg)
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
        match = DATE_REGEX.match(arg)
        if match:
            date = int(match.groupdict()['date_diff'])
    return date


def get_date_from_date_diff(day_difference: int) -> datetime.date:
    """Returns date n days from now"""
    now = datetime.date.today()
    return now - datetime.timedelta(days=int(day_difference))


def str_from_date(date: datetime.date) -> str:
    return date.strftime("%d.%m.%Y")


def debug_msg(msg):
    print("DEBUG: {}".format(msg))


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
    parser_path = ".".join([parsers_dir, settings.DEFAULT_PARSER_MODULE])
    default_module = importlib.import_module(parser_path)
    default_parser = parser_class_from_module(default_module)
    return default_parser


def get_parser_classes(active_only: bool=True):
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
