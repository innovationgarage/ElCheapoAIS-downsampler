"""
run me with twistd -n -y aisserver.py, and then connect with multiple (-n is for --nodaemon)
telnet clients to port 1025
"""
from __future__ import print_function
from twisted.protocols import basic
import ais.stream
import ais
import ais.compatibility.gpsd
import datetime
import json
import sys

class nmeaMessage(object):
    def __init__(self, raw, source="unknown"):
        self.source = source
        self.raw = raw
        self.tagblock = {}
        self.parse(self.raw)
        if self.raw.startswith("\\"):
            self.fullmessage = self.raw
        else:
            self.generate_tagblock_timestamp()
            self.generate_tagblock_source()
            self.add_tagblock()
        self.parse(self.fullmessage)
        
    def parse(self, line):
        try:
            i = 0
            for msg in ais.stream.decode([line], keep_nmea=True):
                i += 1
                self.json = ais.compatibility.gpsd.mangle(msg)
                if hasattr(self, 'json'):
                    self.keys = self.json.keys()
        except Exception as e:
            print(e)
        
    def add_tagblock(self):
        tagblock_values = [(k, v) for k, v in self.tagblock.iteritems()]
        tagblock = ""
        for i, kv in enumerate(tagblock_values):
            if i==0:
                tagblock = "{}{}:{}".format(tagblock, tagblock_values[i][0], tagblock_values[i][1])
            else:
                tagblock = "{},{}:{}".format(tagblock, tagblock_values[i][0], tagblock_values[i][1])
        self.tb_checksum = ais.nmea.Checksum(tagblock)
        tagblock = "{}*{}".format(tagblock, self.tb_checksum)
        self.fullmessage = '\{}\{}'.format(tagblock, self.raw)

    def generate_tagblock_timestamp(self):
        if hasattr(self, "json") and 'timestamp' in self.json:
            timestamp = self.json['timestamp']
            try:
                self.tagblock['c'] = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                try:
                    self.tagblock['c'] = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    pass
        else:
            self.tagblock['c'] = datetime.datetime.utcnow().strftime("%s")
            
    def generate_tagblock_source(self):
        self.tagblock['s'] = self.source

class session(object):
    def __init__(self, settings):
        self.last_message_timestamp = {}
        self.settings = settings

    def __call__(self, messages):
        """
        - (if new MMSI) adds MMSI to the session sources
        - updates last_message_timestamp for the MMSI based on session settings
        """
        for msg in messages:
            if not hasattr(msg, 'json'):
                continue
            now = datetime.datetime.strptime(msg.json["tagblock_timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%s")
            src = msg.json['mmsi']
            if src not in self.last_message_timestamp:
                yield msg
                self.last_message_timestamp[src] = now
            else:
                seconds_from_last_message = float(now) - float(self.last_message_timestamp[src])
                if seconds_from_last_message >= 60 * (1. / self.settings['max_message_per_mmsi_per_min']):
                    yield msg
                    self.last_message_timestamp[src] = now
            
if __name__=="__main__":    
    session_settings = {
        'max_message_per_min':1000,
        'max_message_per_mmsi_per_min': 60 * float(sys.argv[3]), # 0.05,
#        'position_precision_degrees': 0.1,
    }
    
    sess = session(settings=session_settings)
    with open(sys.argv[1], "r") as inf:
        with open(sys.argv[2], "w") as outf:
            for msg in sess(nmeaMessage(line, "ME") for line in inf):
                if hasattr(msg, 'json'):
                    outf.write(msg.fullmessage)
                #            print(json.dumps(msg.json, indent=4, sort_keys=True))
    # msg.add_tagblock()
    
# class ElCheapo(basic.LineReceiver):
#     def connectionMade(self):
#         print("Got new client!")
#         self.factory.clients.append(self)
#         self.messages = []
        
#     def connectionLost(self, reason):
#         print("Lost a client!")
#         self.factory.clients.remove(self)

#     def lineReceived(self, line):
#         self.nmealine = line
#         self.nmealine = add_timestamp(self.nmealine)
#         self.messages.append(parse(self.nmealine))
#         for c in self.factory.clients:
#             c.echoMessage(len(self.messages))
#             c.echoMessage(self.messages[-1])

#     def echoMessage(self, message):
#         self.transport.write(str(message) + b'\n')
    
# from twisted.internet import protocol
# from twisted.application import service, internet

# factory = protocol.ServerFactory()
# factory.protocol = ElCheapo
# factory.clients = []

# application = service.Application("ElCheapo")
# internet.TCPServer(1025, factory).setServiceParent(application)
