from .base import AbstractCache


class DictionaryCache(AbstractCache):
    """This cache is not persistent, it's cleaned from request to request,
    so there is no real point of using it with out any data serialization and storage."""

    def __init__(self):
        self.is_available = True
        self.data = {}

    def put(self, key, value, key_type=None):
        self.data[key] = value
        print(self.data)

    def get(self, key, key_type=None):
        # TODO: think about the behaviour when items is not present
        return self.data.get(key, None)

    def delete(self, key, key_type=None):
        self.data.pop(key, None)

    @property
    def is_available(self):
        return True

    @is_available.setter
    def is_available(self, value):
        pass
