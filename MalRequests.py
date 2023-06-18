from MalItemParser import MalItemParser


async def request_raw_mal(query, session):
    url = 'https://myanimelist.net/search/prefix.json'
    params = {
        'type': 'anime',
        'keyword': query[:100],
        'v': 1
    }
    return await session.get(url, params=params)


async def request_mal_animes(query, session):
    r = await request_raw_mal(query, session)
    if r.status != 200:
        return []
    data = await r.json()
    items = data.get('categories', [{}])[0].get('items', [])
    itemps = [MalItemParser(item, query) for item in items]
    itemps.sort(key=lambda itemp: itemp.cmp_key)
    return [itemp.value for itemp in itemps]


async def request_mal_anime(query, session):
    animes = await request_mal_animes(query, session)
    if len(animes) == 0:
        return None
    return animes[0]
