#!/usr/bin/env python  
#
# Author Aske Olsson aske.olsson@switch-gears.dk
#
import socket
import struct

#MCAST_GRP = '224.1.1.1'
#MCAST_PORT = 5007
MCAST_ADDR = "239.77.124.213"
MCAST_RECV_PORT = 19419
MCAST_PORT = 19418

recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.bind(('', MCAST_RECV_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_ADDR), socket.INADDR_ANY)

recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
send_sock.sendto("Hello", (MCAST_ADDR, MCAST_PORT))
recv_sock.settimeout(2)

try:
	while True:
		data, sender_addr = recv_sock.recvfrom(1024)
		print data, 
		print "IP:", sender_addr[0]
except socket.timeout:
	pass

recv_sock.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP, socket.inet_aton(MCAST_ADDR) + socket.inet_aton('0.0.0.0'))
recv_sock.close()
