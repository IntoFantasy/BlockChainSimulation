from Crypto import Random
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
import base64
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs
from hashlib import *
from base58 import *


def convert_pubkey_to_addr(pubkey_str):
    sha = sha256(pubkey_str).digest()
    ripe = new('ripemd160', sha).digest()
    return b58encode_check(b'\x00' + ripe).decode()


"""
进行数字签名,需要明文和私钥
"""


def Sign(message, private_key):
    RSA_Key = RSA.importKey(private_key)
    signer = Signature_pkcs.new(RSA_Key)
    digest = SHA1.new()
    digest.update(str(message).encode())
    signature = base64.b64encode(signer.sign(digest))
    return signature


"""
数字签名验证
"""


# noinspection PyNoneFunctionAssignment
def Verify(message, public_key, signature):
    RSA_Key = RSA.importKey(public_key)
    verifier = Signature_pkcs.new(RSA_Key)
    digest = SHA1.new()
    digest.update(str(message).encode())
    is_matched = verifier.verify(digest, base64.b64decode(signature))
    return is_matched


class Wallet:
    def __init__(self):
        self.keys = []
        self.addrs = []

    def generate_keys(self):
        random_generator = Random.new().read
        # 获取一个rsa算法对应的密钥对生成器实例
        rsa = RSA.generate(1024, random_generator)
        # 私钥生成
        private_key = rsa.exportKey()
        # 公钥生成
        public_key = rsa.publickey().exportKey()
        self.keys.append((private_key, public_key))
        # 生成地址(待定)
        addr = convert_pubkey_to_addr(private_key)
        self.addrs.append(addr)

    @property
    def nok(self):
        return len(self.keys)





# test = Wallet()
# test.generate_keys()
# private_key = test.keys[0][0]
# public_key = test.keys[0][1]
# myaddr = test.addrs[0]
# # print(private_key)
# # print(myaddr)
# signature = Sign("sky", private_key=private_key)
# print(signature)
# signature = bytes(1)+signature[3:]
# print(signature)
# print(Verify("sky", public_key, signature))
