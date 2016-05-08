# coding: utf-8
import datetime
from typing import Dict, Set, Union

import requests

from cache.mongo import MongoCurrencyCache
from currency import Currency
from settings import LOGGER_NAME


class PriorbankParser(object):

    is_active = True
    allowed_currencies = ('USD', 'RUB', 'EUR')
    name = 'Priorbank Parser'
    short_name = 'prbp'

    DATE_FORMAT = "%d-%m-%Y"
    BASE_URL = "https://www.priorbank.by/currency_exchange"

    # p_p_col_pos=3&p_p_col_count=6&fromDate=08-05-2016&toDate=08-05-2016&channelIDs=3&currencies=all"

    def __init__(self, parser="lxml", *args, **kwargs):
        self._cache = MongoCurrencyCache(Currency, LOGGER_NAME)
        self._parser = parser

    @classmethod
    def _response_for_date(cls, date: datetime.date) -> Dict:
        str_date = date.strftime(cls.DATE_FORMAT)
        payload = {
            "p_p_id": "exchangeliferayspringmvcportlet_WAR_exchangeliferayspringmvcportlet_INSTANCE_GACJA0EoQLJN",
            "p_p_lifecycle": 2,
            "p_p_state": "normal",
            "p_p_mode": "view",
            "p_p_resource_id": "ajaxGetReportForRange",
            "p_p_cacheability": "cacheLevelPage",
            "p_p_col_id": "column-1",
            "p_p_col_pos": 3,
            "p_p_col_count": 6,
            "fromDate": str_date,
            "toDate": str_date,
            "channelIDs": 3,
            "currencies": "all"
        }
        return requests.get(cls.BASE_URL, params=payload).json()

    def _currencies_from_json_response(self, j: Dict) -> Set[Currency]:
        full_list = j["fullList"]
        channel = full_list[0]
        exchange_list = channel['exchangeModelForChannels'][0]['exchangeList']
        currencies = [self._currency_from_dict_elem(d) for d in exchange_list]
        return set(currencies)

    def _currency_from_dict_elem(self,
                                 d: Dict[str,
                                         Union[int, float, str]]) -> Currency:
        iso = d['iso']
        sell = d['sell']
        buy = d['buy']
        name = d['title']
        return Currency(name, iso, sell=sell, buy=buy)

    def get_all_currencies(self, date=None):
        """Get all available currencies for the given date
        (both sell and purchase)"""
        if date is None:
            date = datetime.date.today()
        json_data = self._response_for_date(date)
        return self._currencies_from_json_response(json_data)

    def get_currency(self, currency_name="USD", date=None):
        """Get currency data for the given currency name"""
        if date is None:
            date = datetime.date.today()

        if currency_name.upper() not in PriorbankParser.allowed_currencies:
            allowed = ", ".join(PriorbankParser.allowed_currencies)
            msg = "Incorrect currency '{}', allowed values: {}"
            raise ValueError(msg.format(currency_name, allowed))

        currencies = self.get_all_currencies(date=date)
        for currency in currencies:
            if currency.iso.upper() == currency_name:
                return currency
        return Currency.empty_currency()
        raise NotImplementedError

if __name__ == '__main__':
    parser = PriorbankParser()
    print(parser.get_currency())
