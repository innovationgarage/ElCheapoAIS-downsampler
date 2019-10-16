import aisdownsampler.message
import aisdownsampler.downsampler
import aisdownsampler.dbus_api
import socket_tentacles
import datetime
import threading
import queue

class Downsampler(threading.Thread):
    def __init__(self, manager, station_id=None, **kw):
        self.manager = manager
        self.queue = queue.Queue()
        self.station_id = station_id
        self.sess = aisdownsampler.downsampler.Session(**kw)
        threading.Thread.__init__(self)
        
    def inputiter(self):
        while True:
            msg = self.queue.get()
            yield aisdownsampler.message.NmeaMessage(msg, self.station_id or "unknown")

    def run(self):
        for msg in self.sess(self.inputiter()):
            if hasattr(msg, 'json'):
                for sender in self.manager.senders:
                    sender.queue.put(msg.fullmessage)
                    
class ReceiveHandler(socket_tentacles.ReceiveHandler):
    def handle(self):
        for line in self.file:
            print("Received", repr(line))
            self.server.manager.downsampler.queue.put(line)

class SendHandler(socket_tentacles.SendHandler):
    def handle(self):
        self.queue = queue.Queue()
        try:
            self.server.manager.senders.add(self)            
            while True:
                msg = self.queue.get()
                self.file.write(msg)
                self.file.flush()
        finally:
            self.server.manager.senders.remove(self)

    def put(self, msg):
        self.queue.put(msg)
            
    def __hash__(self):
        return id(self)

class Server(object):
    def __init__(self):
        self.senders = set()
        self.downsampler = Downsampler(self)
        self.server = socket_tentacles.Server({"source": ReceiveHandler, "destination": SendHandler})
        self.server.manager = self
        self.dbus_api = aisdownsampler.dbus_api.DBusManager(self)

        self.downsampler.start()
        self.dbus_api.start()

def server():
    return Server()

