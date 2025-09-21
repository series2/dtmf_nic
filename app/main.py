import fcntl
import os
import struct
from app.dtmf_nic import DTMF_NIC

class DEBUG_TEXT_IO():
    def read(self,n):
        text=input(" send > ")
        return bytes(text,"utf-8")
    def write(self,data):
        print(data.decode("utf-8","ignore"))

class DEBUG_IO():
    def read(self,n):
        text=input(" send (only [0-0|a-f]) > ")
        if len(text)%2!=0:
            text=text+"0"
        return bytes.fromhex(text)
    def write(self,data):
        print(data.hex())


from scapy.all import Ether, IP, ICMP, raw
class DEBUG_ICMP():
    # def __init__(self):

    def read(self,n):
        src_ip=input("> ").strip()
        if src_ip=="":
            return b""
        pkt = Ether() / IP(src=src_ip, dst="0.0.0.0") / ICMP(type="echo-reply")
        data = raw(pkt)
        return data
    def write(self,data):
        pkt = Ether(data)
        print(pkt.summary())
        print(pkt.show())
        print(pkt)

class DEBUG_TEXT_FILE_IO():
    def __init__(self):
        self.fd = os.open("./tmp", os.O_RDWR)
    def read(self,n):
        # システムコールによって書き込まれた送信命令を読む
        # echo "Hello" >> tmp
        return os.read(self.fd,n)
    def write(self,data):
        # 受信したパケットを書き込む
        # os.write(self.fd,data)
        print(data.decode("utf-8","ignore"))

class TAP_IO():
    def __init__(self):
        TUNSETIFF = 0x400454ca
        IFF_TAP   = 0x0002
        IFF_NO_PI = 0x1000
        self.fd = os.open("/dev/net/tun", os.O_RDWR)
        ifr = struct.pack("16sH", b"mynic", IFF_TAP | IFF_NO_PI)
        fcntl.ioctl(self.fd, TUNSETIFF, ifr)
    def read(self,n):
        return os.read(self.fd,n)
    def write(self,data):
        os.write(self.fd,data)

"""
Before running this script, set up the TAP device with:
sudo ip tuntap add dev mynic mode tap user $USER
sudo ip link set mynic up
sudo ip addr add 192.168.10.1/24 dev mynic
"""
if __name__ == "__main__":
    # mode="DEBUG"
    mode="TEXT"
    # mode="FILE"
    # mode="ICMP"
    # mode="TAP"
    if mode=="DEBUG":
        DTMF_NIC(DEBUG_IO()).main()
        exit(0)
    elif mode=="TEXT":
        DTMF_NIC(DEBUG_TEXT_IO()).main()
        exit(0)
    elif mode=="FILE":
        DTMF_NIC(DEBUG_TEXT_FILE_IO()).main()
        exit(0)
    elif mode=="ICMP":
        DTMF_NIC(DEBUG_ICMP()).main()
        exit(0)
    # TAP デバイスを開く
    DTMF_NIC(TAP_IO()).main()