from trading import *
from block import *
from peer import Peer, logger
from config import *
import time


class BlockChain:
    def __init__(self):
        self.peers = []

    def create_genesis_block(self, number, value):
        self.init_peer(number)
        tx_in = [Vin(to_spend=None,
                     signature=str(os.urandom(32)),
                     pubkey=None)]

        tx_out = [Vout(value=value, to_addr=peer.wallet.addrs[-1])
                  for peer in self.peers]

        txs = [Tx(tx_in=tx_in, tx_out=tx_out, nlocktime=0)]
        genesis_block = Block(version=0,
                              prev_block_hash=None,
                              timestamp=time.time(),
                              bits=Config.Initial_Difficulty,
                              nonce=0,
                              txs=txs)

        logger.info('A blockchain p2p network created,{0} peers joined'.format(self.nop))
        logger.info('genesis block has been generated')

        utxos = find_utxos_from_block(txs)
        for peer in self.peers:
            peer.blockchain.append(genesis_block)
            add_utxos_to_set(peer.utxo_set, utxos)

    @property
    def nop(self):
        return len(self.peers)

    # 区块链创世者
    def init_peer(self, number=1):
        for _ in range(number):
            peer_ = Peer()
            create_peer(self, peer_)


def find_utxos_from_block(txs):
    return [UTXO(vout, Pointer(tx.id, i), tx.is_coinbase, True, True) for tx in txs for i, vout in enumerate(tx.tx_out)]


def add_utxos_to_set(utxo_set, utxos):
    if isinstance(utxos, dict):
        utxos = utxos.values()

    for utxo in utxos:
        utxo_set[utxo.pointer] = utxo


def create_peer(net, peer):
    peer.pid = net.nop
    peer.network = net
    peer.wallet.generate_keys()
    net.peers.append(peer)
