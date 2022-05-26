import time
import hashlib


def calculate_target(bits):
    return 1 << (256 - bits)


def mine(block):
    nonce = 0
    target = calculate_target(block.bits)
    merkle_root_hash = block.get_merkle_root()
    while int(hashlib.sha256(block.header(nonce, merkle_root_hash).encode()).hexdigest(), 16) >= target:
        nonce += 1
    return nonce


