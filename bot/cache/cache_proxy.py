import datetime
from typing import Sequence, Union

from bot.currency import Currency
from bot.settings import (
    DENOMINATION_DATE,
    DENOMINATION_MULTIPLIER
)


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

        cached_currency = self.get_cached_currency(parser, currency_name, date)

        if cached_currency is None:
            currency = parser.get_currency(currency_name, date)
            currency = self.denominate_currency(currency, date)
        else:
            currency = self.denominate_currency(cached_currency, date)

        return currency

    def get_all_currencies(self, parser,
                           date: datetime.date=None) -> Sequence[Currency]:
        if date is None:
            date = datetime.date.today()
        return []

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
