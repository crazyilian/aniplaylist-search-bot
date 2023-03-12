import aiohttp
from cache import AsyncTTL
import json


def async_ttl_cache(maxsize, ttl):
    def dec(func):
        @AsyncTTL(maxsize=maxsize, time_to_live=ttl, skip_args=1)
        async def cached_str_f(self, json_str):
            data = json.loads(json_str)
            args = data['args']
            kwargs = data['kwargs']
            return await func(self, *args, **kwargs)

        async def newf(self, *args, **kwargs):
            json_str = json.dumps({'args': args, 'kwargs': kwargs})
            return await cached_str_f(self, json_str)

        return newf

    return dec


class CachedSession:
    def __init__(self, headers):
        self.session = aiohttp.ClientSession(headers=headers)

    @async_ttl_cache(maxsize=256, ttl=5 * 60)
    async def get(self, url, **kwargs):
        return await self.session.get(url, **kwargs)

    @async_ttl_cache(maxsize=256, ttl=5 * 60)
    async def post(self, url, **kwargs):
        return await self.session.post(url, **kwargs)
