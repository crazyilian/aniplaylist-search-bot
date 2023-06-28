class HitParser:
    def __init__(self, raw):
        self.raw = raw
        self.song_type = self.raw.get('song_type', '')
        self.anime_titles = self.raw.get('anime_titles', [])
        self.song_number = self.raw.get('song_number', '')
        self.episodes = self.raw.get('episodes', [])
        self.substitute = self.raw.get('substitute', {}).get('name', '')
        self.song_title = self.prefer_english(self.raw.get('titles'))
        self.song_links = [l for l in self.raw.get('links', []) if l and l.get('link')]
        self.preview_link = self.raw.get('preview_url')
        self.artists = self.raw.get('artists', [])

    @staticmethod
    def filter_english(texts):
        return list(filter(
            lambda t: sum(ord(c) <= ord('z') for c in t) >= len(t) // 2,
            texts
        ))

    @staticmethod
    def prefer_english(texts):
        return (HitParser.filter_english(texts) + texts)[0]

    @property
    def anime_title_playlist_fix(self):
        if self.song_type.lower() != 'playlist':
            return self.prefer_english(self.anime_titles)
        return self.prefer_english(sorted(self.anime_titles, key=lambda t: '|' in t))

    @property
    def anime_title(self):
        return self.prefer_english(self.anime_titles)

    @property
    def song_sub(self):
        sub = self.song_type
        if self.song_number:
            sub += ' ' + self.song_number
        if len(self.episodes) == 1:
            sub += f' (ep {self.episodes[0]})'
        elif len(self.episodes) >= 2:
            sub += f' (eps {", ".join(self.episodes)})'
        if self.substitute:
            sub += ' - ' + self.substitute
        return sub

    @property
    def song_link(self):
        if len(self.song_links) == 0:
            return None
        srt = sorted(self.song_links, key=lambda l: (not l.get('main'),  # firstly if main is True
                                                     l.get('platform') != 'spotify'))  # secondly prefer spotify
        return srt[0].get('link')

    @property
    def parsed_artists(self):
        p_artists = []
        for artist in self.artists:
            name = self.prefer_english(artist.get('names'))
            links = artist.get('links', [])
            links.sort(key=lambda l: 'spotify' not in l)  # first spotify links
            link = (links + [None])[0]
            p_artists.append({'name': name, 'link': link})
        return p_artists

    def parse(self):
        return {
            'title': self.song_title,
            'link': self.song_link,
            'song_type': self.song_sub,
            'preview_link': self.preview_link,
            'artists': self.parsed_artists,
            'anime_title': self.anime_title_playlist_fix,
            'anime': None
        }
