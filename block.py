import hashlib


class Block(tuple):
    # 版本，前哈希值，时间戳，挖矿难度，工作量证明，交易合计
    def __new__(cls, version, prev_block_hash, timestamp, bits, nonce, txs):
        return super(Block, cls).__new__(cls, (version, prev_block_hash, timestamp, bits, nonce, txs))

    @property
    def version(self):
        return self[0]

    @property
    def prev_block_hash(self):
        return self[1]

    @property
    def timestamp(self):
        return self[2]

    @property
    def bits(self):
        return self[3]

    @property
    def nonce(self):
        return self[4]

    @property
    def txs(self):
        return self[5]

    def _replace(self, nonce=0):
        return Block(self[0], self[1], self[2], self[3], nonce, self[5])

    def header(self, nonce=None, merkle_root_hash=None):
        if merkle_root_hash is None:
            merkle_root_hash = self.get_merkle_root()
        return "{0}{1}{2}{3}{4}{5}".format(self[0], self[1], self[2], self[3], merkle_root_hash, nonce or self[4])

    @property
    def hash(self):
        return hashlib.sha256(self.header().encode()).hexdigest()

    @property
    def merkle_root_hash(self):
        return self.get_merkle_root()

    def get_merkle_root(self):
        return get_merkle_root_of_txs(self.txs) if self.txs else None


def pair_node(l):
    return (l[i:i + 2] for i in range(0, len(l), 2))


# 计算梅克尔树根哈希值
def get_merkle_root(level):
    while len(level) != 1:
        odd = None
        if len(level) % 2 == 1:
            odd = level.pop()
        # 合并得到新得到层级
        level = [hashlib.sha256((i1 + i2).encode()).hexdigest() for i1, i2 in pair_node(level)]
        if odd:
            level.append(odd)
    return level[0]


# 计算交易的梅克尔树根哈希值
def get_merkle_root_of_txs(txs):
    return get_merkle_root([tx.id for tx in txs])


