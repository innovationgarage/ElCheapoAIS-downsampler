"""
run me with twistd -n -y aisserver.py, and then connect with multiple (-n is for --nodaemon)
telnet clients to port 1025
"""
from __future__ import print_function
from twisted.protocols import basic
from twisted.internet import protocol
from twisted.application import service, internet
import aisdownsampler.message
import aisdownsampler.downsampler
import twisted.application.app
import twisted.internet.reactor
import twisted.application.strports

class Source(basic.LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        print("Got new source client!")
        self.factory.server.source = self

    def connectionLost(self, reason):
        print("Lost a source client!")
        self.factory.server.source = None

    def lineReceived(self, line):
        print("Received", repr(line))
        if self.factory.server.destination is None: return        
        self.factory.server.destination.handleLine(line)

class Destination(basic.LineReceiver):
    delimiter = '\n'

    def __init__(self, session, station_id):
        self.session = session
        self.station_id = station_id
        self.lines = []
        self.output = iter(self.session(self.input()))
        
    def connectionMade(self):
        print("Got new destination client!")
        self.factory.server.destination = self

    def connectionLost(self, reason):
        print("Lost a client!")
        self.factory.server.destination = None

    def input(self):
        while True:
            if self.lines:
                line = self.lines[0]
                self.lines = self.lines[1:]
                yield aisdownsampler.message.NmeaMessage(line, self.station_id)
            else:
                yield None
        
    def handleLine(self, line):
        self.lines.append(line)
        for line in self.output:
            if line is None:
                return
            self.sendLine(line.fullmessage)

    def lineReceived(self, line):
        print("WARNING: Destination received", repr(line))

class Server(object):
    def __init__(self):
        self.source = None
        self.destination = None
    
class SourceFactory(protocol.ServerFactory):
    protocol = Source
    def __init__(self, server):
        self.server = server
class DestinationFactory(protocol.ServerFactory):
    def __init__(self, server, session, station_id):
        self.server = server
        self.session = session
        self.station_id = station_id
    def buildProtocol(self, addr):
        res = Destination(self.session, self.station_id)
        res.factory = self
        return res

def build_server(source, destination, session, station_id):
    server = Server()
    factories = {"source": SourceFactory(server),
                 "destination": DestinationFactory(server, session, station_id)}
    config = {"source": source, "destination": destination}
    
    application = service.Application("aisdownsampler")
    for direction, conn in config.iteritems():
        factory = factories[direction]
        if conn["type"] == "connect":
            twisted.application.internet.ClientService(
                twisted.internet.endpoints.clientFromString(
                    twisted.internet.reactor, str(conn["connect"])
                ), factory).setServiceParent(application)
        elif conn["type"] == "listen":
            twisted.application.strports.service(
                str(conn["listen"]), factory
            ).setServiceParent(application)
            
    return application
          
def server(*arg, **kw):
    application = build_server(*arg, **kw)

    twisted.application.app.startApplication(application, 0)
    twisted.internet.reactor.run()
