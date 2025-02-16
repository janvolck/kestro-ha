import time
import asyncio

from configparser import ConfigParser
from threading import Thread
from .network import Network
from .display.proxy_display import ProxyDisplay
from .gpio.proxy_gpio import ProxyGpio
from .sensors import power_sensor, temperature_sensor, humidity_sensor, distance_sensor


class PeripheralService:
    """Initialises the configured peripherals and provides a
    central place to access and manipulate the initialised peripherals"""

    def __init__(self):
        self._properties: dict[str, any] = {}
        self._tasks = []

        self._network = Network()
        self._ip_info_index = 0
        self._ip_info_last_changed = 0.0

        self._gpio = ProxyGpio()
        self._displays = ProxyDisplay()

        self._aborted = False
        self._worker = Thread(target=self._do_work)

    def load_config(self, config_path: str):
        config = ConfigParser()
        config.read(config_path)
        self._gpio.load_config(config)
        self._displays.load_config(config)

    async def abort(self):
        self._aborted = True

    def update_property(self, key: str, value: any):
        self._properties[key] = value

    def display(self):
        return self._displays

    def distance_sensor(self):
        return distance_sensor

    def gpio(self):
        return self._gpio

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
        loop = asyncio.new_event_loop()
        self._tasks.append(loop.create_task(self._refresh_network()))
        self._tasks.append(loop.create_task(self._refresh_gpio()))
        self._tasks.append(loop.create_task(self._refresh()))
        self._tasks.append(loop.create_task(self._refresh_display()))
        loop.run_until_complete(asyncio.wait(self._tasks))
        loop.close

    async def _refresh_network(self):
        while not self._aborted:
            await self._network.refresh()

            addr = "No Connection"
            if len(self._network._addresses) > 1:
                if time.time() - self._ip_info_last_changed > 5.0:
                    self._ip_info_last_changed = time.time()
                    self._ip_info_index += 1

                    if self._ip_info_index >= len(self._network._addresses):
                        self._ip_info_index = 0

            elif len(self._network._addresses) == 1:
                self._ip_info_index = 0
            else:
                self._ip_info_index = -1

            if self._ip_info_index < 0:
                self.update_property("ip_addr", None)
            else:
                iface = list(self._network._addresses)[self._ip_info_index]
                addr = "%s: %s" % (iface, self._network._addresses[iface])
                self.update_property("ip_addr", addr)

            await asyncio.sleep(5.0)

    async def _refresh_gpio(self):
        while not self._aborted:
            await self._gpio.refresh()
            for input, value in self._gpio.inputs:
                self.update_property(input, value)

            for output, value in self._gpio.outputs:
                self.update_property(output, value)

            await asyncio.sleep(0.1)

    async def _refresh_display(self):
        while not self._aborted:
            await self._displays.refresh(self._properties)
            await asyncio.sleep(0.1)

    async def _refresh(self):
        while not self._aborted:
            try:
                if distance_sensor:
                    await distance_sensor.refresh()
                    self.update_property("distance", distance_sensor.distance)

                if humidity_sensor:
                    await humidity_sensor.refresh()
                    self.update_property("humidity", humidity_sensor.humidity)

                if power_sensor:
                    await power_sensor.refresh()
                    self.update_property("voltage", power_sensor.voltage)
                    self.update_property("current", power_sensor.current)

                if temperature_sensor:
                    await temperature_sensor.refresh()
                    self.update_property("temperature", temperature_sensor.temperature)

            except RuntimeError:
                pass
            except Exception:
                pass

            await asyncio.sleep(0.1)
