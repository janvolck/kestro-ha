import time
import asyncio
import logging
import paho.mqtt.client as mqtt
import socket

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

        self.__local_properties: dict[str, any] = {}
        self._tasks = []

        self._network = Network()
        self._displays = DisplayManager()
        self._gpio = GpioManager()
        self._sensors = SensorManager()
        self._mqtt = None

        self._ip_info_index = 0
        self._ip_info_last_changed = 0.0
        self._aborted = False
        self._worker = Thread(target=self._do_work)

    def load_config(self, config_path: str):
        config = ConfigParser()
        config.read(config_path)
        self._mqtt_load_config(config)
        self._network.load_config(config)
        self._displays.load_config(config)
        self._gpio.load_config(config)
        self._sensors.load_config(config)

    async def abort(self):
        self._aborted = True

    def update_local_property(self, key: str, value: any):
        property_changed = False

        if key in self.__local_properties:
            if self.__local_properties[key] != value:
                property_changed = True
        else:
            property_changed = True

        if property_changed:
            self.__local_properties[key] = value
            self._mqtt_publish(key, value)

    def displays(self):
        return self._displays

    def gpio(self):
        return self._gpio

    def sensors(self):
        return self._sensors

    def start(self):
        if not self._aborted:
            self._mqtt.loop_start()
            self._worker.start()

    def _do_work(self):
        loop = asyncio.new_event_loop()
        self._tasks.append(loop.create_task(self._refresh_network()))
        self._tasks.append(loop.create_task(self._refresh_gpio()))
        self._tasks.append(loop.create_task(self._refresh_sensors()))
        self._tasks.append(loop.create_task(self._refresh_displays()))
        loop.run_until_complete(asyncio.wait(self._tasks))
        loop.close

    def _mqtt_load_config(self, config: ConfigParser):
        mqtt_client_id = None
        mqtt_host = None
        mqtt_port = 1883

        if config.has_option("mqtt", "id"):
            mqtt_client_id = config.get("mqtt", "id")

        if config.has_option("mqtt", "host"):
            mqtt_host = config.get("mqtt", "host")

        if config.has_option("mqtt", "port"):
            mqtt_port = config.getint("mqtt", "port")

        if mqtt_host:
            self._mqtt = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_id
            )
            self._mqtt.on_connect = self._mqtt_on_connect
            self._mqtt.on_connect_fail = self._mqtt_on_connect_fail
            self._mqtt.on_disconnect = self._mqtt_on_disconnect
            self._mqtt.on_message = self._mqtt_on_message
            self._mqtt.connect_async(mqtt_host, mqtt_port)
            # TODO : decorate connect and message methods
            # publish local properties to mqtt when they change
            # subscribe to sensors and add them to properties that
            # will be sent to display on refresh
            # this way we can display status of other sensors
            # in the network on a specific display

    def _mqtt_on_connect(
        self, client: mqtt.Client, userdata, flags, reason_code, properties
    ):
        print(f"Connected with result code {reason_code}")
        client.subscribe("kestro/#")
        for key, value in self.__local_properties.items():
            self._mqtt_publish(key, value)

    def _mqtt_on_connect_fail(self, client, userdata):
        print(f"Connect failed")

    def _mqtt_on_disconnect(
        self, client, userdata, disconnect_flags, reason_code, properties
    ):
        print(f"Disconnected with result code {reason_code}")

    def _mqtt_on_message(self, client, userdata, message):
        print(f"New message received")

    def _mqtt_publish(self, key: str, value: any):
        if self._mqtt and len(key) > 0:
            topic = self._key_to_topic(key)
            self._mqtt.publish(topic, value)

    def _key_to_topic(self, key: str):
        topic = f"""kestro/{key}"""
        return topic

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
                    self.update_local_property("ip_addr", None)
                else:
                    iface = list(self._network._addresses)[self._ip_info_index]
                    addr = "%s: %s" % (iface, self._network._addresses[iface])
                    self.update_local_property("ip_addr", addr)

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
                            self.update_local_property(output["pin"], output["value"])

                if "inputs" in status and status["inputs"]:
                    for input in status["inputs"]:
                        if "pin" in input and "value" in input:
                            self.update_local_property(input["pin"], input["value"])

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
                await self._displays.refresh(self.__local_properties)

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
                        self.update_local_property(key, value)

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
