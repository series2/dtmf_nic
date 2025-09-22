import time
import numpy as np
from collections import deque
from app.util import DTMF_FREQS, DURATION,SILENCE_DURATION ,LOW_FREQS, HIGH_FREQS, PACKET_TIMEOUT, goertzel

RATE = 16000
FRAME_MS = 20             # 分析窓の長さ（ms）
STRIDE_MS = 5             # ストライド幅（ms）
CHUNK = int(RATE * STRIDE_MS / 1000)   # 読み取り単位
FRAME_LEN = int(RATE * FRAME_MS / 1000)  # 分析窓のサンプル数

TOTAL_THRESHOLD = 5e8
REL_THRESHOLD = 0.4
MIN_ACTIVE_FRAMES = max(2, int(DURATION / (FRAME_MS / 1000)))
MIN_SILENCE_FRAMES = max(2, int(0.5*SILENCE_DURATION/ (FRAME_MS / 1000)))
print(MIN_ACTIVE_FRAMES,MIN_SILENCE_FRAMES)
VOTE_SIZE = 5   # 投票に使う履歴フレーム数(全部でおよそ VOTE_SIZE * STRIDE_MS 時間)

class DTMFDecoder:
    def __init__(self, stream):
        self.stream = stream
        self.buffer = deque(maxlen=FRAME_LEN)  # 直近のサンプル保持
        self.detect_history = deque(maxlen=VOTE_SIZE)

    def recv(self):
        state = 'IDLE'
        active_frames = 0
        silence_frames = 0
        current_key = None
        byte_packet = bytearray()
        tmps = []
        last_active_time = time.time()

        while True:
            # 新しいチャンクを追加
            data = np.frombuffer(self.stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16).astype(np.float32)
            self.buffer.extend(data)

            # 分析窓が溜まるまで待つ
            if len(self.buffer) < FRAME_LEN:
                continue

            window = np.array(self.buffer)
            powers = {f: goertzel(window, f, RATE) for f in LOW_FREQS + HIGH_FREQS}
            #print(powers)
            #total_power = np.mean(window**2)
            total_power = sum(powers.values())/len(powers)

            low_max = max(powers[f] for f in LOW_FREQS)
            high_max = max(powers[f] for f in HIGH_FREQS)
            low_sum = sum(powers[f] for f in LOW_FREQS)
            high_sum = sum(powers[f] for f in HIGH_FREQS)
            #print(total_power)
            is_silence = (
                total_power < TOTAL_THRESHOLD or
                low_max / (low_sum + 1e-9) < REL_THRESHOLD or
                high_max / (high_sum + 1e-9) < REL_THRESHOLD
            )

            current_time = time.time()

            r = None
            if not is_silence:
                # DTMF判定
                low = max(LOW_FREQS, key=lambda f: powers[f])
                high = max(HIGH_FREQS, key=lambda f: powers[f])
                for k, (f1, f2) in DTMF_FREQS.items():
                    if f1 == low and f2 == high:
                        r = k
                        break

            # 履歴に追加（無音は特別に None として扱う）
            self.detect_history.append(None if is_silence else r)

            # 投票による判定（過半数に満たない場合はNone）
            votes = list(self.detect_history)
            detected = None
            if votes:
                candidate = max(set(votes), key=votes.count)
                if votes.count(candidate) > len(votes) // 2:
                    detected = candidate
            #print(detected)  
            

            # 無音扱い
            # print(detected,current_key,current_time-last_active_time)
            if detected is None:
                silence_frames += 1
                if current_key is None:
                    if current_time - last_active_time >= PACKET_TIMEOUT:
                        if len(tmps) >= 1:
                            byte_packet.append(tmps[0] << 4)
                            tmps = []
                        if len(byte_packet) > 0:
                            print("\nパケット終了: ", byte_packet.hex(), flush=True)
                        return byte_packet
                else:
                    if silence_frames >= MIN_SILENCE_FRAMES:
                        state = 'IDLE'
                        silence_frames = 0
                        active_frames = 0
                        current_key = None
                        last_active_time = current_time
                continue
            last_active_time = current_time

            if state == 'IDLE':
                state = 'ACTIVE'
                current_key = detected
                active_frames = 1
                silence_frames = 0
            elif state == 'ACTIVE':
                if detected == current_key:
                    active_frames += 1
                else:
                    current_key = detected
                    active_frames = 1
                    silence_frames = 0

            if active_frames == MIN_ACTIVE_FRAMES:
                if len(tmps) == 0 and len(byte_packet) == 0:
                    print("Recieving ... : ", end="", flush=True)
                tmps.append(current_key)
                if len(tmps) >= 2:
                    byte_packet.append(tmps[0] << 4 | tmps[1])
                    tmps = []
                print(hex(current_key)[2:], end="", flush=True)
                active_frames += 1

    def __exit__(self):
        self.close()

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
