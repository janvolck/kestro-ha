import time
import asyncio
import logging

from configparser import ConfigParser
from threading import Thread
from .network import Network
from .display.display_manager import DisplayManager
from .gpio.gpio_manager import GpioManager
from .gpio.base_gpio import (
    GpioStatusChangedSubscriber,
    GpioPinStateChangedSubscriber,
    GpioPinStateChangedEvent,
    GpioStatusChangedEvent,
)
from .sensors.sensor_manager import SensorManager
from .sensors.base_sensor import SensorStatusChangedSubscriber, SensorStatusChangedEvent


class PeripheralService:
    """Initialises the configured peripherals and provides a
    central place to access and manipulate the initialised peripherals"""

    def __init__(self):
        self.__log = logging.getLogger(__name__)
        self.__log.debug("PeripheralService created")

        self._display_properties: dict[str, str] = {}
        self._tasks = []
        self._sensor_status_changed_observers: list[SensorStatusChangedSubscriber] = []
        self._gpio_status_changed_observers: list[GpioStatusChangedSubscriber] = []
        self._pin_state_changed_observers: list[GpioPinStateChangedSubscriber] = []

        self._network = Network()
        self._displays = DisplayManager()
        self._gpio = GpioManager()
        self._gpio.subscribe_to_status_changed(self._on_gpio_status_changed)
        self._gpio.subscribe_to_pin_state_changed(self._on_pin_state_changed)
        self._sensors = SensorManager()
        self._sensors.subscribe(self._on_sensor_status_changed)

        self._network_addresses_index = 0
        self._network_address_last_rotate = None
        self._aborted = False
        self._worker = Thread(target=self._do_work)

    def load_config(self, config_path: str):

        self.__log.debug(f"PeripheralService loading config from {config_path}")

        config = ConfigParser()
        config.read(config_path)
        self._network.load_config(config)
        self._displays.load_config(config)
        self._gpio.load_config(config)
        self._sensors.load_config(config)

    def subscribe_to_sensor_status_changed(
        self, observer: SensorStatusChangedSubscriber
    ):
        if observer not in self._sensor_status_changed_observers:
            self._sensor_status_changed_observers.append(observer)

    def unsubscribe_from_sensor_status_changed(
        self, observer: SensorStatusChangedSubscriber
    ):
        if observer in self._sensor_status_changed_observers:
            self._sensor_status_changed_observers.remove(observer)

    def subscribe_to_gpio_status_changed(self, observer: GpioStatusChangedSubscriber):
        if observer not in self._gpio_status_changed_observers:
            self._gpio_status_changed_observers.append(observer)

    def unsubscribe_from_gpio_status_changed(
        self, observer: GpioStatusChangedSubscriber
    ):
        if observer in self._gpio_status_changed_observers:
            self._gpio_status_changed_observers.remove(observer)

    def subscribe_to_pin_state_changed(self, observer: GpioPinStateChangedSubscriber):
        if observer not in self._pin_state_changed_observers:
            self._pin_state_changed_observers.append(observer)

    def unsubscribe_from_pin_state_changed(
        self, observer: GpioPinStateChangedSubscriber
    ):
        if observer in self._pin_state_changed_observers:
            self._pin_state_changed_observers.remove(observer)

    def update_display_property(self, key: str, value: any):
        self._display_properties[key] = value

    async def abort(self):
        self._aborted = True

    def displays(self) -> DisplayManager:
        return self._displays

    def gpio(self) -> GpioManager:
        return self._gpio

    def sensors(self) -> SensorManager:
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
        loop.close()

    async def _refresh_network(self):
        while not self._aborted:
            try:
                await self._network.refresh()

                addresses = self._network._addresses
                if len(addresses) <= 0:
                    self._network_address_last_rotate = None
                    self._network_addresses_index = -1
                    self.update_display_property("local_address", "No Connection")
                elif not self._network_address_last_rotate:
                    self._network_address_last_rotate = time.time()
                    self._network_addresses_index = 0
                elif time.time() - self._network_address_last_rotate > 5.0:
                    self._network_address_last_rotate = time.time()
                    self._network_addresses_index += 1

                if self._network_addresses_index >= len(addresses):
                    self._network_addresses_index = 0

                for i in range(len(addresses)):
                    address = addresses[i]
                    key = address["id"]
                    name = address["name"]
                    address = address["address"]

                    self.update_display_property(key, address)

                    if i == self._network_addresses_index:
                        addr = f"{name}: {address}"
                        self.update_display_property("local_address", addr)

            except RuntimeError as e:
                self.__log.error(
                    "PeripheralService failed to refresh network:" + str(e)
                )
                pass
            except Exception as e:
                self.__log.error(
                    "PeripheralService failed to refresh network:" + str(e)
                )
                pass

            await asyncio.sleep(5.0)

    async def _refresh_gpio(self):
        while not self._aborted:
            try:
                await self._gpio.refresh()

            except RuntimeError as e:
                self.__log.error("PeripheralService failed to refresh GPIOs:" + str(e))
                pass
            except Exception as e:
                self.__log.error("PeripheralService failed to refresh GPIOs:" + str(e))
                pass

            await asyncio.sleep(0.1)

    async def _refresh_sensors(self):
        while not self._aborted:
            try:
                await self._sensors.refresh()

            except RuntimeError as e:
                self.__log.error(
                    "PeripheralService failed to refresh sensors:" + str(e)
                )
                pass
            except Exception as e:
                self.__log.error(
                    "PeripheralService failed to refresh sensors:" + str(e)
                )
                pass

            await asyncio.sleep(1.0)

    async def _refresh_displays(self):
        while not self._aborted:
            try:
                await self._displays.refresh(self._display_properties)

            except RuntimeError as e:
                self.__log.error(
                    "PeripheralService failed to refresh displays:" + str(e)
                )
                pass
            except Exception as e:
                self.__log.error(
                    "PeripheralService failed to refresh displays:" + str(e)
                )
                pass

            await asyncio.sleep(1.0)

    def _on_sensor_status_changed(self, event: SensorStatusChangedEvent):
        if event:
            property_name = f"{event}.{event.id}"
            self.update_display_property(property_name, event.status)

            for observer in self._sensor_status_changed_observers:
                observer(event)

    def _on_gpio_status_changed(self, event: GpioStatusChangedEvent):
        if event:
            for observer in self._gpio_status_changed_observers:
                observer(event)

    def _on_pin_state_changed(self, event: GpioPinStateChangedEvent):

        if event:
            self.update_display_property(event.id, event.status)

            for observer in self._pin_state_changed_observers:
                observer(event)
