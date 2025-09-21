#!/usr/bin/env python3
import os, fcntl, struct
from scapy.all import Ether, IP, ICMP, raw
import time

def send_byte_stream(data: bytes, send):
    """
    data: バイト列
    send: 1文字（0~f）の文字列を送信する関数
    """
    for byte in data:
        # 上位4ビット
        high = (byte >> 4) & 0xF
        send(format(high, 'x'))  # 0~f に変換
        time.sleep(0.5)
        
        # 下位4ビット
        low = byte & 0xF
        send(format(low, 'x'))
        time.sleep(0.5)

src_ip=input("> ").strip()
pkt = Ether() / IP(src=src_ip, dst="0.0.0.0") / ICMP(type="echo-reply")
data = raw(pkt)
print(pkt)
print(data)
send_byte_stream(data,lambda b:print(b))
