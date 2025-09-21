import sys
import time
import numpy as np
import pyaudio
import select
import termios
import tty
from scapy.all import Ether, IP, ICMP, raw


# DTMF周波数マップ
DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'a': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'b': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'c': (852, 1633),
    'e': (941, 1209), '0': (941, 1336), 'f': (941, 1477), 'd': (941, 1633),
}

RATE = 8000
DURATION = 0.2  # トーン長さ（秒）

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=RATE,
                output=True)

def play_tone(key):
    # print("debug",key,key in DTMF_FREQS)
    if key not in DTMF_FREQS:
        return
    f1, f2 = DTMF_FREQS[key]
    t = np.linspace(0, DURATION, int(RATE*DURATION), False)
    wave = (np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t)) * 0.5
    stream.write(wave.astype(np.float32).tobytes())


# 端末設定保存＆rawモード
# fd = sys.stdin.fileno()
# old_settings = termios.tcgetattr(fd)
# tty.setcbreak(fd)

print("キーを押すとDTMFトーンが鳴ります (0-9, A-D, *, #) | Ctrl+Cで終了")

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

try:
    while True:
        src_ip=input("> ").strip()
        pkt = Ether() / IP(src=src_ip, dst="0.0.0.0") / ICMP(type="echo-reply")
        data = raw(pkt)
        # print(pkt)
        # print(data)
        send_byte_stream(data,lambda b:play_tone(b))

        # play_tone(key)
        time.sleep(0.01)  # CPU負荷軽減
except KeyboardInterrupt:
    print("\n終了")
finally:
    # termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    stream.stop_stream()
    stream.close()
    p.terminate()
