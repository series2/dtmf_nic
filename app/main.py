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


from scapy.all import Ether, IP, ICMP,ARP , raw
class DEBUG_ICMP():
    # def __init__(self):

    def read(self,n):
        src_ip=input("> ").strip()
        if src_ip=="":
            return b""
        pkt = Ether() / IP(src=src_ip, dst="192.168.111.13") / ICMP(type="echo-reply")
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
        flags = fcntl.fcntl(self.fd,fcntl.F_GETFL)
        fcntl.fcntl(self.fd,fcntl.F_SETFL,flags|os.O_NONBLOCK)
    def read(self,n):
        try:
            data=os.read(self.fd,n)
            pkt = Ether(data)
            
            if ICMP not in pkt and ARP not in pkt:
                print("send rejected :",pkt.summary())
                return None # OS ga yokei na packet wo irete kuru node filter suru.
            print("sending data : ",pkt.summary())
            print("sending raw data : ",data.hex())
            print("sending formatted data : ")
            pkt.show()
            return data
        except BlockingIOError:
            return None
        except Exception:
            return None
        return None
    def write(self,data):
        pkt = Ether(data)
        print("recieving data : ",pkt.summary())
        print("recieving formatted data : ")
        pkt.show()
        os.write(self.fd,data)

"""
Before running this script, set up the TAP device with:
sudo ip tuntap add dev mynic mode tap user $USER
sudo ip link set mynic up
sudo ip addr add 192.168.111.15/24 dev mynic
# option filtering...
sudo iptables -A INPUT -i mynic -j DROP
sudo iptables -A OUTPUT -o mynic -j DROP
sudo iptables -A INPUT -i mynic -p icmp -j ACCEPT
sudo iptables -A OUTPUT -o mynic -p icmp -j ACCEPT


end ...
sudo ip link set dev mynic down
sudo ip tuntap del dev mynic mode tap
# option
... iptables ha saikidou de kieru.
"""
if __name__ == "__main__":
    # mode="DEBUG"
    # mode="TEXT"
    # mode="FILE"
    # mode="ICMP"
    mode="TAP"
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