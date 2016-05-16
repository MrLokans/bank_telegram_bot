import abc


class AbstractCache(object, metaclass=abc.ABCMeta):
    """Base class for cache classes, providing cache interface"""
    _instance = None

    @abc.abstractmethod
    def get(self, key, key_type=None):
        """Method to put item to cache"""
        pass

    @abc.abstractmethod
    def put(self, key, value, key_type=None, value_type=None):
        """Method to put item to cache"""
        pass

    def delete(self, key, key_type=None):
        """Method to delete item from cache"""
        pass

    def is_available(self):
        pass

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """Naive singleton method implementation"""
        if cls._instance is not None:
            return cls._instance
        return cls(*args, **kwargs)
