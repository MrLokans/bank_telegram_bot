# coding: utf-8
from abc import ABCMeta, abstractmethod


class BaseParser(object, metaclass=ABCMeta):

    is_active = False
    allowed_currencies = tuple()
    name = 'Base Parser'
    short_name = 'base'

    @abstractmethod
    def get_all_currencies(self, date=None):
        """Get all available currencies for the given date
        (both sell and purchase)"""
        pass

    @abstractmethod
    def get_currency(self, currency_name="USD", date=None):
        """Get currency data for the given currency name"""
        pass
