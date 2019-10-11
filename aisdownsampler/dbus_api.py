import dbus
import dbus.service
import dbus.mainloop.glib
import gi.repository.GLib
import threading
import queue
import json

        
class StatusObject(dbus.service.Object):
    def __init__(self, manager, object_path='/no/innovationgarage/elcheapoais/downsampler/status'):
        dbus.service.Object.__init__(self, manager.bus, object_path)
        self.manager = manager
        self.nmea_queue = queue.Queue()
        gi.repository.GLib.timeout_add(100, self.send_nmea)

    def send_nmea(self):
        while not self.nmea_queue.empty():
            msg = self.nmea_queue.get(False)
            self.NMEA(json.dumps(msg))
        return True
        
    @dbus.service.signal('no.innovationgarage.elcheapoais')
    def NMEA(self, message):
        pass
        #print("Sending %s" % message)

class DBusManager(threading.Thread):
    def __init__(self, bus="SystemBus"):
        self.bus_name = bus
        threading.Thread.__init__(self)
        
    def run(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = getattr(dbus, self.bus_name)()
        self.name = dbus.service.BusName('no.innovationgarage.elcheapoais.downsampler', self.bus)
        self.status = StatusObject(self)
        
        loop = gi.repository.GLib.MainLoop()
        loop.run()
