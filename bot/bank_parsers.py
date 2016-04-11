# coding: utf-8

import datetime
from collections import namedtuple

from bs4 import BeautifulSoup
import requests


Currency = namedtuple('Currency', "name iso sell buy")


class BelgazpromParser(object):

    BASE_URL = 'http://belgazprombank.by/about/kursi_valjut/'
    DATE_FORMAT = "%d.%m.%Y"
    name = 'Белгазпромбанк'
    short_name = 'bgp'
    MINIMAL_DATE = datetime.datetime(year=2004, month=5, day=1)
    allowed_currencies = ('USD', 'EUR', 'RUB', 'BYR',
                          'GBP', 'UAH', 'CHF', 'PLN')

    def __init__(self, *args, **kwargs):
        self.name = BelgazpromParser.name
        self.short_name = BelgazpromParser.short_name

    # TODO: caching!
    def __get_exchange_rate_for_the_date(self, d):
        """Gets page with currency rates for the given date"""

        supplied_date = d
        if supplied_date is None:
            supplied_date = datetime.date.today()
        assert isinstance(supplied_date, datetime.date), "Incorrect date type"

        str_date = datetime.date.strftime(supplied_date,
                                          BelgazpromParser.DATE_FORMAT)
        date_params = {"date": str_date}
        return requests.get(BelgazpromParser.BASE_URL, params=date_params)

    def __soup_from_request(self, resp):
        """Create soup object from the supplied requests response"""
        text = resp.text
        return BeautifulSoup(text, "html.parser")

    def __get_currency_table(self, soup):
        return soup.find(id="courses_tab1_form").parent

    def __get_currency_objects(self, cur_table, days_since_now=None):
        if not days_since_now:
            exchange_table = cur_table.find('table').find('tbody')
            exchange_rows = exchange_table.find_all('tr')
            return [BelgazpromParser.__currency_object_from_row(row)
                    for row in exchange_rows]
        # TODO: add data display for the date in the past

    @classmethod
    def __currency_object_from_row(cls, row_object):
        table_cols = row_object.find_all('td')
        return Currency(name=table_cols[0].text.strip(),
                        iso=table_cols[1].text,
                        sell=table_cols[2].find(text=True),
                        buy=table_cols[3].find(text=True))

    def get_all_data(self):
        return [tuple(cur) for cur in self.currencies]

    def get_all_currencies(self, date=None):
        # TODO: check if string is supplied as date
        if date is None:
            date = datetime.date.today()
        assert isinstance(date, datetime.date), "Incorrect date supplied"

        r = self.__get_exchange_rate_for_the_date(date)
        s = self.__soup_from_request(r)
        currency_table = self.__get_currency_table(s)
        currencies = self.__get_currency_objects(currency_table)
        return currencies

    # def get_all_currencies(self, diff_days=None):
    #     if diff_days is not None:
    #         try:
    #             diff_days = int(diff_days)
    #         except ValueError:
    #             diff_days = 0
    #     else:
    #         diff_days = 0

    #     current_date = datetime.date.today()
    #     former_date = current_date - datetime.timedelta(days=diff_days)

    #     r = self.__get_exchange_rate_for_the_date(former_date)
    #     s = self.__soup_from_request(r)
    #     currency_table = self.__get_currency_table(s)
    #     currencies = self.__get_currency_objects(currency_table)
    #     return currencies

    def get_currency_for_diff_date(self, diff_days, currency="USD"):
        former_date = datetime.date.today - datetime.timedelta(days=diff_days)
        return self.get_currency(currency, date=former_date)

    def get_currency(self, currency_name="USD", date=None):
        # TODO: requires heavy optimization or caching
        if date is None:
            date = datetime.date.today()
        assert isinstance(date, datetime.date), "Incorrect date supplied"
        currencies = self.get_all_currencies(date)

        for cur in currencies:
            if currency_name.upper() == cur.iso:
                return cur
        else:
            return Currency('NoValue', '', '', '')
