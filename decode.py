import numpy as np
import pyaudio
import time

# DTMF周波数マップ (*->E, #->F)
DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
    'E': (941, 1209),  # * -> E
    '0': (941, 1336),
    'F': (941, 1477),  # # -> F
    'D': (941, 1633),
}

LOW_FREQS = [697, 770, 852, 941]
HIGH_FREQS = [1209, 1336, 1477, 1633]

RATE = 8000
FRAME_MS = 20        # フレーム長（ms単位）
CHUNK = int(RATE * FRAME_MS / 1000)

TOTAL_THRESHOLD = 1e7
REL_THRESHOLD = 0.5
MIN_ACTIVE_FRAMES = max(2, int(0.10 / (FRAME_MS / 1000)))
MIN_SILENCE_FRAMES = max(2, int(0.05 / (FRAME_MS / 1000)))
PACKET_TIMEOUT = 5.0  # 無音5秒でパケット終了

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

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print(f"マイクからDTMFを受信中 (フレーム長={FRAME_MS}ms)... Ctrl+Cで終了")

state = 'IDLE'
active_frames = 0
silence_frames = 0
current_key = None
packet = []
last_active_time = time.time()

try:
    while True:
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16).astype(np.float32)
        powers = {f: goertzel(data, f, RATE) for f in LOW_FREQS + HIGH_FREQS}
        total_power = sum(powers.values())

        # 無音判定
        low_max = max(powers[f] for f in LOW_FREQS)
        high_max = max(powers[f] for f in HIGH_FREQS)
        low_sum = sum(powers[f] for f in LOW_FREQS)
        high_sum = sum(powers[f] for f in HIGH_FREQS)

        is_silence = (total_power < TOTAL_THRESHOLD or
                      low_max / low_sum < REL_THRESHOLD or
                      high_max / high_sum < REL_THRESHOLD)

        current_time = time.time()

        # 無音でパケットタイムアウトチェック
        if is_silence:
            silence_frames += 1
            if current_key is None:
                # 無音のみで IDLE
                if current_time - last_active_time >= PACKET_TIMEOUT and packet:
                    # パケット終了
                    print("\nパケット終了: ","".join(packet), flush=True)
                    packet = []
                    last_active_time = current_time
            else:
                # ACTIVE中の無音フレーム
                if silence_frames >= MIN_SILENCE_FRAMES:
                    state = 'IDLE'
                    silence_frames = 0
                    active_frames = 0
                    current_key = None
                    last_active_time = current_time
            continue

        # DTMF判定
        low = max(LOW_FREQS, key=lambda f: powers[f])
        high = max(HIGH_FREQS, key=lambda f: powers[f])
        detected = None
        for k, (f1, f2) in DTMF_FREQS.items():
            if f1 == low and f2 == high:
                detected = k
                break
        if detected is None:
            # 無効な音は無視
            silence_frames += 1
            continue

        last_active_time = current_time  # トーンがあるのでタイマーリセット

        # 状態遷移
        if state == 'IDLE':
            state = 'ACTIVE'
            current_key = detected
            active_frames = 1
            silence_frames = 0
        elif state == 'ACTIVE':
            if detected == current_key:
                active_frames += 1
            else:
                state = 'ACTIVE'
                current_key = detected
                active_frames = 1
                silence_frames = 0

        # キー確定
        if active_frames == MIN_ACTIVE_FRAMES:
            packet.append(current_key)
            print(current_key, end="", flush=True)  # 途中経過を表示
            active_frames += 1  # 追加後、再度確定させないように増やす

except KeyboardInterrupt:
    print("\n終了")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
