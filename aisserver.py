"""
run me with twistd -n -y aisserver.py, and then connect with multiple (-n is for --nodaemon)
telnet clients to port 1025
"""
from __future__ import print_function
from twisted.protocols import basic
import ais.stream
import ais
import datetime

def parse(line):
    try:
        return next(ais.stream.decode([line]))
    except:
        pass

def add_timestamp(message):
    timestamp = datetime.datetime.utcnow().strftime("%s")
    tagblock = "\c:{}".format(timestamp)
    checksum = ais.nmea.Checksum(tagblock)
    tagblock = "{}*{}".format(tagblock, checksum)
    message = "{}\{}".format(tagblock, message)
    return message
    
class MyAIS(basic.LineReceiver):
    def connectionMade(self):
        print("Got new client!")
        self.factory.clients.append(self)
        self.messages = []
        
    def connectionLost(self, reason):
        print("Lost a client!")
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        self.nmealine = line
        self.nmealine = add_timestamp(self.nmealine)
        self.messages.append(parse(self.nmealine))
        for c in self.factory.clients:
            c.echoMessage(len(self.messages))
            c.echoMessage(self.messages[-1])
            
    def echoMessage(self, message):
        self.transport.write(str(message) + b'\n')

    
from twisted.internet import protocol
from twisted.application import service, internet

factory = protocol.ServerFactory()
factory.protocol = MyAIS
factory.clients = []

application = service.Application("AISserver")
internet.TCPServer(1025, factory).setServiceParent(application)
