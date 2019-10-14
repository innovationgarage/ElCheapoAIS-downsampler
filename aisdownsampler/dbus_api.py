import dbus
import dbus.service
import dbus.mainloop.glib
import gi.repository.GLib
import threading
import queue

def get(bus, bus_name, obj_path, interface_name, parameter_name, default=None):
    try:
        return bus.get_object(bus_name, obj_path).Get(interface_name, parameter_name)
    except:
        return default

class DBusManager(threading.Thread):
    def __init__(self, downsampler, bus="SystemBus"):
        self.downsampler = downsampler
        self.bus_name = bus
        threading.Thread.__init__(self)

    def NMEA(self, msg):
        self.downsampler.queue.put(msg)

    def PropertiesChanged(self, interface_name, properties_modified, properties_deleted, dbus_message):
        if interface_name == "no.innovationgarage.elcheapoais.downsampler":
            for key, value in properties_modified.items():
                if key == "max_message_per_sec":
                    print("Setting %s=%s" % (key, value))
                    self.downsampler.max_message_per_sec = value
                elif key == "max_message_per_mmsi_per_sec":
                    print("Setting %s=%s" % (key, value))
                    self.downsampler.max_message_per_mmsi_per_sec = value
        elif interface_name == "no.innovationgarage.elcheapoais.receiver":    
            for key, value in properties_modified.items():
                if key == "station_id":
                    print("Setting %s=%s" % (key, value))
                    self.downsampler.station_id = value
                
    def run(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = getattr(dbus, self.bus_name)()
        self.name = dbus.service.BusName('no.innovationgarage.elcheapoais.downsampler', self.bus)

        self.downsampler.sess.max_message_per_sec = get(
            self.bus, 'no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/downsampler',
            "no.innovationgarage.elcheapoais.downsampler", "max_message_per_sec", 0.01)
        
        self.downsampler.max_message_per_mmsi_per_sec = get(
            self.bus, 'no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/downsampler',
            "no.innovationgarage.elcheapoais.downsampler", "max_message_per_mmsi_per_sec", 0.01)

        self.downsampler.station_id = get(
            self.bus, 'no.innovationgarage.elcheapoais.config', '/no/innovationgarage/elcheapoais/receiver',
            "no.innovationgarage.elcheapoais.receiver", "station_id", None)

        self.bus.add_signal_receiver(self.PropertiesChanged,
                                     dbus_interface = "org.freedesktop.DBus.Properties",
                                     signal_name = "PropertiesChanged",
                                     message_keyword='dbus_message')

        self.bus.add_signal_receiver(self.NMEA, signal_name="NMEA", dbus_interface = "no.innovationgarage.elcheapoais")

        loop = gi.repository.GLib.MainLoop()
        loop.run()

