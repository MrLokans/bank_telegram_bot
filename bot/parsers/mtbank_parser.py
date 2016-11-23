# coding: utf-8

import datetime
from typing import Sequence
import requests
from bs4 import BeautifulSoup

from bot.currency import Currency
from bot.settings import LOGGER_NAME, logger
from .base import BaseParser


class MtbankParser(BaseParser):
    is_active = False
    BASE_URL = 'https://www.mtbank.by/'
    DATE_FORMAT = "%d.%m.%Y"
    name = 'МТБанк'
    short_name = 'mtb'
    MINIMAL_DATE = datetime.datetime(year=2004, month=5, day=1)
    allowed_currencies = ('USD', 'EUR', 'RUB')

    def __init__(self, parser="html.parser", *args, **kwargs):
        self.name = MtbankParser.name
        self.short_name = MtbankParser.short_name
        self._parser = parser

    def _get_page_soup(self) -> BeautifulSoup:
        text = requests.get(self.BASE_URL)
        return BeautifulSoup(text, "html.parser")

    def get_all_currencies(self, date=None):
        raise NotImplementedError

    def get_currency(self, currency_name="USD", date=None):
        raise NotImplementedError


if __name__ == '__main__':
    parser = MtbankParser()
    print(parser.get_all_currencies())
