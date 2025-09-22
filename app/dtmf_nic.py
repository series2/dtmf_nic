import app
from app.decode import DTMFDecoder
from app.encode import DTMFEncoder
from app.util import MAX_FRAME_SIZE
import pyaudio


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
                format=pyaudio.paInt16,
                channels=1,
                rate=app.encode.RATE,
                output=True)
        )
        self.decoder=DTMFDecoder(self.decoder_stream)
    def main(self):
        while True:
            # 受信があればブロッキング、ない場合即時読み取りへ
            print("*"*30)
            print("Recieving...")
            recv_packet = self.decoder.recv()
            if len(recv_packet)!=0:
                print("Receiving end! and Writing ...")
                self.io.write(recv_packet)
                print("Wrinting end!")
            else:
                print("No Recv")
            
            print("="*30)
            print("Read File...")
            send_packet = self.io.read(MAX_FRAME_SIZE)
            print("Reading End!")
            if send_packet:
                print("Sending ...")
                # 誰も送信していないとみなす
                self.decoder_stream.stop_stream()
                self.encoder.send(send_packet)
                print("Sending End!")
                # 送信中はプロセスはブロックされ、受信されない
                self.decoder_stream.start_stream()
            else:
                print("No Send")
