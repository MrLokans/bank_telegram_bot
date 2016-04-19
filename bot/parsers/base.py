# coding: utf-8


class BaseParser(object):

    def get_all_currencies(self, date=None):
        raise NotImplemented

    def get_currency(self, currency_name="USD", date=None):
        raise NotImplemented
