import sys
import time
import numpy as np
import pyaudio
import select
import termios
import tty

# DTMF周波数マップ
DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477), 'D': (941, 1633),
}

RATE = 8000
DURATION = 0.2  # トーン長さ（秒）

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=RATE,
                output=True)

def play_tone(key):
    if key not in DTMF_FREQS:
        return
    f1, f2 = DTMF_FREQS[key]
    t = np.linspace(0, DURATION, int(RATE*DURATION), False)
    wave = (np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t)) * 0.5
    stream.write(wave.astype(np.float32).tobytes())

def get_key_nonblocking():
    """非ブロッキングで1文字取得"""
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1).upper()
    return None

# 端末設定保存＆rawモード
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
tty.setcbreak(fd)

print("キーを押すとDTMFトーンが鳴ります (0-9, A-D, *, #) | Ctrl+Cで終了")

try:
    while True:
        key = get_key_nonblocking()
        if key:
            print(key,end="", flush=True)  # 標準出力にも表示
            play_tone(key)
        time.sleep(0.01)  # CPU負荷軽減
except KeyboardInterrupt:
    print("\n終了")
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    stream.stop_stream()
    stream.close()
    p.terminate()
