"""
    Collection of diferent routine helpers
"""


import re
import datetime

DATE_REGEX = re.compile(r"-d(?P<date_diff>[\d]+)")


def get_date_arg(args):
    """Return date difference from argument sequence if date flag is present"""
    date = 0
    for arg in args:
        match = DATE_REGEX.match(arg)
        if match:
            date = int(match.groupdict()['date_diff'])
    return date


def get_date_from_date_diff(day_difference):
    """Returns date n days from now"""
    now = datetime.datetime.now()
    return now - datetime.timedelta(days=int(day_difference))


def str_from_date(date):
    return date.strftime("%d.%m.%Y")


def debug_msg(msg):
    print("DEBUG: {}".format(msg))


def date_diffs_for_long_diff(day_diff, min_n=8, max_n=20):
    """
        Takes number of days and splits it into a list of diffs
    """

    if 1 <= day_diff <= max_n:
        return [i for i in range(day_diff+1)]
    else:
        for i in range(min_n, max_n+1):
            if day_diff % i == 0:
                den = day_diff // i
                return [x * den for x in range(0, i + 1)]
        portion = day_diff // (max_n - 1)
        rest = day_diff - (portion * (max_n - 1))
        result = [x * portion for x in range(0, max_n - 1)]
        result.append(rest + result[-1])
        return result
