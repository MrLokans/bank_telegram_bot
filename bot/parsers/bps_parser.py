# coding: utf-8
import re
import datetime
from typing import Sequence, Set

import requests
from bs4 import BeautifulSoup

from cache.mongo import MongoCurrencyCache
from currency import Currency
from settings import LOGGER_NAME

CURRENCY_REGEX = re.compile(r'\d?\s*(?P<value>[A-Za-z]+)')


class BPSParser(object):

    is_active = True
    allowed_currencies = tuple()
    name = 'БПС-Банк'
    short_name = 'bpsb'
    allowed_currencies = set(('USD', 'EUR', 'RUB', 'UAH', 'PLN', 'GBP', 'CHF'))
    BASE_URL = "http://www.bps-sberbank.by/43257F17004E948D/currency_rates"
    DATA_FORMAT = "%Y.%m.%d"

    def __init__(self, parser="lxml", *args, **kwargs):
        self._cache = MongoCurrencyCache(Currency, LOGGER_NAME)
        self._parser = parser

    @classmethod
    def _response_for_date(cls, date: datetime.date=None) -> str:
        if date is None:
            date = datetime.date.today()

        str_date = date.strftime(cls.DATA_FORMAT)
        payload = {"openForm": 1, "date": str_date}
        r = requests.get(cls.BASE_URL, params=payload)
        return r.text

    def _soup_from_response(self, text: str) -> BeautifulSoup:
        return BeautifulSoup(text, self._parser)

    def __rate_rows(self, soup: BeautifulSoup) -> Sequence[BeautifulSoup]:
        search_query = "div.currency-block table.icon tbody > tr"
        return soup.select(search_query)

    def _currency_from_row(self, row: BeautifulSoup) -> Currency:
        row_cells = row.find_all("td")
        name = row_cells[0].find(text=True).lower()
        text = row_cells[1].find(text=True, recursive=False)
        iso = self._subtract_cur_iso(text)
        buy = row_cells[2].find(text=True, recursive=False)
        sell = row_cells[3].find(text=True, recursive=False)
        currency = Currency(name, iso, float(sell), float(buy))
        return currency

    def _subtract_cur_iso(self, cur: str) -> str:
        """
            Value like '1 USD' should be turned simply into 'USD'
        """
        match = CURRENCY_REGEX.match(cur)
        if match:
            return match.groupdict()["value"]
        raise ValueError("Incorrect currency supplied: {}".format(cur))

    def get_all_currencies(self, date=None) -> Set[Currency]:
        """Get all available currencies for the given date
        (both sell and purchase)"""
        # FIXME: add caching
        if date is None:
            date = datetime.date.today()
        response = self._response_for_date(date)
        soup = self._soup_from_response(response)
        rows = self.__rate_rows(soup)
        return set([self._currency_from_row(row) for row in rows])

    def get_currency(self, currency_name="USD", date=None):
        """Get currency data for the given currency name"""
        if date is None:
            date = datetime.date.today()

        if currency_name.upper() not in BPSParser.allowed_currencies:
            allowed = ", ".join(BPSParser.allowed_currencies)
            msg = "Incorrect currency '{}', allowed values: {}"
            raise ValueError(msg.format(currency_name, allowed))

        currencies = self.get_all_currencies(date=date)
        for currency in currencies:
            if currency.iso.upper() == currency_name:
                return currency
        return Currency.empty_currency()


def test():
    parser = BPSParser()
    assert parser._subtract_cur_iso("1   USD") == "USD"
