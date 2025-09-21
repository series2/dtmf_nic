import sys
import time
import numpy as np
import pyaudio
import select
import termios
import tty
from scapy.all import Ether, IP, ICMP, raw

from app.util import DTMF_FREQS, DURATION, PACKET_TIMEOUT, SILENCE_DURATION


RATE = 8000

class DTMFEncoder:
    def __init__(self,stream):
        self.stream=stream
    def play_tone(self, key):
        # print("debug",key,key in DTMF_FREQS)
        if key not in DTMF_FREQS:
            return
        f1, f2 = DTMF_FREQS[key]
        t = np.linspace(0, DURATION, int(RATE*DURATION), False)
        wave = (np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t)) * 0.5
        self.stream.write(wave.astype(np.float32).tobytes())

    def send(self,packet_data: bytes):
        """
        packet_data: バイト列
        send: 1文字（0~f）の文字列を送信する関数
        送信完了までブロッキングする
        """
        for byte in packet_data:
            # 上位4ビット
            high = (byte >> 4) & 0xF
            self.play_tone(high)  # 0~f に変換
            time.sleep(SILENCE_DURATION)
            
            # 下位4ビット
            low = byte & 0xF
            self.play_tone(low)
            time.sleep(SILENCE_DURATION)
        time.sleep(PACKET_TIMEOUT-SILENCE_DURATION) 
    

    def __exit__(self):
        self.close()
    
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
