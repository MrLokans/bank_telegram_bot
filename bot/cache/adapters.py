"""
This module contains a number of adapter class to caching facilities.
In terms of business logic we'd like to talk about saving currency in cache,
and in terms of administration we'd like to have abstract cache back-ends
so adapters help us to provide high-level interface to low-level cache
operations.
"""


class StrCacheAdapter(object):

    def __init__(self, cache, currency_cls):
        self.cache = cache
        self.currency_cls = currency_cls

    def get_cached_value(self, bank_short_name: str,
                         currency_name: str,
                         str_date: str):
        search_key = "{}_{}_{}".format(bank_short_name.lower(),
                                       currency_name.lower(),
                                       str_date.lower())
        str_result = self.cache.get(search_key)
        if str_result is None:
            return None
        buy, sell, multiplier = str_result.split(",")
        c = self.currency_cls(currency_name,
                              currency_name,
                              buy=float(buy),
                              sell=float(sell),
                              multiplier=int(multiplier))
        return c

    def cache_currency(self,
                       bank_short_name: str,
                       cur_instance,
                       str_date: str) -> None:
        search_key = "{}_{}_{}".format(bank_short_name.lower(),
                                       cur_instance.iso.lower(),
                                       str_date.lower())
        multiplier = 1
        if hasattr(cur_instance, "multiplier"):
            multiplier = cur_instance.multiplier
        str_value = ",".join([str(cur_instance.buy),
                              str(cur_instance.sell),
                              str(multiplier)])
        self.cache.put(search_key, str_value)
