import difflib


class MalItemParser:
    def __init__(self, item, query):
        self.item = item
        self.name = self.item.get('name')
        self.match = difflib.SequenceMatcher(None, self.name.lower(), query.lower()).ratio()
        payload = self.item.get('payload', {})
        self.media_type = payload.get('media_type')
        self.score = payload.get('score', 'N/A').strip()
        self.mal_match = self.item.get('es_score', 0)
        self.url = self.item.get('url')

    @property
    def type_order(self):
        order = ('TV', 'Movie', 'OVA', 'Special', 'ONA', 'Music')
        if self.media_type not in order:
            return len(order)
        return order.index(self.media_type)

    @property
    def float_score(self):
        score = self.score.removesuffix('N/A')
        if not score:
            return 0
        return float(score)

    @property
    def cmp_key(self):
        return (
            -self.match,  # maximum actual match
            self.type_order,  # probably most popular
            -self.float_score,  # best score
            -self.mal_match  # maximum mal prefix match
        )

    @property
    def value(self):
        return {
            'name': self.name,
            'url': self.url,
            'score': self.score,
            'match': self.match
        }
