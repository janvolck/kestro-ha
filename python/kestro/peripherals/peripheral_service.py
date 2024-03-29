import time

from threading import Thread
from .network import Network
from .display import display
from .gpio import gpio
from .sensors import power_sensor, temperature_sensor, humidity_sensor, distance_sensor


class PeripheralService:
    """Initialises the configured peripherals and provides a
    central place to access and manipulate the initialised peripherals"""

    def __init__(self):
        self.network = Network()
        self.ip_info_index = 0
        self.ip_info_last_changed = 0.0
        self._aborted = display is None
        self._worker = Thread(target=self._do_work)

    def abort(self):
        self._aborted = True

    def display(self):
        return display

    def distance_sensor(self):
        return distance_sensor

    def gpio(self):
        return gpio

    def humidity_sensor(self):
        return humidity_sensor

    def power_sensor(self):
        return power_sensor

    def temperature_sensor(self):
        return temperature_sensor

    def start(self):
        if not self._aborted:
            self._worker.start()

    def _do_work(self):
        import time

        while not self._aborted:
            self._update()
            time.sleep(1)

    def _update(self):
        try:
            self.network.refresh()

            addr = "No Connection"
            if len(self.network.addresses) > 1:
                if time.time() - self.ip_info_last_changed > 5.0:
                    self.ip_info_last_changed = time.time()
                    self.ip_info_index += 1

                    if self.ip_info_index >= len(self.network.addresses):
                        self.ip_info_index = 0

                iface = list(self.network.addresses)[self.ip_info_index]
                addr = "%s: %s" % (iface, self.network.addresses[iface])

            elif len(self.network.addresses) == 1:
                addr = self.network.address

            display.update_property("ip_addr", addr)

            if distance_sensor:
                distance_sensor.refresh()
                display.update_property("distance", distance_sensor.distance)

            if humidity_sensor:
                humidity_sensor.refresh()
                display.update_property("humidity", humidity_sensor.humidity)

            if power_sensor:
                power_sensor.refresh()
                display.update_property("voltage", power_sensor.voltage)
                display.update_property("current", power_sensor.current)

            if temperature_sensor:
                temperature_sensor.refresh()
                display.update_property("temperature", temperature_sensor.temperature)

            display.refresh()
        except RuntimeError:
            pass
        except Exception:
            pass
