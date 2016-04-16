# coding: utf-8

import datetime
from collections import namedtuple
import logging

from bs4 import BeautifulSoup
import requests
import pymongo

import settings

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(__name__)

Currency = namedtuple('Currency', "name iso sell buy")


class MongoCurrencyCache(object):
    def __init__(self):
        self.server_delay = 10
        self.is_storage_available = False
        try:
            self._client = pymongo.MongoClient(settings.MONGO_HOST,
                                               int(settings.MONGO_PORT),
                                               serverSelectionTimeoutMS=self.server_delay)
            self._client.server_info()
            self._db = self._client[settings.MONGO_DATABASE]
            self._db.authenticate(settings.MONGO_USER,
                                  settings.MONGO_PASSWORD)
            self._collection = self._db[settings.MONGO_COLLECTION]
            self.is_storage_available = True
        except pymongo.errors.ServerSelectionTimeoutError:
            self.is_storage_available = False
        except pymongo.errors.OperationFailure:
            logging.error("Incorrect credentials supplied: {} - {}".format(settings.MONGO_USER,
                                                                           settings.MONGO_PASSWORD))
            self.is_storage_available = False

    def get_cached_value(self, bank_name, cur_name, date_str):
        if not self.is_storage_available:
            logger.info("Currency requested from cache but cache is unavailable.")
            return None
        search_key = "{}_{}_{}".format(bank_name.lower(),
                                       cur_name.lower(),
                                       date_str.lower())
        item = self._collection.find({"currency_key": search_key})
        if item:
            item = Currency(cur_name.upper(),
                            cur_name.upper(),
                            item['sell_value'],
                            item['buy_value'])
            return item
        return None

    def cache_currency(self, bank_name, cur_instance,
                       date_str):
        dbg_msg = "Trying to cache currency {}-{}-{} in cache.".format(
            bank_name, cur_instance.sell, date_str
        )
        logger.debug(dbg_msg)

        if not self.is_storage_available:
            logger.info("Cache is unavailable.")
            return False
        save_key = "{}_{}_{}".format(bank_name.lower(),
                                     cur_instance.iso.lower(),
                                     date_str.lower())
        item = {
            "currency_key": save_key,
            "buy_value": cur_instance.buy,
            "sell_value": cur_instance.sell
        }
        self._collection.insert(item)


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
        self._cache = MongoCurrencyCache()

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

        str_date = date.strftime(BelgazpromParser.DATE_FORMAT)
        cached_item = self._cache.get_cached_value(self.short_name,
                                                   currency_name,
                                                   str_date)
        if cached_item:
            logger.info("Cached value found {}, returning".format(cached_item))
            return cached_item

        currencies = self.get_all_currencies(date)

        for cur in currencies:
            if currency_name.upper() == cur.iso:
                self._cache.cache_currency(self.short_name, cur, str_date)
                return cur
        else:
            return Currency('NoValue', '', '', '')
