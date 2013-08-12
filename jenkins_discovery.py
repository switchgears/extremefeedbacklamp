#!/usr/bin/env python  
      
# Jenkins server UDP based discovery
# Based on original work by Gordon McGregor gordon.mcgregor@verilab.com
#
# Author Aske Olsson aske.olsson@switch-gears.dk
  
from twisted.internet.protocol import DatagramProtocol  
from twisted.internet import reactor  
from twisted.application.internet import MulticastServer  
from twisted.internet import task  
import xml.etree.ElementTree as ET

MULTICAST_ADDR = "239.77.124.213"
UDP_PORT = 33848
DELAY = 60
  
class JenkinsDiscovery(DatagramProtocol):  
 def __init__(self):  
  self.instances = {}
  self.ping_str = 'Hello Jenkins, Where are you'
 def startProtocol(self):  
#  print 'Host discovery: listening'  
  self.transport.joinGroup(MULTICAST_ADDR)  
   
 def refreshList(self):  
#  print 'Refreshing list...'  
  self.instances = {}  
  self.ping()  
   
 def ping(self):  
  self.transport.write(self.ping_str, (MULTICAST_ADDR, UDP_PORT))  
  
 def datagramReceived(self, datagram, address):  
#  print datagram
  try:
    xml = str.lower(datagram)
    root = ET.fromstring(xml)
    # Check if we received a datagram from another Jenkins/Hudson instance  
    if root.tag == 'hudson' or root.tag == 'jenkins':
      for url in root.findall('url'):
#        print "Jenkins url:", url.text
        if not url.text in self.instances:
          self.instances[url.text] = address[0]
#        print "Jenkins IP:", address[0]
    print "Found instances:"
    for k,v in self.instances.iteritems():
      print "%s Running @ %s" %(k,v)
  except: 
    # Twisted and xml parser seems to through some Unhandled error
    pass    


if __name__ == '__main__':
  discovery = JenkinsDiscovery()  
  reactor.listenMulticast(UDP_PORT, discovery)  
  refresh = task.LoopingCall(discovery.refreshList)  
  refresh.start(DELAY) 
  reactor.run()  

