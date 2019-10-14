from __future__ import print_function
import datetime

class Session(object):
    def __init__(self, max_message_per_sec=None, max_message_per_mmsi_per_sec=1):
        self.last_message_timestamp = None
        self.last_message_per_mmsi_timestamp = {}
        self.max_message_per_sec = max_message_per_sec
        self.max_message_per_mmsi_per_sec = max_message_per_mmsi_per_sec

    def __call__(self, messages):
        """
        - (if new MMSI) adds MMSI to the session sources
        - updates last_message_per_mmsi_timestamp for the MMSI based on session settings
        """
        for msg in messages:
            if msg is None:
                yield msg
                
            if not hasattr(msg, 'json'):
                continue

            now = msg.tagblock["c"]
            src = msg.json['mmsi']
            
            if self.max_message_per_sec is not None and self.last_message_timestamp is not None:
                seconds_from_last_message = float(now) - float(self.last_message_timestamp)
                if seconds_from_last_message < 1. / self.max_message_per_sec:
                    continue

            if self.max_message_per_mmsi_per_sec is not None and src in self.last_message_per_mmsi_timestamp:
                seconds_from_last_message = float(now) - float(self.last_message_per_mmsi_timestamp[src])
                if seconds_from_last_message < 1. / self.max_message_per_mmsi_per_sec:
                    continue
                    
            yield msg
            self.last_message_timestamp = now
            self.last_message_per_mmsi_timestamp[src] = now
