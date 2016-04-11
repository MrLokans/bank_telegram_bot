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
