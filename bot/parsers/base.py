# coding: utf-8
from abc import ABCMeta, abstractmethod
import datetime


class BaseParser(object, metaclass=ABCMeta):

    is_active = False
    allowed_currencies = tuple()
    name = 'Base Parser'
    short_name = 'base'
    DENOMINATION_DATE = datetime.date(year=2016, month=7, day=1)

    @abstractmethod
    def get_all_currencies(self, date=None):
        """Get all available currencies for the given date
        (both sell and purchase)"""
        pass

    @abstractmethod
    def get_currency(self, currency_name="USD", date=None):
        """Get currency data for the given currency name"""
        pass

    def is_cache_set(self):
        return hasattr(self, '_cache') and self._cache

    def try_caching(self, currency, current_date, today_date, use_cache=True):
        """Caches currency if cache is available and currency
        object is not empty"""
        if not use_cache:
            return
        if not self.is_cache_set():
            return
        is_today = today_date == current_date
        if not is_today and not currency.is_empty():
            self._cache.cache_currency(self.short_name,
                                       currency, current_date)
