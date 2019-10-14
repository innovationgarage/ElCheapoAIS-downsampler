import dbus
import dbus.service
import dbus.mainloop.glib
import gi.repository.GLib
import threading
import queue

class DBusManager(threading.Thread):
    def __init__(self, downsampler, bus="SystemBus"):
        self.downsampler = downsampler
        self.bus_name = bus
        threading.Thread.__init__(self)

    def NMEA(self, msg):
        self.downsampler.queue.put(msg)
        
    def run(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = getattr(dbus, self.bus_name)()
        self.name = dbus.service.BusName('no.innovationgarage.elcheapoais.downsampler', self.bus)
        
        self.bus.add_signal_receiver(self.NMEA, signal_name="NMEA", dbus_interface = "no.innovationgarage.elcheapoais")

        loop = gi.repository.GLib.MainLoop()
        loop.run()

