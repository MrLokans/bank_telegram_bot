# import logging

import redis

from bot.cache import AbstractCache
from bot.cache import redis_settings as settings


class RedisCache(AbstractCache):
    """This class implements caching interface
    for redis backend"""

    def __init__(self, currency_cls, logger_name):

        prefs = {"host": settings.REDIS_HOST,
                 "port": settings.REDIS_PORT,
                 "db": settings.REDIS_DB}
        self._connection = redis.StrictRedis(**prefs)

    def get(self, key, key_type=None):
        try:
            item = self._connection.get('key')
            if item is not None:
                return item["value"]
        except redis.exceptions.ConnectionError:
            return None
        return None

    def put(self, key, value, key_type=None, key_value=None):
        try:
            self._connection.set(key, value)
        except redis.exceptions.ConnectionError:
            pass
