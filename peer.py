import time
from wallet import *
import logging
from config import *
from trading import *
from block import *

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s')

logger = logging.getLogger(__name__)


def build_message(string):
    return hashlib.sha256(string).hexdigest().encode()


class Peer:
    def __init__(self):
        self.wallet = None
        self.txs = []
        self.candidate_block_txs = []
        self.blockchain = []
        self.has_wallet = False
        self.generate_wallet()
        self.current_tx = None
        self.utxo_set = {}
        self.mem_pool = {}
        self.fee = Config.FEE_TX
        self.pid = None
        self.orphan_pool = {}
        self._is_current_tx_created = False
        self._is_current_tx_sent = False
        self._is_block_candidate_created = False
        self.allow_utxo_from_pool = True
        self.network = None
        self._delayed_tx = None
        self.candidate_block = None

    def generate_wallet(self):
        if not self.has_wallet:
            self.wallet = Wallet()
            self.has_wallet = True

    @property
    def addr(self):
        return self.wallet.addrs[-1] if self.wallet.addrs else None

    """
    utxo模型
    """

    def get_utxo(self):
        return [utxo for utxo in self.utxo_set.values()
                if (utxo.vout.to_addr in self.wallet.addrs) and utxo.unspent]

    def get_unconfirmed_utxo(self):
        utxos = self.get_utxo()
        return [utxo for utxo in utxos if not utxo.confirmed]

    def get_confirmed_utxo(self):
        utxos = self.get_utxo()
        return [utxo for utxo in utxos if utxo.confirmed]

    def set_fee(self, value):
        self.fee = value

    def get_fee(self):
        return self.fee

    def get_height(self):
        return len(self.blockchain)

    """
    计算余额
    """

    def get_balance(self):
        utxos = self.get_utxo()
        return sum(utxo.vout.value for utxo in utxos)


    """
    创建一般交易
    """

    def create_transaction(self, to_addr, value):
        outputs = create_normal_tx(self, to_addr, value)
        if outputs:
            tx_in, tx_out, fee = outputs
            self.current_tx = Tx(tx_in, tx_out, fee, nlocktime=0)
            self.txs.append(self.current_tx)
            self._is_current_tx_created = True
            logger.info('{0}(pid={1}) created a transaction'.format(self, self.pid))
            return True
        return False

    """
    交易双方确认
    """

    def send_transaction(self):
        if not self.txs:
            return False

        if self._is_current_tx_created:
            sign_utxo_from_tx(self.utxo_set, self.current_tx)
            add_tx_to_mem_pool(self, self.current_tx)
            self._is_current_tx_created = False
            self._is_current_tx_sent = True
            logger.info("{0}(pid={1}) sent a transaction to network".format(self, self.pid))
            return True
        return False

    def receive_transaction(self, tx):
        if tx and (tx not in self.mem_pool):
            if self.verify_transaction(tx, self.mem_pool):
                add_tx_to_mem_pool(self, tx)
                return True
        return False

    """
    交易广播
    """

    def broadcast_transaction(self, tx=None):
        if not self._is_current_tx_sent:
            self.send_transaction()

        self._is_current_tx_created = False
        self._is_current_tx_sent = False

        tx = tx or self.current_tx
        if tx:
            peers = self.network.peers[:]
            peers.remove(self)
            number = broadcast_tx(peers, tx)
            self.current_tx = None

            logger.info("{0}(pid={1})'s transaction verified by {2} peers".format(self, self.pid, number))
            return number
        return 0

    """
    验证一笔交易
    """

    def verify_transaction(self, tx, pool={}):
        if tx in self.txs:
            return True
        return verify_tx(self, tx, pool)

    # 创建候选区块(未加入难度自动调整模块)
    def create_coinbase(self, value):
        return Tx.create_coinbase(self.wallet.addrs[-1], value=value)

    def create_candidate_block(self, prev_height):
        self.choose_tx_candidates()
        txs = self.candidate_block_txs
        fees = calculate_fees(self.txs)
        rewards = get_block_reward(prev_height + 1, fees)
        coinbase = self.create_coinbase(rewards + fees)
        # 创币交易应放在账本的第一条
        txs = [coinbase] + txs
        prev_block_hash = self.blockchain[-1].hash
        bits = Config.Initial_Difficulty
        self.candidate_block = Block(version=0,
                                     prev_block_hash=prev_block_hash,
                                     timestamp=time.time(),
                                     bits=bits,
                                     nonce=0,
                                     txs=txs or [])
        self._is_block_candidate_created = True

    def choose_tx_candidates(self):
        if not self.mem_pool:
            self.update_mem_pool(self.network.peers[0])
        self.candidate_block_txs = list(self.mem_pool.values())

    """
    验证区块
    """

    def verify_block(self, block):
        if self._delayed_tx:
            fill_mem_pool(self)

        if self.orphan_pool:
            check_orphan_tx_from_pool(self)

        if block == self.candidate_block:
            return True

        if not verify_winner_block(self, block):
            return False

        return True

    """
    peer links to p2p network
    """

    def login(self):
        assert self in self.network.off_peers, (
            "This peer does not connect to network or online"
        )
        repeat_log_in(self, self.network)
        self.update_blockchain()

    """
    peer logs out 
    """

    def logout(self):
        assert self in self.network.peers, (
            "This peer does not connect to network"
        )
        log_out(self, self.network)

    def update_blockchain(self, other):
        return update_chain(self, other)

    def update_mem_pool(self, other):
        if other._delayed_tx:
            fill_mem_pool(other)
        return update_pool(self, other.mem_pool)

    def update_utxo_set(self, other):
        self.utxo_set.update(other.utxo_set)


"""
辅助函数
"""


# 创建一般交易
def create_normal_tx(peer, to_addr, value):
    utxos, balance = peer.get_utxo(), peer.get_balance()
    fee, wallet = peer.fee, peer.wallet

    tx_in, tx_out = [], []
    value = value + fee
    if balance < value:
        logger.info('no enough money for transaction for {0}(pid = {1})'.format(peer, peer.pid))
        return
    # 以先小额再大额的策略使用utxo
    utxos = sorted(utxos, key=lambda UTXO: UTXO.vout.value)
    need_to_spend, n = 0, 0
    for i, utxo in enumerate(utxos):
        need_to_spend += utxo.vout.value
        if need_to_spend >= value:
            n = i + 1
            break
    # 可生成新的钥匙对保护安全
    # wallet.generate_keys()
    if need_to_spend > value:
        my_addr = wallet.addrs[-1]
        tx_out += [Vout(to_addr, value - fee), Vout(my_addr, need_to_spend - value)]
    else:
        tx_out += [Vout(to_addr, value - fee)]

    for utxo in utxos[:n]:
        addr = utxo.vout.to_addr
        idx = wallet.addrs.index(addr)
        sk, pk = wallet.keys[idx].sk, wallet.keys[idx].pk

        string = str(utxo.pointer) + str(pk) + str(tx_out)
        message = build_message(string)
        signature = Sign(message, sk)
        tx_in.append(Vin(utxo.pointer, signature, pk))

    return tx_in, tx_out, fee


# 写入交易池，但是不确定
def sign_utxo_from_tx(utxo_set, tx):
    for vin in tx.tx_in:
        pointer = vin.to_spend
        utxo = utxo_set[pointer]
        utxo = utxo._replace(unspent=False)
        utxo_set[pointer] = utxo


def add_tx_to_mem_pool(peer, tx):
    peer.mem_pool[tx.id] = tx
    # 如果允许使用未确认的utxo
    if peer.allow_utxo_from_pool:
        add_utxos_from_tx_to_set(peer.utxo_set, tx)


def add_utxos_from_tx_to_set(utxo_set, tx):
    utxos = find_utxos_from_tx(tx)
    for utxo in utxos:
        utxo_set[utxo.pointer] = utxo


def find_utxos_from_tx(tx):
    return [UTXO(vout, Pointer(tx.id, i), tx.is_coinbase) for i, vout in enumerate(tx.tx_out)]


# 计算交易费
def calculate_fees(txs=None):
    if txs is None:
        txs = []
    return sum(tx.fee for tx in txs)


"""
交易验证部分
"""


# 验证基本参数
def verify_tx_basic(tx):
    if not isinstance(tx, Tx):
        return False
    if (not tx.tx_out) or (not tx.tx_in):
        return False
    return True


# 验证双重支付
def double_payment(pool, tx):
    if tx.id in pool:
        return True
    a = {vin.to_spend for vin in tx.tx_in}
    b = {vin.to_spend for tx in pool.values() for vin in tx.tx_in}
    return a.intersection(b)


# 验证数字签名
def verify_signature_for_vin(vin, utxo, tx_out):
    pk_str, signature = vin.pubkey, vin.signature
    to_addr = utxo.vout.to_addr
    string = str(vin.to_spend) + str(pk_str) + str(tx_out)
    message = build_message(string)
    # 公钥转换为地址
    pubkey_as_addr = convert_pubkey_to_addr(pk_str)
    if pubkey_as_addr != to_addr:
        return False
    if not Verify(message, pk_str, signature):
        return False
    return True


def verify_tx(peer, tx, pool=None):
    if pool is None:
        pool = {}

    if not verify_tx_basic(tx):
        return False

    if double_payment(pool, tx):
        return False

    available_value = 0

    for vin in tx.tx_in:
        utxo = peer.utxo_set.get(vin.to_spend)
        if not utxo:
            peer.orphan_pool[tx.id] = tx
            return False

        if not verify_signature_for_vin(vin, utxo, tx.tx_out):
            return False

        available_value += utxo.vout.value
    if available_value < sum(vout.value for vout in tx.tx_out):
        return False
    return True


# 验证孤立池
def check_orphan_tx_from_pool(peer):
    copy_pool = peer.orphan_pool.copy()
    for tx in copy_pool.values():
        if not verify_tx(tx, peer.mem_pool):
            return False
        add_tx_to_mem_pool(peer, tx)
        del peer.orphan_pool[tx.id]
    return True


# 验证创币交易
def verify_coinbase(tx, reward):
    if not isinstance(tx, Tx):
        return False
    if not tx.is_coinbase:
        return False
    if (not (len(tx.tx_out) == 1)) or (tx.tx_out[0].value != reward):
        return False
    return True


# 定义挖矿的奖励：奖励随着挖出来的比特币数量而减少
def get_block_reward(height, fees=0):
    COIN = int(1e8)
    # 每100个区间将奖励减半
    reward_interval = 100
    initial_reward = 50 * COIN
    # 减半次数
    halvings = height // reward_interval
    if halvings >= 64:
        return fees

    reward = initial_reward >> halvings
    return reward + fees


# 交易广播(跟据情况实现)
def broadcast_tx(peer, current_tx):
    pass


# 登入与更新
def repeat_log_in(peer, net):
    net.off_peers.remove(peer)
    net.peers.append(peer)


def log_out(peer, net):
    net.peers.remove(peer)
    net.off_peers.append(peer)
    peer.mem_pool = []


def update_chain(peer, other):
    other_height = other.get_height()
    height = peer.get_height()
    if other_height > height:
        peer.blockchain = []
        for block in other.blockchain:
            peer.blockchain.append(block)
        return True
    return False


def update_pool(peer, pool):
    a, b = set(peer.mem_pool), set(pool)
    for tx_id in (b - a):
        tx = pool.get(tx_id)
        peer.mem_pool[tx_id] = tx

    if peer._delayed_tx:
        fill_mem_pool(peer)

    if peer.orphan_pool:
        check_orphan_tx_from_pool(peer)

    return True


def fill_mem_pool(peer):
    add_tx_to_mem_pool(peer, peer._delayed_tx)
    peer._delayed_tx = None


# 验证区块
def calculate_target(bits):
    return 1 << (256 - bits)


def verify_winner_block(peer, block):
    if not isinstance(block, Block):
        return False

    if int(block.hash, 16) > calculate_target(block.bits):
        logger.info('{0} wrong answer'.format(block))
        return False

    txs = block.txs
    if not isinstance(txs, list) and \
            not isinstance(txs, tuple):
        logger.info('incorrect txs type in {0}'.format(block))
        return False

    if len(txs) < 2:
        logger.info('no enough txs for txs {0}'.format(block))
        return False

    block_txs = txs[1:]
    rewards = get_block_reward(peer.get_height()) + calculate_fees(block_txs)
    if not verify_coinbase(block.txs[0], rewards):
        logger.info('{0} coinbase incorrect'.format(block))
        return False

    if double_payment_in_block_txs(block_txs):
        logger.info('double payment in {0}'.format(block))
        return False

    for tx in block_txs:
        if not verify_tx(peer, tx):
            return False
    return True


def double_payment_in_block_txs(txs):
    a = {vin.to_spend for tx in txs for vin in tx.tx_in}
    b = [vin.to_spend for tx in txs for vin in tx.tx_in]
    return len(a) != len(b)
