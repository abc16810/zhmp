# -*- coding: utf-8 -*
from django.core.cache import cache
import hashlib
import time


def _cache_key(request, *, action, key=None, user=None):
    keys = ["mp", "rl", action]
    if key is not None:
        key_hash = hashlib.sha256(key.encode("utf8")).hexdigest()
        keys.append(key_hash)
    return ":".join(keys)


def consume(request, *, action, key=None, amount=None, duration=None, user=None):
    allowed = True
    if request.method == "GET" or not amount or not duration:
        pass
    else:
        cache_key = _cache_key(request, action=action, key=key, user=user)
        history = cache.get(cache_key, [])
        now = time.time()
        while history and history[-1] <= now - duration:
            history.pop()
        allowed = len(history) < amount
        if allowed:
            history.insert(0, now)
            cache.set(cache_key, history, duration)
    return allowed


def clear(request, *, action, key=None, user=None):
    cache_key = _cache_key(request, action=action, key=key, user=user)
    cache.delete(cache_key)

