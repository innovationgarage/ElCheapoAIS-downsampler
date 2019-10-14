import aisdownsampler.message
import aisdownsampler.downsampler
import aisdownsampler.dbus_api
import socket_tentacles
import datetime
import threading
import queue

senders = set()
station_id = None
downsampler = None
dbus_api = None
 
class Downsampler(threading.Thread):
    def __init__(self, **kw):
        self.queue = queue.Queue()
        self.sess = aisdownsampler.downsampler.Session(**kw)
        threading.Thread.__init__(self)
        
    def inputiter(self):
        while True:
            msg = self.queue.get()
            yield aisdownsampler.message.NmeaMessage(msg, station_id)

    def run(self):
        for msg in self.sess(self.inputiter()):
            if hasattr(msg, 'json'):
                for sender in senders:
                    sender.queue.put(msg.fullmessage)
                    
class ReceiveHandler(socket_tentacles.ReceiveHandler):
    def handle(self):
        for line in self.file:
            print("Received", repr(line))
            downsampler.queue.put(line)

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
    global downsampler, dbus_api, station_id
    station_id = config["station_id"]
    downsampler = Downsampler(**config["session"])
    downsampler.start()
    dbus_api = aisdownsampler.dbus_api.DBusManager(downsampler, config["dbus"])
    dbus_api.start()
    socket_tentacles.run(config, {"source": ReceiveHandler, "destination": SendHandler})
