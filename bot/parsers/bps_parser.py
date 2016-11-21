# coding: utf-8
import re
import datetime
from typing import Sequence, Set

import requests
from bs4 import BeautifulSoup

from bot.currency import Currency
from bot.exceptions import BotLoggedError
from bot.parsers.base import BaseParser

CURRENCY_REGEX = re.compile(r'(?P<multiplier>\d+)\s*(?P<value>[A-Za-z]+)')


class BPSParser(BaseParser):

    is_active = True
    allowed_currencies = tuple()
    name = 'БПС-Банк'
    short_name = 'bpsb'
    allowed_currencies = set(('USD', 'EUR', 'RUB', 'UAH',
                              'PLN', 'GBP', 'CHF', 'BYN'))
    BASE_URL = "http://www.bps-sberbank.by/43257F17004E948D/currency_rates"
    DATE_FORMAT = "%Y.%m.%d"

    def __init__(self, cache=None, parser="lxml", *args, **kwargs):
        self._cache = cache
        self._parser = parser

    @classmethod
    def _response_for_date(cls, date: datetime.date=None) -> str:
        if date is None:
            date = datetime.date.today()

        str_date = date.strftime(cls.DATE_FORMAT)
        payload = {"openForm": 1, "date": str_date}
        r = requests.get(cls.BASE_URL, params=payload)
        return r.text

    def _soup_from_response(self, text: str) -> BeautifulSoup:
        return BeautifulSoup(text, self._parser)

    def __rate_rows(self, soup: BeautifulSoup) -> Sequence[BeautifulSoup]:
        search_query = "div.currency-block #tab-32 table.icon tbody > tr"
        return soup.select(search_query)

    def _currency_from_row(self, row: BeautifulSoup) -> Currency:
        row_cells = row.find_all("td")
        name = row_cells[0].find(text=True).lower()
        text = row_cells[1].find(text=True, recursive=False)
        multiplier, iso = self._subtract_cur_iso_and_multiplier(text)
        buy = row_cells[2].find(text=True, recursive=False).replace(" ", "")
        sell = row_cells[3].find(text=True, recursive=False).replace(" ", "")
        currency = Currency(name, iso,
                            float(sell) / multiplier,
                            float(buy) / multiplier)
        return currency

    def _subtract_cur_iso_and_multiplier(self, cur: str) -> str:
        """
            Value like '1 USD' should be turned simply into 'USD'
        """
        match = CURRENCY_REGEX.match(cur)
        if match:
            return (int(match.groupdict()["multiplier"]),
                    match.groupdict()["value"])
        raise BotLoggedError("Incorrect currency supplied: {}".format(cur))

    def get_all_currencies(self, date=None, use_cache=True) -> Set[Currency]:
        """Get all available currencies for the given date
        (both sell and purchase)"""
        # FIXME: add caching
        today = datetime.date.today()
        if date is None:
            date = today
        response = self._response_for_date(date)
        soup = self._soup_from_response(response)
        rows = self.__rate_rows(soup)

        currencies = set([self._currency_from_row(row) for row in rows])
        if date < self.DENOMINATION_DATE:
            for c in currencies:
                c.multiplier = 10000
        else:
            for c in currencies:
                c.multiplier = 1
        for currency in currencies:
            self.try_caching(currency, date, today, use_cache=use_cache)

        return currencies

    def get_currency(self, currency_name="USD", date=None, use_cache=True):
        """Get currency data for the given currency name"""
        today = datetime.date.today()
        if date is None:
            date = today

        if currency_name.upper() not in BPSParser.allowed_currencies:
            allowed = ", ".join(BPSParser.allowed_currencies)
            msg = "Incorrect currency '{}', allowed values: {}"
            raise BotLoggedError(msg.format(currency_name, allowed))

        is_today = date == today

        cached_item = None
        if not is_today:
            cached_item = self._cache.get_cached_value(self.short_name,
                                                       currency_name,
                                                       date)
        if cached_item:
            if not hasattr(cached_item, 'multiplier'):
                if date < self.DENOMINATION_DATE:
                    cached_item.multiplier = 10000
                else:
                    cached_item.multiplier = 1
            return cached_item

        currencies = self.get_all_currencies(date=date)
        for currency in currencies:
            if currency.iso.upper() == currency_name:
                if date < self.DENOMINATION_DATE:
                    currency.multiplier = 10000
                else:
                    currency.multiplier = 1
                self.try_caching(currency, date, today, use_cache=use_cache)
                return currency
        return Currency.empty_currency()


def test():
    parser = BPSParser()
    assert parser._subtract_cur_iso("1   USD") == "USD"
