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

class nmeaMessage(object):
    def __init__(self, raw):
        self.raw = raw
        self.tagblock = {}
        self.parse(self.raw)
        if hasattr(self, 'json'):
            self.generate_tagblock_timestamp()
            self.generate_tagblock_source()
            self.add_tagblock()
        else:
            self.fullmessage = self.raw
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

class session(object):
    def __init__(self, settings):
        self.sources = []
        self.messages = []
        self.last_message_timestamp = {}
        self.settings = settings
        
    def add_source(self, src):
        """
        src: source identifier of the AIS message - MMSI
        """
        if src not in self.sources:
            self.sources.append(src)

    def drop_source(self, src):
        if src in self.sources:
            self.sources.remove(src)

    def add_message(self, msg):
        """
        - (if new MMSI) adds MMSI to the session sources
        - updates last_message_timestamp for the MMSI based on session settings
        """
        try:
            now = datetime.datetime.utcnow().strftime("%s")
            src = msg.json['mmsi']
            if src not in self.sources:
                self.add_source(src)
                self.messages.append(msg)
                self.last_message_timestamp[src] = now
            else:
                seconds_from_last_message = float(now) - float(self.last_message_timestamp[src])
                if seconds_from_last_message >= self.settings['max_message_per_mmsi_per_min']/60.:
                    self.messages.append(msg)
                    self.last_message_timestamp[src] = now
        except Exception as e:
            pass
            
if __name__=="__main__":    
    session_settings = {
        'max_message_per_min':1000,
        'max_message_per_mmsi_per_min': 0.05,
#        'position_precision_degrees': 0.1,
    }
    
    sess = session(settings=session_settings)
    with open("nmea-sample", "r") as inf:
        with open("nmea.out", "w") as outf:
            for line in inf:
                msg = nmeaMessage(line)
                sess.add_message(msg)
                if hasattr(msg, 'json'):
                    json.dump(msg.json['mmsi'], outf)
                    outf.write("\n")
                #            print(json.dumps(msg.json, indent=4, sort_keys=True))
    print(len(sess.messages))
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
