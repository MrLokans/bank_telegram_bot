# coding: utf-8

import logging
import typing


from bot.cache import AbstractCache
from bot.cache import mongo_settings as settings

Cur = typing.TypeVar('Cur')


class MongoCurrencyCache(AbstractCache):
    def __init__(self, currency_cls, logger_name):
        import pymongo
        self.server_delay = 10
        self.is_storage_available = False
        self.logger = logging.getLogger(name=logger_name)
        self.currency_cls = currency_cls
        try:
            setup = {
                'host': settings.MONGO_HOST,
                'port': int(settings.MONGO_PORT),
                'serverSelectionTimeoutMS': self.server_delay
            }
            self._client = pymongo.MongoClient(**setup)
            self._client.server_info()
            self._db = self._client[settings.MONGO_DATABASE]

            # self._db.authenticate(settings.MONGO_USER,
            #                       settings.MONGO_PASSWORD)
            self._collection = self._db[settings.MONGO_COLLECTION]
            self.is_storage_available = True
        except pymongo.errors.ServerSelectionTimeoutError:
            self.is_storage_available = False
        except pymongo.errors.OperationFailure:
            err_msg = "Incorrect credentials supplied: {} - {}"
            self.logger.error(err_msg.format(settings.MONGO_USER,
                                             settings.MONGO_PASSWORD))
            self.is_storage_available = False

    def get(self, key, key_type=None):
        item = self._collection.find_one({"currency_key": key})
        if item is not None:
            return item["value"]
        return None

    def put(self, key, value, key_type=None, key_value=None):
        item = {
            "currency_key": key,
            "value": value
        }
        self._collection.insert(item)
