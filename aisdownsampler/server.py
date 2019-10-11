import aisdownsampler.message
import aisdownsampler.downsampler
import socket_tentacles
import datetime
import threading
import queue
import json

senders = set()
station_id = None
downsampler = None

class Downsampler(threading.Thread):
    def __init__(self, **kw):
        self.queue = queue.Queue()
        self.sess = aisdownsampler.downsampler.Session(**kw)
        threading.Thread.__init__(self)
        
    def inputiter(self):
        while True:
            yield self.queue.get()

    def run(self):
        for msg in self.sess(self.inputiter()):
            if hasattr(msg, 'json'):
                for sender in senders:
                    sender.queue.put(msg.fullmessage)

class ReceiveHandler(socket_tentacles.ReceiveHandler):
    def handle(self):
        for line in self.file:
            print("Received", repr(line))
            downsampler.queue.put(aisdownsampler.message.NmeaMessage(line, station_id))            

class SendHandler(socket_tentacles.SendHandler):
    def handle(self):
        self.queue = queue.Queue()
        try:
            senders.add(self)            
            while True:
                msg = self.queue.get()
                self.file.write(msg)
                self.file.flush()
        finally:
            senders.remove(self)

    def put(self, msg):
        self.queue.put(msg)
            
    def __hash__(self):
        return id(self)

def server(config):
    global downsampler, station_id
    station_id = config["station_id"]
    downsampler = Downsampler(**config["session"])
    downsampler.start()
    socket_tentacles.run(config, {"source": ReceiveHandler, "destination": SendHandler})
