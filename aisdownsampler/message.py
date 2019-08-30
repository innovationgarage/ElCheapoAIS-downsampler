from __future__ import print_function
import ais.stream
import ais
import ais.compatibility.gpsd
import datetime
import json
import sys

class NmeaMessage(object):
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
        if hasattr(self, "json") and 'timestamp' in self.json:
            timestamp = self.json['timestamp']
            try:
                self.tagblock['c'] = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime("%s")
            except ValueError:
                try:
                    self.tagblock['c'] = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%s")
                except ValueError:
                    pass
        else:
            self.tagblock['c'] = datetime.datetime.utcnow().strftime("%s")
            
    def generate_tagblock_source(self):
        self.tagblock['s'] = self.source
