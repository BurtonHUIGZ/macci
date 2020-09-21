# -*-encoding: utf-8 -*-
#
# @author gaoyuan
#
# Mar 2017

from codex.basehandler import BaseHandler, settings
from functools import wraps
import redis


class CacheHandler(BaseHandler):
    __slots__ = ('client',)

    def __init__(self, host, port, db, password):
        self.client = redis.Redis(host, port=port, db=db, password=password)

    # strings
    def get(self, key, load=True):
        value = self.client.get(key)
        if value and load:
            return self.loads(value)
        return value.decode() if isinstance(value, bytes) else value

    def set(self, key, value, expire=settings.cache_expire, dumps=False):
        if dumps:
            self.client.set(key, self.dumps(value), expire)
        else:
            self.client.set(key, value, ex=expire)

    def delete(self, *key):
        self.client.delete(*key)

    # lists
    def lpush(self, name, *values):
        """Push ``values`` onto the head of the list ``name``"""
        return self.client.lpush(name, *values)

    def rpush(self, name, *values):
        """Push ``values`` onto the tail of the list ``name``"""
        return self.client.rpush(name, *values)

    def lrange(self, name, start, end):
        """
        Return a slice of the list ``name`` between
        position ``start`` and ``end``

        ``start`` and ``end`` can be negative numbers just like
        Python slicing notation
        """
        return self.client.lrange(name, start, end)

    # hashes
    def hmset(self, name, mapping):
        """
        Set key to value within hash ``name`` for each corresponding
        key and value from the ``mapping`` dict.
        """
        self.client.hmset(name, mapping)

    def hget(self, name, key):
        """Return the value of ``key`` within the hash ``name``"""
        return self.client.hget(name, key)

    # sets
    def sadd(self, name, *values):
        """Add ``value(s)`` to set ``name``"""
        self.client.sadd(name, *values)

    def smembers(self, name):
        """Return all members of the set ``name``"""
        return self.client.smembers(name)

    def api(self, expire):

        def func_wrapper(func):

            @wraps(func)
            def _func_wrapper(cls, *args, **kwargs):

                if cls.request.method.lower() != 'get':
                    return func(cls, *args, **kwargs)
                key = cls.request.path_info + '?' + self.urlencode(
                    {k: v.encode('utf-8') for k, v in list(cls.request.GET.items())})
                if getattr(cls.request, 'user', None):
                    key += "user_id=" + str(cls.request.user.get('user_id'))
                hash_key = key
                if settings.cache:
                    resp = self.get(hash_key)
                    if resp is None:
                        resp = func(cls, *args, **kwargs)
                        self.set(hash_key, resp, expire, dumps=True)
                    else:
                        print('hit cache: %s' % key)
                else:
                    resp = func(cls, *args, **kwargs)
                return resp

            return _func_wrapper

        return func_wrapper

    def clean_api(self, key):
        if settings.cache:
            for k in self.client.keys(key):
                self.client.delete(k)
                print("clean cache %s" % k)

    def clean_api_with_user(self, cls, key):
        if settings.cache:
            if getattr(cls.request, 'user', None):
                key += '?' + cls.request.user.get('uid')
            self.client.delete(key)

    @staticmethod
    def _hash_lock_key(key, prefix=''):
        if isinstance(key, dict):
            hash_key = '_'.join(key.values())
        elif isinstance(key, (list, set, tuple)):
            hash_key = '_'.join(key)
        elif isinstance(key, (str, bytes, int)):
            hash_key = str(key)
        elif isinstance(key, object):
            hash_key = repr(key)
        else:
            raise Exception("""
                Wrong Lock Object! available object is dict, list, set, tuple, str, bytes, int, object
            """)
        hash_key = '_'.join([prefix, hash_key])
        return hash_key

    def lock_acqure(self, prefix='', key=None, expire=None):
        """
            redis加锁
        """
        hash_key = self._hash_lock_key(prefix=prefix, key=key)
        if self.get(hash_key):
            return False
        self.set(key=hash_key, value=1, expire=expire)
        return True

    def lock_release(self, prefix='', key=None):
        """
            redis释放锁
        """
        hash_key = self._hash_lock_key(prefix=prefix, key=key)
        return self.client.delete(hash_key)


cache = CacheHandler(settings.cache_host,
                     settings.cache_port,
                     settings.cache_db,
                     settings.cache_password)

redis_client = cache.client

if __name__ == '__main__':
    print(redis_client.get("1"))
