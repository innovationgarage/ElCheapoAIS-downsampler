from __future__ import print_function
import ais.stream
import ais
import ais.compatibility.gpsd
import datetime
import json
import sys

class NmeaMessage(object):
    def __init__(self, msg, source="unknown"):
        self.json = json.loads(msg)
        #self.keys = msg.keys()
        self.source = source
        self.raw = self.json["nmea"]
        self.tagblock = {}
    
        self.generate_tagblock_timestamp()
        self.generate_tagblock_source()

        if self.raw.startswith("\\"):
            self.fullmessage = self.raw
        else:
            self.add_tagblock()
        
    def add_tagblock(self):
        tagblock_values = [(k, v) for k, v in self.tagblock.items()]
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
        if "tagblock_timestamp" in self.json:
            self.tagblock["c"] = datetime.datetime.strptime(self.json["tagblock_timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%s")
        else:
            if 'timestamp' in self.json:
                timestamp = self.json['timestamp']
                try:
                    t = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    try:
                        t = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        pass
            else:
                t = datetime.datetime.utcnow()
            self.tagblock['c'] = t.strftime("%s")
            self.json['tagblock_timestamp'] = t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
    def generate_tagblock_source(self):
        if "tagblock_station" in self.json:
            self.tagblock['s'] = self.json["tagblock_station"]
        else:
            self.json["tagblock_station"] = self.tagblock['s'] = self.source
