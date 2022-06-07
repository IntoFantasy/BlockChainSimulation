import time

from peer import *
from block import *
import consensus
from blockchain import *
import re
from StrParser import *

# p1 = Peer()
# p2 = Peer()
# # trade = create_normal_tx(p1, p2.addr, 2)
# # print(p1.get_utxo())
# p1.wallet.generate_keys()
# # print(p1.addr)
# trade = Tx.create_coinbase(p1.addr, 1000)
# add_tx_to_mem_pool(p1, trade)
# print(p1.get_utxo())
# print(trade.fee)
# # print(trade.tx_out)
# # print([UTXO(vout, Pointer(trade.id, i), trade.is_coinbase) for i, vout in enumerate(trade.tx_out)])

# p = Pointer(1, 2)
# vout = Vout(1, 2)
# vin = Vin(p, b'1', b'12')
# tx = Tx([vin], [vout])
# block = Block(1, 2, 3, 4, 5, [tx, tx])
# print(tx.id)
# print(hashlib.sha256(tx.id.encode()+tx.id.encode()).hexdigest())
# print(block.merkle_root_hash)
# block = Block(1, 2, 3, 4, 5, [tx, tx, tx, tx])
# print(block.merkle_root_hash)

# y = 1 << 248
# nonce = 0
# s = "love"
# while int(hashlib.sha256((s+str(nonce)).encode()).hexdigest(), 16) >= y:
#     nonce += 1
# print(nonce)
# print(int(sha256((s+str(nonce+1)).encode()).hexdigest(), 16) < y)

# vin = Vin(to_spend=None, signature=b'1', pubkey=None)
# vout = Vout(to_addr='1', value=100)
# tx = Tx([vin], [vout])
# block = Block(version=1.0, prev_block_hash=None, timestamp=time.time(), bits=25, nonce=12345, txs=[tx])
# # print(block.header())
# # print(block.header(11))
# print(consensus.mine(block))


net = BlockChain()
net.create_genesis_block(11, 5000)
p1 = net.peers[0]
p2 = net.peers[1]
p1.create_transaction(p2.wallet.addrs[-1], 200)
print(p1.current_tx)
tx_string = p1.current_tx.to_string()
print(tx_string)
print(p2.verify_transaction(p1.current_tx))
# process = re.split(r'(?:[\[\]])',  tx_string)
# process = RemoveNone(process)
# tx_in = VinParser(process[0])
# print(tx_in)
# print(p1.current_tx.tx_out)
# tx_out = VoutParser(process[1])
# print(tx_out)
# print(process[2])
Tx_new = TxParser(tx_string)
print(Tx_new)
print(Tx_new.to_string() == tx_string)
