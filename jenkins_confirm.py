#!/usr/bin/env python

import SocketServer

def getmac(interface):
  # Return the MAC address of interface
  try:
    str = open('/sys/class/net/%s/address' % interface).readline()
  except:
    str = "00:00:00:00:00:00"
  return str[0:17]

mac = getmac("eth0")

class MyTCPHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        self.data = self.rfile.readline().strip()
        if "SG-PING" in self.data:
        	self.wfile.write(mac)
        else:
        	self.wfile.write("I'm afraid I can't let you do that, Dave\n")

if __name__ == "__main__":
    HOST, PORT = "", 19417
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()
