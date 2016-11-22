import datetime


class CacheProxy(object):
    """
    Serves as a caching proxy to the given
    parser object
    """

    def __init__(self, cache):
        self._cache = cache

    def get_currency(self, parser,
                     currency_name: str='USD',
                     date: datetime.date=None):
        """
        Attempts to get exchange rate for the given
        date from the given parser. Attempts
        to get cached value is possible and
        caches the result otherwise
        """
        if date is None:
            date = datetime.date.today()
        return None

    def get_all_currencies(self, parser,
                           date: datetime.date=None):
        if date is None:
            date = datetime.date.today()
        return []
