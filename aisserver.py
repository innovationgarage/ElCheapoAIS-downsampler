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
import sys
import json

class nmeaMessage(object):
    def __init__(self, raw):
        self.raw = raw
        self.json = {}
        self.tagblock = {}
        self.parse(self.raw)
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
        if 'timestamp' in self.json:
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
        if 'mmsi' in self.json:
            self.tagblock['s'] = self.json['mmsi']
    
if __name__=="__main__":    
#    line = sys.argv[1]
    with open("nmea-sample", "r") as inf:
        with open("nmea.out", "w") as outf:
#            line = "!AIVDM,1,1,,B,K5DfMB9FLsM?P00d,0*70"
            for line in inf:
#                print(line)
                msg = nmeaMessage(line)
                json.dump(msg.json, outf)
                outf.write("\n")
                #            print(json.dumps(msg.json, indent=4, sort_keys=True))
                print(msg.fullmessage)
    
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
