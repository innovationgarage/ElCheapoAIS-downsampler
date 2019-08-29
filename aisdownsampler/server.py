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
import twisted.internet.task
import datetime

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
        self.factory.server.last_input = datetime.datetime.now()
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
        if self.factory.server.notifier:
            with open(self.factory.server.notifier, "w") as f:
                f.write("geocloud=1\n")

    def connectionLost(self, reason):
        print("Lost a client!")
        self.factory.server.destination = None
        if self.factory.server.notifier:
            with open(self.factory.server.notifier, "w") as f:
                f.write("geocloud=0\n")

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
            print("Sending", line.fullmessage)
            self.sendLine(line.fullmessage)

    def lineReceived(self, line):
        print("WARNING: Destination received", repr(line))

class Server(object):
    def __init__(self, notifier = None):
        self.source = None
        self.destination = None
        self.notifier = notifier
        self.last_input = None
        self.input_status = False
        
        self.heartbeat_task = twisted.internet.task.LoopingCall(self.heartbeat)
        self.heartbeat_task.start(1.0)

    def heartbeat(self):
        input_status = self.last_input is not None and datetime.datetime.now() - self.last_input < datetime.timedelta(seconds = 1)
        if input_status != self.input_status:
            self.input_status = input_status
            if self.notifier:
                with open(self.notifier, "w") as f:
                    f.write("nmea=%s\n" % ([0,1][self.input_status],))
        
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

def build_server(source, destination, session, station_id, notifier):
    server = Server(notifier = notifier)
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
