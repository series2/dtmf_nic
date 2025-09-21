import os
import app
from app.decode import DTMFDecoder
from app.encode import DTMFEncoder
from app.util import MAX_FRAME_SIZE
import pyaudio
import os, fcntl, struct


# めんどくさいので半二重で実装する
class DTMF_NIC():
    def __init__(self,io):
        self.io=io
        p = pyaudio.PyAudio()
        self.decoder_stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=app.decode.RATE,
                        input=True,
                        frames_per_buffer=app.decode.CHUNK)
        self.encoder=DTMFEncoder(
            p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=app.encode.RATE,
                output=True)
        )
        self.decoder=DTMFDecoder(self.decoder_stream)
    def main(self):
        while True:
            # 受信があればブロッキング、ない場合即時読み取りへ
            recv_packet = self.decoder.recv()
            if recv_packet is not None:
                print("RECV")
                self.io.write(recv_packet)
            else:
                print("No Recv")
            
            send_packet = self.io.read(MAX_FRAME_SIZE)
            if send_packet:
                print("SEND")
                # 誰も送信していないとみなす
                self.decoder_stream.stop_stream()
                self.encoder.send(send_packet)
                # 送信中はプロセスはブロックされ、受信されない
                self.decoder_stream.start_stream()
            else:
                print("No Send")
