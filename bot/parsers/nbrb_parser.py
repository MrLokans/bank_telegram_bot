# coding: utf-8

import datetime
from typing import Sequence

import requests
from lxml import etree

from bot.currency import Currency
from bot.parsers.base import BaseParser


class NBRBParser(BaseParser):
    is_active = True
    BASE_URL = 'http://www.nbrb.by/Services/XmlExRates.aspx'
    DATE_FORMAT = "%m/%d/%Y"
    name = 'Нацбанк РБ'
    short_name = 'nbrb'
    MINIMAL_DATE = datetime.date(year=1996, month=1, day=1)
    allowed_currencies = ('AUD', 'ATS', 'AZM', 'AMD', 'BEF',
                          'BGL', 'HUF', 'GRD', 'GEL', 'DKK',
                          'USD', 'JPY', 'IEP', 'ISK', 'ESP',
                          'ITL', 'KZT', 'CAD', 'KWD', 'KGS',
                          'LVL', 'LBP', 'LTL', 'MDL', 'DEM',
                          'NLG', 'NOK', 'PLZ', 'PTE', 'RUR',
                          'ROL', 'XDR', 'SGD', 'SKK', 'TJR',
                          'TRL', 'TMM', 'UZS', 'UAK', 'FIM',
                          'FRF', 'GBP', 'CZK', 'SEK', 'CHF',
                          'XEU', 'EEK', 'EUR', 'BYN')

    def __init__(self,
                 parser: str="html.parser",
                 cache=None,
                 *args, **kwargs) -> None:
        self.name = NBRBParser.name
        self.short_name = NBRBParser.short_name
        self._cache = cache
        self._parser = parser

    @classmethod
    def _response_text_for_date(cls, date: datetime.date) -> str:
        if date < cls.MINIMAL_DATE:
            msg = """\
Date you are trying to request is to old, minimal date is {}
""".format(cls.MINIMAL_DATE)
            raise ValueError(msg)
        date_str = date.strftime(cls.DATE_FORMAT)
        r = requests.get(cls.BASE_URL, params={"ondate": date_str})
        r.encoding = 'utf-8'
        # TODO: handle exceptions
        return r.text

    def _currency_from_xml_obj(self,
                               xml_tree: etree._Element,
                               currency_name: str) -> Currency:
        xpath = 'Currency/CharCode[text()="{}"]/..'
        res = xml_tree.xpath(xpath.format(currency_name.upper()))
        c = res[0]

        name = iso = c.find('CharCode').text
        sell_value = c.find('Rate').text

        c = Currency(name, iso, sell_value, None)
        return c

    def _currency_from_xml_text(self,
                                xml_text: str,
                                currency_name: str) -> Currency:

        tree = etree.fromstring(xml_text)
        return self._currency_from_xml_obj(tree, currency_name)

    def get_all_currencies(self,
                           date: datetime.date=None) -> Sequence[Currency]:
        # TODO: add aggressive caching
        today = datetime.date.today()
        if date is None:
            date = today

        _xml = self._response_text_for_date(date)
        tree = etree.fromstring(_xml)
        currencies_xpath = 'Currency/CharCode/text()'
        available_currencies = tree.xpath(currencies_xpath)

        results = [self._currency_from_xml_obj(tree, c)
                   for c in available_currencies]
        for currency in results:
            if date < self.DENOMINATION_DATE:
                currency.multiplier = 10000
            else:
                currency.multiplier = 1
        return results

    def get_currency(self, currency_name="USD", date=None):
        today = datetime.date.today()
        if date is None:
            date = today

        _xml = self._response_text_for_date(date)
        currency = self._currency_from_xml_text(_xml, currency_name)
        if date < self.DENOMINATION_DATE:
            currency.multiplier = 10000
        else:
            currency.multiplier = 1
        return currency
