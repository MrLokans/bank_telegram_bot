# coding: utf-8

import datetime
from typing import Sequence
import requests
from bs4 import BeautifulSoup

from cache.mongo import MongoCurrencyCache
from currency import Currency
from settings import LOGGER_NAME, logger
from .base import BaseParser


class MtbankParser(BaseParser):
    is_active = False
    BASE_URL = ''
    DATE_FORMAT = "%d.%m.%Y"
    name = 'МТБанк'
    short_name = 'mtb'
    MINIMAL_DATE = datetime.datetime(year=2004, month=5, day=1)
    allowed_currencies = ('USD', 'EUR', 'RUB', 'BYR',
                          'GBP', 'UAH', 'CHF', 'PLN')

    def __init__(self, parser="html.parser", *args, **kwargs):
        self.name = MtbankParser.name
        self.short_name = MtbankParser.short_name
        self._cache = MongoCurrencyCache(Currency, LOGGER_NAME)
        self._parser = parser

    def get_all_currencies(self, date=None):
        raise NotImplementedError

    def get_currency(self, currency_name="USD", date=None):
        raise NotImplementedError
