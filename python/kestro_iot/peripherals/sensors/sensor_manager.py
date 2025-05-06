from .base_sensor import (
    BaseSensor,
    SensorStatusChangedEvent,
    SensorStatusChangedSubscriber,
)
from configparser import ConfigParser


class SensorManager:

    def __init__(self):
        super().__init__()
        self._devices: dict[str, BaseSensor] = {}
        self._observers: list[SensorStatusChangedSubscriber] = []

    def load_config(self, config: ConfigParser):
        if config.has_option("sensors", "devices"):
            devices = config.get("sensors", "devices")
            for device in devices.split(" "):
                if config.has_option(device, "type"):

                    device_type = config.get(device, "type")
                    if device_type == "hc-sr04":
                        from .hc_sr04 import HcSr04

                        sensor = HcSr04(id=device, configuration=config)
                        sensor.subscribe(self._on_sensor_status_changed)
                        self.add(device, sensor)

                    elif device_type == "dht22":
                        from .dht22 import Dht22

                        sensor = Dht22(id=device, configuration=config)
                        sensor.subscribe(self._on_sensor_status_changed)
                        self.add(device, sensor)

                    elif device_type == "ina260":
                        from .ina260_circuitpython import Ina260

                        sensor = Ina260(id=device, configuration=config)
                        sensor.subscribe(self._on_sensor_status_changed)
                        self.add(device, sensor)

    def add(self, id: str, driver: BaseSensor):
        self._devices[id] = driver

    def remove(self, id: str):
        self._devices.pop(id)

    def subscribe(self, observer: SensorStatusChangedSubscriber):
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: SensorStatusChangedSubscriber):
        if observer in self._observers:
            self._observers.remove(observer)

    def status(self):
        result: dict[str, any] = {}

        for device in self._devices.values():
            device_status = device.status()
            if device_status:
                for key, value in device_status.items():
                    sensor_key = f"""{device.id}.{key}"""
                    result[sensor_key] = value

        return result

    async def refresh(self):
        for device in self._devices.values():
            await device.refresh()

    def _on_sensor_status_changed(self, event: SensorStatusChangedEvent):
        for observer in self._observers:
            observer(event)
