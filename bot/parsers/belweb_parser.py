# coding: utf-8

import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from bot.currency import Currency
from .base import BaseParser


class BelwebParser(BaseParser):
    is_active = True
    BASE_URL = 'http://www.bveb.by/'
    DATE_FORMAT = "%d.%m.%Y"
    name = 'БелВЭБ'
    short_name = 'bwb'
    MINIMAL_DATE = datetime.datetime(year=2013, month=1, day=3)
    allowed_currencies = ('USD', 'EUR', 'RUB', 'LIT',
                          'CNY', 'AUD', 'UAH', 'PLZ',
                          'JPY', 'DKK', 'CHF', 'SEK',
                          'NOK', 'GBP', 'CZK', 'CAD')

    def __init__(self, parser="html.parser", *args, **kwargs):
        self._parser = parser

    def _url_for_date(self, date: datetime.date) -> str:
        formatted_date = date.strftime(self.DATE_FORMAT)
        frag = 'individual/currency-exchange/exchange/bveb/?date_hidden={}'
        return urljoin(self.BASE_URL, frag.format(formatted_date))

    def _currency_soup_for_date(self, date: datetime.date) -> BeautifulSoup:
        url = self._url_for_date(date)
        resp = requests.get(url)
        return BeautifulSoup(resp.text, self._parser)

    def _currency_from_row(self, row: BeautifulSoup) -> Currency:
        cells = row.find_all('td')
        currency_name = cells[1].text
        if '/' in currency_name:
            return None
        try:
            multiplier = self._multiplier_from_name(currency_name)
            currency_code = cells[2].text
            buy = float(cells[3].find(text=True).replace(" ", "")) / multiplier
            sell = float(cells[4].find(text=True).replace(" ", "")) / multiplier
            return Currency(name=currency_code, iso=currency_code,
                            sell=sell, buy=buy)
        except AttributeError:
            return None

    def get_all_currencies(self, date=None):
        if date is None:
            date = datetime.date.today()
        soup = self._currency_soup_for_date(date)
        tables = soup.find_all('table', class_='rates_second')
        if not tables:
            curs = []
        else:
            currency_table = tables[1]
            rows = [row for row in currency_table.find_all('tr')][3:]
            curs = filter(lambda x: x is not None,
                          (self._currency_from_row(row) for row in rows))
        return list(curs)

    def get_currency(self, currency_name="USD", date=None):
        if date is None:
            date = datetime.date.today()
        for cur in self.get_all_currencies(date):
            if cur.iso == currency_name:
                return cur
        else:
            return None


if __name__ == '__main__':
    parser = BelwebParser()
    print(list(parser.get_all_currencies()))
