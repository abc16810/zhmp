# coding: utf-8
from config.env import env
try:
    import cPickle as pickle
except ImportError:
    import pickle
import redis


REDIS_CLS = redis.StrictRedis
REDIS_PARAMS = {
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'encoding': 'utf-8',
    'url': env("CACHE_URL"),
}


def get_redis(**kwargs):
    """
    :param kwargs:
    :return:
    """
    redis_cls = kwargs.pop('redis_cls', REDIS_CLS)
    url = kwargs.pop('url', None)
    if url:
        return redis_cls.from_url(url, **kwargs)
    else:
        return redis_cls(**kwargs)


class Base(object):
    """redis base queue class"""

    def __init__(self, key, serializer=None):
        """初始化每个蜘蛛的redis 队列
        server： StrictRedis
        spider： Spider
        key： str
            Redis key
        serializer : object
            Serializer object with ``loads`` and ``dumps`` methods.
        """
        if serializer is None:
            serializer = pickle
        if not hasattr(serializer, 'loads'):
            raise TypeError("serializer does not implement 'loads' function: %r"
                            % serializer)
        if not hasattr(serializer, 'dumps'):
            raise TypeError("serializer '%s' does not implement 'dumps' function: %r"
                            % serializer)

        self.server = get_redis(**REDIS_PARAMS)
        self.key = key
        self.serializer = serializer

    def _encode(self, msg):
        """Encode a object"""
        return self.serializer.dumps(msg, protocol=-1)

    def _decode(self, encoded):
        """Decode an previously encoded"""
        return self.serializer.loads(encoded)

    def __len__(self):
        """Return the length of the queue"""
        raise NotImplementedError

    def push(self, request):
        """Push a request"""
        raise NotImplementedError

    def pop(self, timeout=0):
        """Pop a request"""
        raise NotImplementedError

    def clear(self):
        """Clear queue/stack"""
        self.server.delete(self.key)


class FifoQueue(Base):
    """"Per-spider FIFO queue"""

    def __len__(self):
        """Return the length of the queue"""
        return self.server.llen(self.key)

    def push(self, msg):
        """Push a request"""
        self.server.lpush(self.key, self._encode(msg))

    def pop(self, timeout=0):
        """Pop a request"""
        if timeout > 0:
            data = self.server.brpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            data = self.server.rpop(self.key)
        if data:
            return self._decode(data)
