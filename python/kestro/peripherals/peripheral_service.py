import time
import asyncio
import logging

from configparser import ConfigParser
from threading import Thread
from .network import Network
from .display.display_manager import DisplayManager
from .gpio.gpio_manager import GpioManager
from .sensors.sensor_manager import SensorManager


class PeripheralService:
    """Initialises the configured peripherals and provides a
    central place to access and manipulate the initialised peripherals"""

    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.__logger.debug("PeripheralService created")

        self._properties: dict[str, any] = {}
        self._tasks = []

        self._network = Network()
        self._displays = DisplayManager()
        self._gpio = GpioManager()
        self._sensors = SensorManager()

        self._ip_info_index = 0
        self._ip_info_last_changed = 0.0
        self._aborted = False
        self._worker = Thread(target=self._do_work)

    def load_config(self, config_path: str):
        config = ConfigParser()
        config.read(config_path)
        self._network.load_config(config)
        self._displays.load_config(config)
        self._gpio.load_config(config)
        self._sensors.load_config(config)

    async def abort(self):
        self._aborted = True

    def update_property(self, key: str, value: any):
        self._properties[key] = value

    def displays(self):
        return self._displays

    def gpio(self):
        return self._gpio

    def sensors(self):
        return self._sensors

    def start(self):
        if not self._aborted:
            self._worker.start()

    def _do_work(self):
        loop = asyncio.new_event_loop()
        self._tasks.append(loop.create_task(self._refresh_network()))
        self._tasks.append(loop.create_task(self._refresh_gpio()))
        self._tasks.append(loop.create_task(self._refresh_sensors()))
        self._tasks.append(loop.create_task(self._refresh_displays()))
        loop.run_until_complete(asyncio.wait(self._tasks))
        loop.close

    async def _refresh_network(self):
        while not self._aborted:
            try:
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

            except RuntimeError as e:
                self.__logger.error(
                    "PeripheralService failed to refresh network:" + str(e)
                )
                pass
            except Exception as e:
                self.__logger.error(
                    "PeripheralService failed to refresh network:" + str(e)
                )
                pass

            await asyncio.sleep(5.0)

    async def _refresh_gpio(self):
        while not self._aborted:
            try:
                await self._gpio.refresh()

                status = self._gpio.status()

                if "outputs" in status and status["outputs"]:
                    for output in status["outputs"]:
                        if "pin" in output and "value" in output:
                            self.update_property(output["pin"], output["value"])

                if "inputs" in status and status["inputs"]:
                    for input in status["inputs"]:
                        if "pin" in input and "value" in input:
                            self.update_property(input["pin"], input["value"])

            except RuntimeError as e:
                self.__logger.error(
                    "PeripheralService failed to refresh GPIOs:" + str(e)
                )
                pass
            except Exception as e:
                self.__logger.error(
                    "PeripheralService failed to refresh GPIOs:" + str(e)
                )
                pass

            await asyncio.sleep(0.1)

    async def _refresh_displays(self):
        while not self._aborted:
            try:
                await self._displays.refresh(self._properties)

            except RuntimeError as e:
                self.__logger.error(
                    "PeripheralService failed to refresh displays:" + str(e)
                )
                pass
            except Exception as e:
                self.__logger.error(
                    "PeripheralService failed to refresh displays:" + str(e)
                )
                pass

            await asyncio.sleep(0.5)

    async def _refresh_sensors(self):
        while not self._aborted:
            try:
                await self._sensors.refresh()

                status = self._sensors.status()
                if status:
                    for key, value in status.items():
                        self.update_property(key, value)

            except RuntimeError as e:
                self.__logger.error(
                    "PeripheralService failed to refresh sensors:" + str(e)
                )
                pass
            except Exception as e:
                self.__logger.error(
                    "PeripheralService failed to refresh sensors:" + str(e)
                )
                pass

            await asyncio.sleep(0.5)
