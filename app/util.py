import numpy as np
LOW_FREQS = [697, 770, 852, 941]
HIGH_FREQS = [1209, 1336, 1477, 1633]

# DTMF周波数マップ
DTMF_FREQS = {
    0x1 : (697, 1209), 0x2 : (697, 1336), 0x3: (697, 1477), 0xa: (697, 1633),
    0x4: (770, 1209), 0x5: (770, 1336), 0x6: (770, 1477), 0xb: (770, 1633),
    0x7: (852, 1209), 0x8: (852, 1336), 0x9: (852, 1477), 0xc: (852, 1633),
    0xe: (941, 1209), 0x0: (941, 1336), 0xf: (941, 1477), 0xd: (941, 1633),
}

DURATION = 0.2  # トーン長さ（秒）
SILENCE_DURATION = 0.5  # 無音時間（秒）
MAX_FRAME_SIZE = 4096  # フレームサイズの最大
PACKET_TIMEOUT = 2.0  # 無音2秒でパケット終了

def goertzel(samples, freq, rate):
    n = len(samples)
    k = int(0.5 + n * freq / rate)
    w = 2 * np.pi * k / n
    coeff = 2 * np.cos(w)
    q0, q1, q2 = 0, 0, 0
    for s in samples:
        q0 = coeff*q1 - q2 + s
        q2, q1 = q1, q0
    return q1**2 + q2**2 - q1*q2*coeff