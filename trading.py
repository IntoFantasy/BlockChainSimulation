"""
建立交易模块
"""
import os
import hashlib


class Pointer(tuple):
    def __new__(cls, tx_id, n):
        return super(Pointer, cls).__new__(cls, (tx_id, n))

    @property
    def tx_id(self):
        return self[0]

    @property
    def n(self):
        return self[1]


class Vin(tuple):
    """
    UTXO定位指针，数字签名，公钥
    """

    def __new__(cls, to_spend, signature, pubkey):
        return super(cls, Vin).__new__(cls, (to_spend, signature, pubkey))

    @property
    def to_spend(self):
        return self[0]

    @property
    def signature(self):
        return self[1]

    @property
    def pubkey(self):
        return self[2]

    @property
    def sig_script(self):
        return self[3]


class Vout(tuple):
    """
    交易接收者的地址，交易金额
    """

    def __new__(cls, to_addr, value):
        return super(Vout, cls).__new__(cls, (to_addr, value))

    @property
    def to_addr(self):
        return self[0]

    @property
    def value(self):
        return self[1]

    @property
    def pubkey_script(self):
        script = "OP_DUP OP_ADDR {0} OP_EQ OP_CHECKSIG".format(self[0])
        return script


class Tx(tuple):
    def __new__(cls, tx_in, tx_out, fee=0, nlocktime=0):
        return super(Tx, cls).__new__(cls, (tx_in, tx_out, fee, nlocktime))

    @property
    def tx_in(self):
        return self[0]

    @property
    def tx_out(self):
        return self[1]

    @property
    def fee(self):
        return self[2]

    @property
    def nlocktime(self):
        return self[3]

    @property
    def is_coinbase(self) -> bool:
        return len(self[0]) == 1 and self[0][0].to_spend is None

    @classmethod
    def create_coinbase(cls, pay_to_addr, value):
        return cls(tx_in=[Vin(to_spend=None, signature=str(os.urandom(32)), pubkey=None)],
                   tx_out=[Vout(to_addr=pay_to_addr, value=value)])

    # 生成交易编号并加密
    @property
    def id(self):
        return hashlib.sha256(self.to_string().encode('utf-8')).hexdigest()

    def to_string(self):
        return "{0}{1}{2}".format(self[0], self[1], self[3])


class UTXO(tuple):
    def __new__(cls, vout, pointer, is_coinbase, unspent=True, confirmed=False):
        return super(UTXO, cls).__new__(cls, (vout, pointer, is_coinbase, unspent, confirmed))

    @property
    def vout(self):
        return self[0]

    @property
    def pointer(self):
        return self[1]

    @property
    def is_coinbase(self):
        return self[2]

    @property
    def pubkey_script(self):
        return self[0].pubkey_script

    @property
    def unspent(self):
        return self[3]

    @property
    def confirmed(self):
        return self[4]

    def _replace(self, unspent=True, confirmed=False):
        return UTXO(self[0], self[1], self[2], unspent, confirmed)
