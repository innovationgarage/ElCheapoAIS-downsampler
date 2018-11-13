"""
run me with twistd -n -y aisserver.py, and then connect with multiple (-n is for --nodaemon)
telnet clients to port 1025
"""
from __future__ import print_function
from twisted.protocols import basic
import ais.stream
import ais

class MyAIS(basic.LineReceiver):
    def connectionMade(self):
        print("Got new client!")
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print("Lost a client!")
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        print("received", repr(line))
        for c in self.factory.clients:
            c.message(line)
            c.parse(line)

    def nmeaFileReceived(self, nmeamsg):
        print("received", repr(nmeamsg))
        for c in self.factory.clients:
            c.parse(nmeamsg)
            
    def message(self, message):
        self.transport.write(message + b'\n')

    def parse(self, message):
        self.transport.write(str(ais.decode(message,0)))
        
        
from twisted.internet import protocol
from twisted.application import service, internet

factory = protocol.ServerFactory()
factory.protocol = MyAIS
factory.clients = []

application = service.Application("AISserver")
internet.TCPServer(1025, factory).setServiceParent(application)
