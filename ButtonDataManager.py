BYTES_PER_INT = 3


class ButtonDataManager:
    PREVIEW = 0
    CHANGE_HIT = 1
    NOTHING = 2

    def __init__(self):
        self.btn_cnt = 0

    @staticmethod
    def ints2bytes(ints):
        return b''.join(x.to_bytes(BYTES_PER_INT, 'big') for x in ints)

    @staticmethod
    def bytes2ints(bs):
        return [int.from_bytes(bs[i:i + BYTES_PER_INT], 'big') for i in range(0, len(bs), BYTES_PER_INT)]

    def decode(self, bdata):
        ints = self.bytes2ints(bdata)
        if ints[0] == self.PREVIEW:
            return {
                'action': ints[0],
                'data': None
            }
        elif ints[0] == self.CHANGE_HIT:
            return {
                'action': ints[0],
                'data': ints[1]
            }
        elif ints[0] == self.NOTHING:
            return {
                'action': ints[0],
                'data': None
            }

    def cnt(self):
        self.btn_cnt += 1
        self.btn_cnt %= 2 ** (8 * BYTES_PER_INT)
        return self.btn_cnt

    def change_hit(self, n):
        return self.ints2bytes([self.CHANGE_HIT, n, self.cnt()])

    def preview(self):
        return self.ints2bytes([self.PREVIEW, self.cnt()])

    def nothing(self):
        return self.ints2bytes([self.NOTHING, self.cnt()])

    def check_change_hit(self, bdata):
        return self.decode(bdata)['action'] == self.CHANGE_HIT

    def check_preview(self, bdata):
        return self.decode(bdata)['action'] == self.PREVIEW

    def check_nothing(self, bdata):
        return self.decode(bdata)['action'] == self.NOTHING
