# coding: utf-8


class BaseParser(object):

    is_active = False
    allowed_currencies = tuple()
    name = 'Base Parser'
    short_name = 'base'

    def get_all_currencies(self, date=None):
        """Get all available currencies for the given date
        (both sell and purchase)"""
        raise NotImplementedError

    def get_currency(self, currency_name="USD", date=None):
        """Get currency data for the given currency name"""
        raise NotImplementedError
