from bot.cache import RedisCache
from bot.cache.cache_proxy import CacheProxy
from bot.cache.adapters import StrCacheAdapter

from bot.currency import Currency


default_cache = StrCacheAdapter(RedisCache(Currency, __name__),
                                Currency)
cache_proxy = CacheProxy(default_cache)
