from trading import *
import re


def RemoveNone(arr):
    arr_new = []
    for element in arr:
        if element != '':
            arr_new.append(element)
    return arr_new


def VinParser(VinStr):
    tx_in = []
    process = VinStr.split('Vin')
    process.remove('')
    for vin in process:
        vin = vin.strip().strip(',')
        tx_id = vin[24:88]
        temp1 = vin.split(',signature:')
        temp2 = temp1[1].split(',pubkey:')
        n = int(temp1[0].split(',n:')[1].strip(')'))
        signature = eval(temp2[0])
        pubkey = eval(temp2[1].strip(')'))
        to_spend = Pointer(tx_id, n)
        tx_in.append(Vin(to_spend, signature, pubkey))
    return tx_in


def VoutParser(VoutStr):
    tx_out = []
    process = VoutStr.split('Vout')
    process.remove('')
    for vout in process:
        vout = vout.strip().strip(',')
        to_addr = vout.split(',value:')[0][9:]
        value = int(vout.split(',value:')[1].strip(')'))
        tx_out.append(Vout(to_addr, value))
    return tx_out


def TxParser(TxString):
    process = re.split(r'(?:[\[\]])', TxString)
    process = RemoveNone(process)
    tx_in = VinParser(process[0])
    tx_out = VoutParser(process[1])
    fee = int(process[2])
    return Tx(tx_in, tx_out, fee)
