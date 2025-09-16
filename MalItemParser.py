import Levenshtein


class MalItemParser:
    def __init__(self, item, query):
        self.query = query
        self.item = item
        self.name = self.item.get('name')
        payload = self.item.get('payload', {})
        self.media_type = payload.get('media_type')
        self.score = payload.get('score', 'N/A').strip()
        self.mal_match = self.item.get('es_score', 0)
        self.url = self.item.get('url')
        self.levenshtein = Levenshtein.distance(self.name.lower(), self.query.lower())

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
            min(self.levenshtein, 2),
            -self.mal_match,  # maximum mal prefix match
            self.type_order,  # probably most popular
            -self.float_score,  # best score
        )

    @property
    def value(self):
        return {
            'name': self.name,
            'url': self.url,
            'score': self.score,
            'match': self.mal_match
        }
