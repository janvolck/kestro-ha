import time
import asyncio
import logging
import paho.mqtt.client as mqtt

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
        self.__log = logging.getLogger(__name__)
        self.__log.debug("PeripheralService created")

        self._local_properties: dict[str, any] = {}
        self._display_properties: dict[str, str] = {}
        self._tasks = []

        self._network = Network()
        self._displays = DisplayManager()
        self._gpio = GpioManager()
        self._sensors = SensorManager()
        self._mqtt = None
        self._mqtt_propertytopics: dict[str, str] = {}
        self._mqtt_topicproperties: dict[str, str] = {}

        self._network_addresses_index = 0
        self._network_address_last_rotate = None
        self._aborted = False
        self._worker = Thread(target=self._do_work)

    def load_config(self, config_path: str):
        config = ConfigParser()
        config.read(config_path)
        self._mqtt_load_config(config)
        self._mqtt_load_topic_config(config)
        self._network.load_config(config)
        self._displays.load_config(config)
        self._gpio.load_config(config)
        self._sensors.load_config(config)

    async def abort(self):
        self._aborted = True

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

    def _mqtt_load_topic_config(self, config: ConfigParser):
        if config.has_section("mqtt.propertytopics"):
            for key, value in config.items("mqtt.propertytopics"):
                self._mqtt_propertytopics[key] = value
                self._mqtt_topicproperties[value] = key

    def _mqtt_on_connect(
        self, client: mqtt.Client, userdata, flags, reason_code, properties
    ):
        self.__log.debug(f"Connected with result code {reason_code}")

        for topic in self._mqtt_topicproperties.keys():
            self._mqtt.subscribe(topic)

        for key, value in self._local_properties.items():
            self._mqtt_publish(key, value)

    def _mqtt_on_connect_fail(self, client: mqtt.Client, userdata):
        self.__log.debug(f"Connect failed")

    def _mqtt_on_disconnect(
        self, client: mqtt.Client, userdata, disconnect_flags, reason_code, properties
    ):
        self.__log.debug(f"Disconnected with result code {reason_code}")

    def _mqtt_on_message(
        self, client: mqtt.Client, userdata, message: mqtt.MQTTMessage
    ):
        self.__log.debug(f"New message received {message.topic}:{message.payload}")

        key = self._topic_to_key(message.topic)
        if key:
            self._update_display_property(key, message.topic)

    def _mqtt_publish(self, key: str, value: any):
        if self._mqtt and len(key) > 0:
            topic = self._key_to_topic(key)
            if topic:
                self._mqtt.publish(topic, value)

    def _update_local_property(self, key: str, value: any):
        property_changed = False
        self._update_display_property(key, value)

        if key in self._local_properties:
            if self._local_properties[key] != value:
                property_changed = True
        else:
            property_changed = True

        if property_changed:
            self._local_properties[key] = value
            self._mqtt_publish(key, value)

    def _update_display_property(self, key: str, value: any):
        self._display_properties[key] = value

    def _key_to_topic(self, key: str):
        if key in self._mqtt_propertytopics:
            return self._mqtt_propertytopics[key]

        return None

    def _topic_to_key(self, topic: str):
        if topic in self._mqtt_topicproperties:
            return self._mqtt_topicproperties[topic]

        return None

    async def _refresh_network(self):
        while not self._aborted:
            try:
                await self._network.refresh()

                addresses = self._network._addresses
                if len(addresses) <= 0:
                    self._network_address_last_rotate = None
                    self._network_addresses_index = -1
                    self._update_local_property("local_address", "No Connection")
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

                    self._update_local_property(key, address)

                    if i == self._network_addresses_index:
                        addr = f"{name}: {address}"
                        self._update_local_property("local_address", addr)

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

                status = self._gpio.status()

                if "outputs" in status and status["outputs"]:
                    for output in status["outputs"]:
                        if "pin" in output and "value" in output:
                            self._update_local_property(output["pin"], output["value"])

                if "inputs" in status and status["inputs"]:
                    for input in status["inputs"]:
                        if "pin" in input and "value" in input:
                            self._update_local_property(input["pin"], input["value"])

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

                status = self._sensors.status()
                if status:
                    for key, value in status.items():
                        self._update_local_property(key, value)

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

            await asyncio.sleep(0.5)
