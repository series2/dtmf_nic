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


from scapy.all import Ether, IP, ICMP,ARP, raw
class DEBUG_ICMP():
    def __init__(self):
        self.num=0
        self.MY_IP = "192.168.111.13"
        self.MY_MAC = "00:11:22:33:44:55"
        self.send_buffer=[]

    def read(self,n):
        if self.num>0:
            if len(self.send_buffer)>0:
                pkt=self.send_buffer.pop(0)
                print(pkt.summary())
                print(pkt.show())
                print(pkt)
                return raw(pkt)
            else:
                return b""
        self.num+=1
        dst_ip=input("> ").strip() # 192.168.111.15
        if dst_ip=="":
            return b""
        pkt = Ether(src=self.MY_MAC) / IP(dst=dst_ip, src=self.MY_IP) / ICMP(type="echo-request")
        data = raw(pkt)
        print(pkt.summary())
        print(pkt.show())
        print(pkt)
        return data
    def write(self,data):
        if len(data)==0:
            return
        try:
            pkt = Ether(data)
        except:
            print("Invalid Packet")
            return
        print(pkt.summary())
        print(pkt.show())
        print(pkt)
        if pkt.haslayer(ARP):
            arp = pkt[ARP]
            # 自分宛てのARPリクエストか確認
            if arp.op == 1 and arp.pdst == self.MY_IP:  # op=1はARPリクエスト
                # ARPリプライを作成
                arp_reply = Ether(dst=pkt.src, src=self.MY_MAC) / ARP(
                    op=2,              # ARPリプライ
                    hwsrc=self.MY_MAC,      # 自分のMAC
                    psrc=self.MY_IP,        # 自分のIP
                    hwdst=arp.hwsrc,   # 問い合わせ元のMAC
                    pdst=arp.psrc      # 問い合わせ元のIP
                )
                # パケットをバッファへ
                self.send_buffer.append(arp_reply)
        if pkt.haslayer(IP) and pkt.haslayer(ICMP):
            ip = pkt[IP]
            icmp = pkt[ICMP]
            # ICMP Echo Request (type=8)
            if icmp.type == 8 and ip.dst == self.MY_IP:
                icmp_reply = Ether(dst=pkt.src, src=self.MY_MAC) / IP(
                    src=self.MY_IP, dst=ip.src
                ) / ICMP(
                    type=0,  # Echo Reply
                    id=icmp.id,
                    seq=icmp.seq
                ) / icmp.payload  # ペイロードをそのまま返す
                self.send_buffer.append(icmp_reply)

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
            print(data.hex())
            pkt = Ether(data)
            print(pkt.summary())
            print(pkt.show())
            print(pkt)

            if ICMP not in pkt and ARP not in pkt:
                return None # OS ga yokei na packet wo irete kuru node filter suru.
            
            return data
        except BlockingIOError:
            return None
        except Exception:
            return None
        return None
    def write(self,data):
        pkt = Ether(data)
        print(pkt.summary())
        print(pkt.show())
        print(pkt)
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
    mode="ICMP"
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