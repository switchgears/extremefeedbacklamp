#!/usr/bin/env python  
#
# Author Aske Olsson aske.olsson@switch-gears.dk
#
import socket
import struct

#MCAST_GRP = '224.1.1.1'
#MCAST_PORT = 5007
MCAST_ADDR = "239.77.124.213"
MCAST_PORT = 19418
MCAST_ANS_PORT = 19419

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_ADDR), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

#ip = socket.gethostbyname(socket.gethostname())
myMAC = open('/sys/class/net/eth0/address').read()

while True:
    try:
        data, sender_addr = sock.recvfrom(1024)
#        print data, sender_addr
#        Answer back
        ans_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ans_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        ans_sock.sendto("MAC=" + myMAC, (sender_addr[0], MCAST_ANS_PORT))
    except Exception:
        pass

