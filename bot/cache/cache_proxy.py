import datetime
from typing import (
    Sequence,
)

from bot.currency import Currency
from bot.settings import (
    DENOMINATION_DATE,
    DENOMINATION_MULTIPLIER
)

from threading import Lock


class CacheProxy(object):
    """
    Serves as a caching proxy to the given
    parser object
    """

    def __init__(self, cache):
        self._cache = cache

    def get_currency(self, parser,
                     currency_name: str='USD',
                     date: datetime.date=None) -> Currency:
        """
        Attempts to get exchange rate for the given
        date from the given parser. Attempts
        to get cached value is possible and
        caches the result otherwise
        """
        if date is None:
            date = datetime.date.today()

        сurrency = self.get_cached_currency(parser, currency_name, date)
        if сurrency is None:
            currency = parser.get_currency(currency_name, date)
        currency = self.denominate_currency(сurrency, date)
        return currency

    def get_all_currencies(self, parser,
                           date: datetime.date=None) -> Sequence[Currency]:
        if date is None:
            date = datetime.date.today()
        # TODO: investigate bulk caching of currencies
        # for example we may check. whether all of the
        # provided by parser currencies are cached
        # and return cached values if so\
        currencies = parser.get_all_currencies(date)
        denominated = [self.denominate_currency(c, date)
                       for c in currencies]
        for c in denominated:
            self.try_caching(c, date)
        return denominated

    def get_cached_currency(self, parser,
                            currency_name: str,
                            date: datetime.date) -> Currency:
        """
        Attempts to read currency for the given
        parser, currency name and date
        """
        today = datetime.date.today()
        if date == today:
            # Today exchange rates should never be persisted
            # as they may change across the day
            return None
        cached_item = self._cache.get_cached_value(parser.short_name,
                                                   currency_name,
                                                   date)
        # May be None
        return cached_item

    def try_caching(self, currency, date: datetime.date,
                    use_cache: bool=True):
        """
        Caches currency if cache is available and currency
        object is not empty
        """
        if not use_cache:
            return
        is_today = date == datetime.date.today()
        if not is_today and not currency.is_empty():
            self._cache.cache_currency(self.short_name,
                                       currency, date)

    def denominate_currency(self, currency,
                            date: datetime.date):
        """
        Checks, whether the given currency object
        been denominated or not, adds corresponding
        multiplier if possible
        """
        if not hasattr(currency, 'multiplier') or currency.multiplier == 0:
            if date < DENOMINATION_DATE:
                currency.multiplier = DENOMINATION_MULTIPLIER
            else:
                currency.multiplier = 1
        return currency
