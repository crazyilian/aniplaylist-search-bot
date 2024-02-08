import validators
import urllib.parse
from HitParser import HitParser
from MalRequests import request_mal_anime

HITS_PER_PAGE = 16
MAL_MATCH_LIMIT = 0.5


def process_aniplaylist_query(q):
    q = q.strip()
    if validators.url(q):
        p = urllib.parse.urlparse(q)
        return p.netloc + p.path
    if validators.url('https://' + q):
        p = urllib.parse.urlparse('https://' + q)
        return p.netloc + p.path
    return q


async def request_raw_aniplaylist(query, page, session):
    url = "https://p4b7ht5p18-dsn.algolia.net/1/indexes/*/queries"
    params = {
        'x-algolia-agent': 'Algolia for JavaScript (3.35.1); Browser (lite)',
        'x-algolia-application-id': 'P4B7HT5P18',
        'x-algolia-api-key': 'cd90c9c918df8b42327310ade1f599bd'
    }
    data_params = {
        'clickAnalytics': 'true',
        'facets': ["platforms", "song_type", "links.markets", "season", "links.label", "status"],
        'highlightPostTag': '__/ais-highlight__',
        'highlightPreTag': '__ais-highlight__',
        'hitsPerPage': HITS_PER_PAGE,
        'maxValuesPerFacet': 200,
        'page': page,
        'query': query
    }
    request_data = {
        "requests": [
            {
                "indexName": "songs_prod",
                "params": urllib.parse.urlencode(data_params, quote_via=urllib.parse.quote)
            }
        ]
    }
    return await session.post(url, params=params, json=request_data)


async def request_hit(query, n, session):
    page = n // HITS_PER_PAGE
    n %= HITS_PER_PAGE
    query = process_aniplaylist_query(query)

    r = await request_raw_aniplaylist(query, page, session)

    if r.status != 200:
        return {
            'hit': None,
            'total': 0
        }
    data = await r.json()
    data = data.get('results', [{}])[0]
    raw_hits = data.get('hits', [])
    total = data.get('nbHits', 0)

    if n >= len(raw_hits):
        return {
            'hit': None,
            'total': total
        }

    hitp = HitParser(raw_hits[n])
    hit = hitp.parse()
    if hitp.anime_title is not None:
        anime = await request_mal_anime(hitp.anime_title_playlist_fix, session)
        if anime and anime['match'] >= MAL_MATCH_LIMIT:
            hit['anime'] = anime
    return {
        'hit': hit,
        'total': total
    }
