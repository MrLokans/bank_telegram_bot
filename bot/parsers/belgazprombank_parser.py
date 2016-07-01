# coding: utf-8

import datetime
from typing import Sequence
import requests
from bs4 import BeautifulSoup

from currency import Currency
from settings import logger
from .base import BaseParser


class BelgazpromParser(BaseParser):
    is_active = True
    BASE_URL = 'http://belgazprombank.by/about/kursi_valjut/'
    DATE_FORMAT = "%d.%m.%Y"
    name = 'Белгазпромбанк'
    short_name = 'bgp'
    MINIMAL_DATE = datetime.datetime(year=2004, month=5, day=1)
    allowed_currencies = ('USD', 'EUR', 'RUB', 'BYR',
                          'GBP', 'UAH', 'CHF', 'PLN', 'BYN')

    def __init__(self, parser="lxml", cache=None, *args, **kwargs):
        self.name = BelgazpromParser.name
        self.short_name = BelgazpromParser.short_name
        self._cache = cache
        self._parser = parser

    def __get_response_for_the_date(self,
                                    d: datetime.date) -> requests.models.Response:
        """Gets page with currency rates for the given date"""

        supplied_date = d
        if supplied_date is None:
            supplied_date = datetime.date.today()
        assert isinstance(supplied_date, datetime.date), "Incorrect date type"

        str_date = datetime.date.strftime(supplied_date,
                                          BelgazpromParser.DATE_FORMAT)
        date_params = {"date": str_date}
        r = requests.get(BelgazpromParser.BASE_URL, params=date_params)
        return r

    def __soup_from_response(self,
                             resp: requests.models.Response) -> BeautifulSoup:
        """Create soup object from the supplied requests response"""
        text = resp.text
        return BeautifulSoup(text, self._parser)

    def __get_currency_table(self,
                             soup: BeautifulSoup) -> BeautifulSoup:
        """Returns table with exchanges rates from the given
        BeautifulSoup object"""
        return soup.find(id="courses_tab1_form").parent

    def __get_currency_objects(self,
                               cur_table: BeautifulSoup,
                               days_since_now=None) -> Sequence[Currency]:
        """
            Parses BeautifulSoup table with exchanges rates and extracts
            currency data
        """
        if not days_since_now:
            currencies = []
            exchange_table = cur_table.find('table').find('tbody')
            exchange_rows = exchange_table.find_all('tr')
            for row in exchange_rows:
                try:
                    c = BelgazpromParser.__currency_object_from_row(row)
                    currencies.append(c)
                except ValueError:
                    currencies.append(Currency.empty_currency())
            return currencies

    @classmethod
    def __currency_object_from_row(cls,
                                   row_object: BeautifulSoup) -> Currency:
        table_cols = row_object.find_all('td')
        return Currency(name=table_cols[0].text.strip(),
                        iso=table_cols[1].text,
                        sell=float(table_cols[3].find(text=True)),
                        buy=float(table_cols[2].find(text=True)))

    def get_all_currencies(self,
                           date: datetime.date=None,
                           use_cache=True) -> Sequence[Currency]:
        today = datetime.date.today()
        if date is None:
            date = today
        assert isinstance(date, datetime.date), "Incorrect date supplied"

        r = self.__get_response_for_the_date(date)
        s = self.__soup_from_response(r)
        currency_table = self.__get_currency_table(s)
        currencies = self.__get_currency_objects(currency_table)

        if today < self.DENOMINATION_DATE:
            for c in currencies:
                c.multiplier = 10000
        else:
            for c in currencies:
                c.multiplier = 1

        for currency in currencies:
            self.try_caching(currency, date, today, use_cache=use_cache)
        return currencies

    def get_currency_for_diff_date(self,
                                   diff_days: int,
                                   currency: str="USD") -> Currency:
        delta = datetime.timedelta(days=diff_days)
        former_date = datetime.date.today() - delta
        currency = self.get_currency(currency, date=former_date)
        return currency

    def get_currency(self,
                     currency_name: str="USD",
                     date: datetime.date=None,
                     use_cache: bool=True) -> Currency:
        today = datetime.date.today()
        if date is None:
            date = today
        assert isinstance(date, datetime.date), "Incorrect date supplied"

        is_today = date == today

        cached_item = None
        if not is_today:
            cached_item = self._cache.get_cached_value(self.short_name,
                                                       currency_name,
                                                       date)
        if cached_item:
            if not hasattr(cached_item, 'multiplier'):
                if today < self.DENOMINATION_DATE:
                    cached_item.multiplier = 10000
                else:
                    cached_item.multiplier = 1
            logger.info("Cached value found {}, returning".format(cached_item))
            return cached_item

        currencies = self.get_all_currencies(date)

        for cur in currencies:

            if currency_name.upper() == cur.iso:
                if today < self.DENOMINATION_DATE:
                    cur.multiplier = 10000
                else:
                    cur.multiplier = 1
                self.try_caching(cur, date, today, use_cache=use_cache)
                return cur
        else:
            return Currency.empty_currency()
