# coding: utf-8

import logging

import pymongo

import cache.mongo_settings as settings


class MongoCurrencyCache(object):
    def __init__(self, currency_cls, logger_name):
        self.server_delay = 10
        self.is_storage_available = False
        self.logger = logging.getLogger(name=logger_name)
        self.currency_cls = currency_cls
        try:
            self._client = pymongo.MongoClient(settings.MONGO_HOST,
                                               int(settings.MONGO_PORT),
                                               serverSelectionTimeoutMS=self.server_delay)
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

    def get_cached_value(self, bank_name, cur_name, date_str):
        """Gets currency object from the cache.
        If currency is not present - returns None"""

        if not self.is_storage_available:
            msg = "Currency requested from cache but cache is unavailable."
            self.logger.info(msg)
            return None
        search_key = "{}_{}_{}".format(bank_name.lower(),
                                       cur_name.lower(),
                                       date_str.lower())
        item = self._collection.find_one({"currency_key": search_key})
        if item:
            item = self.currency_cls(cur_name.upper(),
                                     cur_name.upper(),
                                     item['sell_value'],
                                     item['buy_value'])
            return item
        return None

    def cache_currency(self, bank_name, cur_instance,
                       date_str):
        """Puts given currency into the cache"""
        dbg_msg = "Trying to cache currency {}-{}-{} in cache.".format(
            bank_name, cur_instance.sell, date_str
        )
        self.logger.debug(dbg_msg)

        if not self.is_storage_available:
            self.logger.info("Cache is unavailable.")
            return False
        save_key = "{}_{}_{}".format(bank_name.lower(),
                                     cur_instance.iso.lower(),
                                     date_str.lower())
        item = {
            "currency_key": save_key,
            "buy_value": cur_instance.buy,
            "sell_value": cur_instance.sell
        }
        self._collection.insert(item)
