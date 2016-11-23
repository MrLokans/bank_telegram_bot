# coding: utf-8
from abc import ABCMeta, abstractmethod

import re

NUMBER_REGEX = re.compile(r'^\d+')


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

    def _multiplier_from_name(self, name: str) -> int:
        """
        Attempts to extract multiplier from
        the currency name
        >>> p._multiplier_from_name('100 RUB')
        >>> 100
        >>> p._multiplier_from_name('USD')
        >>> 1
        """
        match = NUMBER_REGEX.match(name)
        if match:
            return int(match.group(0))
        return 1

    @abstractmethod
    def get_currency(self, currency_name="USD", date=None):
        """Get currency data for the given currency name"""
        pass
