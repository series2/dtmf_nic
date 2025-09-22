import time
import numpy as np
import tqdm
from app.util import DTMF_FREQS, DURATION, PACKET_TIMEOUT, SILENCE_DURATION
# import wave
# import os

RATE = 44100
CHUNK=128 # tiisai hodo anntei suru rasii

class DTMFEncoder:
    def __init__(self,stream):
        self.stream=stream
    def play_tone(self, key=None):
        # print("debug",key,key in DTMF_FREQS)
        if key is None or key not in DTMF_FREQS:
            t = np.linspace(0, SILENCE_DURATION, int(RATE*SILENCE_DURATION), False)
            wave_data = (np.sin(2*np.pi*0*t) + np.sin(2*np.pi*0*t)) * 0
            wave_data=(wave_data*((2<<14) -1)).astype(np.int16)
            # for start in range(0,len(wave_data),CHUNK):
                # self.stream.write(wave_data[start:start+CHUNK].tobytes())
            return wave_data
        f1, f2 = DTMF_FREQS[key]
        t = np.linspace(0, DURATION, int(RATE*DURATION), False)
        wave_data = (np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t)) * 0.2
        
        fade_len=int(0.01*RATE)
        envelope = np.ones(len(wave_data))
        envelope[:fade_len]=np.linspace(0,1,fade_len)
        envelope[-fade_len:]=np.linspace(1,0,fade_len)
        wave_data*=envelope

        wave_data=(wave_data*((2<<14) -1)).astype(np.int16)
        # for start in range(0,len(wave_data),CHUNK):
        #     self.stream.write(wave_data[start:start+CHUNK].tobytes())
        # self.stream.write(wave.tobytes())
        return wave_data



        

    def send(self,packet_data: bytes):
        """
        packet_data: バイト列
        send: 1文字（0~f）の文字列を送信する関数
        送信完了までブロッキングする
        """
        wave_data=[]
        for byte in tqdm.tqdm(packet_data):
            # 上位4ビット
            high = (byte >> 4) & 0xF
            data=self.play_tone(high)
            wave_data.append(data)
            # time.sleep(SILENCE_DURATION)
            data=self.play_tone(None)
            wave_data.append(data)
            
            # 下位4ビット
            low = byte & 0xF
            data=self.play_tone(low)
            wave_data.append(data)
            # time.sleep(SILENCE_DURATION)
            data=self.play_tone(None)
            wave_data.append(data)
        self.stream.write(np.concatenate(wave_data).tobytes())
        # file="tmp.wav"
        # while os.path.exists(file):
        #     file="1"+file
        # with wave.open(file,"wb") as wf:
        #     wf.setnchannels(1)
        #     wf.setsampwidth(2)
        #     wf.setframerate(RATE)
        #     wf.writeframes(np.concatenate(wave_data).tobytes())
        time.sleep(PACKET_TIMEOUT*2.0)
    

    def __exit__(self):
        self.close()
    
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
