import time
import numpy as np
# from scapy.all import Ether,

from app.util import DTMF_FREQS, DURATION, LOW_FREQS, HIGH_FREQS,PACKET_TIMEOUT,goertzel



RATE = 16000
FRAME_MS = 20        # フレーム長（ms単位）
CHUNK = int(RATE * FRAME_MS / 1000)

TOTAL_THRESHOLD = 1e7
REL_THRESHOLD = 0.5
MIN_ACTIVE_FRAMES = max(2, int(0.10 / (FRAME_MS / 1000)))
MIN_SILENCE_FRAMES = max(2, int(0.05 / (FRAME_MS / 1000)))



class DTMFDecoder:
    def __init__(self,stream):
        self.stream=stream
    
    def recv(self):
        # 受信があればブロッキングして受信、なければNoneを返す
        state = 'IDLE'
        active_frames = 0
        silence_frames = 0
        current_key = None
        byte_packet = bytearray()
        tmps=[]
        last_active_time = time.time()

        while True:
            data = np.frombuffer(self.stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16).astype(np.float32)
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
                    # if current_time - last_active_time >= PACKET_TIMEOUT and packet>:
                    if current_time - last_active_time >= PACKET_TIMEOUT:
                        # パケット終了

                        if len(tmps)>=1:
                            # add 0 padding
                            byte_packet.append(tmps[0]<<4 )
                            tmps=[]
                        if len(byte_packet)>0:
                            print("\nパケット終了: ", byte_packet.hex(), flush=True)
                        # pkt = Ether(byte_packet)
                        # print(pkt)
                        return byte_packet
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
                # continue
                # if len(packet)==0:
                    # return None

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
                if len(tmps)==0 and len(byte_packet)==0:
                    print("Recieving ... : " , end="",flush=True)
                tmps.append(current_key)
                if len(tmps)>=2:
                    byte_packet.append(tmps[0]<<4 | tmps[1])
                    tmps=[]
                print(hex(current_key)[2:], end="", flush=True)  # 途中経過を表示
                active_frames += 1  # 追加後、再度確定させないように増やす

            # if len(packet)==0:
                # return None



    def __exit__(self):
        self.close()
    
    def close(self):
        self.stream.stop_stream()
        self.stream.close()


