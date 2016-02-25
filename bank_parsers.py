from collections import namedtuple

from bs4 import BeautifulSoup
import requests


Currency = namedtuple('Currency', "name iso sell buy")


class BelgazpromParser(object):

    URL = 'http://belgazprombank.by/about/kursi_valjut/'

    def __init__(self):
        self._soup = BeautifulSoup(requests.get(BelgazpromParser.URL).text)
        self._currency_table = self.__get_currency_table()
        self.currencies = self.__get_currency_objects()

    def __get_currency_table(self):
        return self._soup.find(id="courses_tab1_form").parent

    def __get_currency_objects(self):
        exchange_table = self._currency_table.find('table').find('tbody')
        exchange_rows = exchange_table.find_all('tr')
        return [BelgazpromParser.__currency_object_from_row(row) for row in exchange_rows]

    @classmethod
    def __currency_object_from_row(cls, row_object):
        table_cols = row_object.find_all('td')
        return Currency(name=table_cols[0].text.strip(),
                        iso=table_cols[1].text,
                        sell=table_cols[2].find(text=True),
                        buy=table_cols[3].find(text=True))

    def get_all_data(self):
        return [tuple(cur) for cur in self.currencies]

    def get_currency(self, currency_name="USD"):
        for cur in self.currencies:
            if currency_name.upper() == cur.iso:
                return cur
        return Currency('NoValue', '', '', '')
