from configparser import ConfigParser
from .base_sensor import BaseSensor
from .base_powersensor import BasePowerSensor
from .base_temperaturesensor import BaseTemperatureSensor
from .base_humiditysensor import BaseHumiditySensor

config = ConfigParser()
config.read("kestro.ini")

power_sensor: BasePowerSensor = None
temperature_sensor: BaseTemperatureSensor = None
humidity_sensor: BaseHumiditySensor = None

if "powersensor" in config:
    if "type" in config["powersensor"]:
        if config["powersensor"]["type"] == "ina260":
            from .ina260 import Ina260

            power_sensor = Ina260()


if "temperaturesensor" in config:
    if "type" in config["temperaturesensor"]:
        if config["temperaturesensor"]["type"] == "dht22":
            from .dht22 import Dht22

            pin = None
            if config["temperaturesensor"]["pin"]:
                pin = config["temperaturesensor"]["pin"]

            temperature_sensor = Dht22(pin=pin)
            humidity_sensor = temperature_sensor


if "humiditysensor" in config:
    if "type" in config["humiditysensor"]:
        if config["humiditysensor"]["type"] == "dht22":
            from .dht22 import Dht22

            pin = None
            if config["temperaturesensor"]["pin"]:
                pin = config["temperaturesensor"]["pin"]

            if humidity_sensor == None:
                humidity_sensor = Dht22(pin=pin)
                temperature_sensor = humidity_sensor


if not power_sensor:
    power_sensor = BasePowerSensor()

if not temperature_sensor:
    temperature_sensor = BaseTemperatureSensor()

if not humidity_sensor:
    humidity_sensor: BaseHumiditySensor()
