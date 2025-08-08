from functools import wraps
from time import time

def cache(ttl=3600):
    cache_dict = {}
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str((args, frozenset(kwargs.items())))
            now = time()
            if key in cache_dict:
                cached_time, result = cache_dict[key]
                if now - cached_time <= ttl:
                    return result
            result = await func(*args, **kwargs)
            cache_dict[key] = (time(), result)
            return result
        return wrapper
    return decorator
