# coding: utf-8
from abc import ABCMeta, abstractmethod

import datetime
import re

NUMBER_REGEX = re.compile(r'^\d+')


class BaseParser(object, metaclass=ABCMeta):

    is_active = False
    allowed_currencies = tuple()
    name = 'Base Parser'
    short_name = 'base'
    DENOMINATION_DATE = datetime.date(year=2016, month=7, day=1)
    DENOMINATION_MULTIPLIER = 10000

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

    def is_cache_set(self):
        return hasattr(self, '_cache') and self._cache

    def try_caching(self, currency, current_date: datetime.date,
                    today_date: datetime.date=None,
                    use_cache: bool=True):
        """
        Caches currency if cache is available and currency
        object is not empty
        """
        if today_date is None:
            today_date = datetime.date.today()
        if not use_cache:
            return
        if not self.is_cache_set():
            return
        is_today = today_date == current_date
        if not is_today and not currency.is_empty():
            self._cache.cache_currency(self.short_name,
                                       currency, current_date)

    def denominate_currencies(self, currencies, date):
        """
        Sets the correct multiplier for all of the
        currencies after the denomination date
        """
        if date < self.DENOMINATION_DATE:
            for c in currencies:
                c.multiplier = self.DENOMINATION_MULTIPLIER
                yield c
        else:
            for c in currencies:
                c.multiplier = 1
                yield c
