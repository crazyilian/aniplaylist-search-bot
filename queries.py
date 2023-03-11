import urllib.parse
import difflib
import validators


def parse_aniplaylist_query(q):
    q = q.strip()
    if validators.url(q):
        p = urllib.parse.urlparse(q)
        return p.netloc + p.path
    if validators.url('https://' + q):
        p = urllib.parse.urlparse('https://' + q)
        return p.netloc + p.path
    return q


async def request_mal_animes(query, session):
    url = 'https://myanimelist.net/search/prefix.json'
    params = {
        'type': 'anime',
        'keyword': query,
        'v': 1
    }
    r = await session.get(url, params=params)
    if r.status != 200:
        return []
    data = await r.json()
    items = data.get('categories', [{}])[0].get('items', [])
    results = []
    for item in items:
        name = item.get('name')
        match = difflib.SequenceMatcher(None, name.lower(), query.lower()).ratio()
        payload = item.get('payload', {})
        key = (
            -match,
            dict(
                zip(('TV', 'Movie', 'OVA', 'Special', 'ONA', 'Music', None), range(7))
            ).get(payload.get('media_type')),
            -float('0' + payload.get('score', 'N/A').removeprefix('N/A')),
            -item.get('es_score', 0)
        )
        val = {
            'name': name,
            'id': item.get('id'),
            'url': item.get('url'),
            'score': payload.get('score', 'N/A'),
            'match': match
        }
        results.append((key, val))
    results.sort()
    results = [x[1] for x in results]
    return results


async def request_mal_anime(query, session):
    animes = await request_mal_animes(query, session)
    if len(animes) == 0:
        return None
    return animes[0]


async def request_aniplaylist(query, session, hit_limit=10):
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
        'hitsPerPage': 16,
        'maxValuesPerFacet': 200,
        'page': 0,
        'query': parse_aniplaylist_query(query)
    }
    request_data = {
        "requests": [
            {
                "indexName": "songs_prod",
                "params": urllib.parse.urlencode(data_params, quote_via=urllib.parse.quote)
            }
        ]
    }
    r = await session.post(url, params=params, json=request_data)
    if r.status != 200:
        return []
    data = await r.json()
    data = data.get('results', [{}])[0].get('hits', [])

    def filter_english(texts):
        return list(filter(
            lambda t: sum(ord(c) <= ord('z') for c in t) >= len(t) // 2,
            texts
        ))

    def get_anime_title_playlist_fix(hit):
        song_type = hit.get('song_type', '')
        titles = hit.get('anime_titles')
        if song_type.lower() != 'playlist':
            return (filter_english(titles) + titles)[0]
        title = (filter_english(filter(lambda t: '|' not in t, titles)) + filter_english(titles) + titles)[0]
        if '|' in title:
            title = title.rsplit('|', 1)[0].strip()
        return title

    def get_anime_title(hit):
        titles = hit.get('anime_titles')
        return (filter_english(titles) + titles)[0]

    def get_song_type(hit):
        song_type = hit.get('song_type', '')
        song_number = hit.get('song_number', '')
        eps = list(map(str, hit.get('episodes', [])))
        sub = hit.get('substitute', {}).get('name', '')
        res = song_type
        if song_number:
            res += ' ' + song_number
        if len(eps) == 1:
            res += f' (ep {eps[0]})'
        elif len(eps) >= 2:
            res += f' (eps {", ".join(eps)})'
        if sub:
            res += ' - ' + sub
        return res

    hits = [
        {
            'title': hit.get('titles')[0],
            'link': sorted(
                hit.get('links', [{}]),
                key=lambda l: (not l.get('link'), not l.get('main'), l.get('platform') != 'spotify')
            )[0].get('link'),
            'song_type': get_song_type(hit),
            'preview_link': hit.get('preview_url'),
            'artists': [
                {
                    'name': artist.get('names')[0],
                    'link': (sorted(artist.get('links', []), key=lambda l: 'spotify' not in l) or [None])[0]
                } for artist in hit.get('artists', [{}]) if artist.get('names')
            ],
            'anime_title': get_anime_title(hit),
            'anime': None
        } for hit in data[:hit_limit]
    ]
    for i, hit in enumerate(hits, 0):
        if hit['anime_title'] is not None:
            hit['anime'] = await request_mal_anime(get_anime_title_playlist_fix(data[i]), session)
    return hits
