import logging
import paho.mqtt.client as mqtt

from configparser import ConfigParser
from ..peripherals.peripheral_service import PeripheralService
from ..peripherals.gpio.base_gpio import GpioPinStateChangedEvent
from ..peripherals.sensors.base_sensor import SensorStatusChangedEvent


class MqttService:
    def __init__(self, peripheral_service: PeripheralService):
        self.__log = logging.getLogger(__name__)
        self.__log.debug("MqttService created")

        self._peripheral_service = peripheral_service
        self._peripheral_service.subscribe_to_pin_state_changed(
            self._on_pin_state_changed
        )
        self._peripheral_service.subscribe_to_sensor_status_changed(
            self._on_sensor_status_changed
        )

        self._mqtt = None
        self._mqtt_property_to_topic: dict[str, str] = {}
        self._mqtt_topic_to_property: dict[str, str] = {}
        self._mqtt_state_to_topic: dict[str, str] = {}
        self._mqtt_topic_to_state: dict[str, str] = {}
        self._mqtt_control_to_topic: dict[str, str] = {}
        self._mqtt_topic_to_control: dict[str, str] = {}
        self._mqtt_birth_messages: dict[str, str] = {}

        self._aborted = False

    def load_config(self, config_path: str):

        self.__log.debug(f"MqttService loading config from {config_path}")

        config = ConfigParser()
        config.read(config_path)
        self._mqtt_load_topic_config(config)
        self._mqtt_load_client_config(config)

    async def abort(self):
        self._aborted = True
        if self._mqtt:
            self._mqtt.loop_stop()
            self._mqtt.disconnect()

    def start(self):
        if self._mqtt and not self._aborted:
            self._mqtt.loop_start()

    def _mqtt_load_topic_config(self, config: ConfigParser):
        if config.has_section("mqtt.properties"):
            for key, value in config.items("mqtt.properties"):
                self._mqtt_property_to_topic[key] = value
                self._mqtt_topic_to_property[value] = key

        if config.has_section("mqtt.states"):
            for key, value in config.items("mqtt.states"):
                self._mqtt_state_to_topic[key] = value
                self._mqtt_topic_to_state[value] = key

        if config.has_section("mqtt.controls"):
            for key, value in config.items("mqtt.controls"):
                self._mqtt_control_to_topic[key] = value
                self._mqtt_topic_to_control[value] = key

    def _mqtt_load_client_config(self, config: ConfigParser):
        mqtt_client_id = None
        mqtt_host = None
        mqtt_port = 1883

        if config.has_option("mqtt", "id"):
            mqtt_client_id = config.get("mqtt", "id")

        if config.has_option("mqtt", "host"):
            mqtt_host = config.get("mqtt", "host")

        if config.has_option("mqtt", "port"):
            mqtt_port = config.getint("mqtt", "port")

        if config.has_option("mqtt", "birth.messages"):
            messages = config.get("mqtt", "birth.messages")
            for message in messages.split(" "):
                topic = None
                payload = None
                if config.has_option(message, "topic"):
                    topic = config.get(message, "topic")
                if config.has_option(message, "payload"):
                    payload = config.get(message, "payload")
                if topic and payload:
                    self._mqtt_birth_messages[topic] = payload

        if mqtt_host:
            self._mqtt = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_id
            )
            self._mqtt.on_connect = self._mqtt_on_connect
            self._mqtt.on_connect_fail = self._mqtt_on_connect_fail
            self._mqtt.on_disconnect = self._mqtt_on_disconnect
            self._mqtt.on_message = self._mqtt_on_message
            self._mqtt.connect_async(mqtt_host, mqtt_port)

    def _mqtt_on_connect(
        self, client: mqtt.Client, userdata, flags, reason_code, properties
    ):
        self.__log.debug(f"Connected with result code {reason_code}")

        # subscribe to all topics
        for topic in self._mqtt_topic_to_property.keys():
            self._mqtt.subscribe(topic)

        for topic in self._mqtt_topic_to_state.keys():
            self._mqtt.subscribe(topic)

        for topic in self._mqtt_topic_to_control.keys():
            self._mqtt.subscribe(topic)

        # publish all properties
        gpio_status = self._peripheral_service.gpio().status()
        if "inputs" in gpio_status and gpio_status["inputs"]:
            for input in gpio_status["inputs"]:
                if "pin" in input and "value" in input:
                    pin = input["pin"]
                    value = input["value"]
                    self._mqtt_publish_property(pin, value)
                    self._mqtt_publish_state(pin, value)

        if "outputs" in gpio_status and gpio_status["outputs"]:
            for output in gpio_status["outputs"]:
                if "pin" in output and "value" in output:
                    pin = output["pin"]
                    value = output["value"]
                    self._mqtt_publish_property(pin, value)
                    self._mqtt_publish_state(pin, value)

        # publish discovery messages
        for topic, payload in self._mqtt_birth_messages.items():
            self._mqtt.publish(topic, payload, retain=True)

    #         sensor_status = self._peripheral_service.sensors().status()
    #         for status in sensor_status:
    #             if "sensor" in status:
    #                 for id, value in status["sensor"].items():
    #                     self._mqtt_publish_property(id, value)

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

        # check if the message is linked to a display property
        if message.topic in self._mqtt_topic_to_property:
            key = self._mqtt_topic_to_property[message.topic]
            self._peripheral_service.update_display_property(
                key, message.payload.decode("utf-8")
            )

        if message.topic in self._mqtt_topic_to_control:
            key = self._mqtt_topic_to_control[message.topic]
            value = message.payload.decode("utf-8").lower()
            if value == "on":
                self._peripheral_service.gpio().enable(key)
            elif value == "off":
                self._peripheral_service.gpio().disable(key)
            elif value == "true":
                self._peripheral_service.gpio().enable(key)
            elif value == "false":
                self._peripheral_service.gpio().disable(key)
            elif value == "toggle":
                self._peripheral_service.gpio().toggle(key)
            elif value == "push":
                self._peripheral_service.gpio().push(key)

    def _mqtt_publish_property(self, key: str, value: any):
        if self._mqtt and len(key) > 0:
            topic = self._property_to_topic(key)
            if topic:
                self._mqtt.publish(topic, value)

    def _mqtt_publish_state(self, key: str, value: any):
        if self._mqtt and len(key) > 0:
            topic = self._state_to_topic(key)
            if topic:
                self._mqtt.publish(topic, "on" if value else "off", retain=True)

    def _property_to_topic(self, key: str):
        if key in self._mqtt_property_to_topic:
            return self._mqtt_property_to_topic[key]

        return None

    def _state_to_topic(self, key: str):
        if key in self._mqtt_state_to_topic:
            return self._mqtt_state_to_topic[key]

        return None

    def _on_sensor_status_changed(self, event: SensorStatusChangedEvent):
        if self._mqtt and event:
            if event.id in self._mqtt_property_to_topic:
                topic = self._mqtt_property_to_topic[event.id]
                self._mqtt.publish(topic, event.status)

    def _on_pin_state_changed(self, event: GpioPinStateChangedEvent):
        if event:
            self._mqtt_publish_property(event.id, event.status)
            self._mqtt_publish_state(event.id, event.status)
