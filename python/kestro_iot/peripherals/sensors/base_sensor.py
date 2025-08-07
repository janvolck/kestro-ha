from __future__ import annotations
from configparser import ConfigParser


class BaseSensor:

    def __init__(self, id: str, configuration: ConfigParser):
        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.id = id
        self._configuration = configuration[id]
        self._observers: list[SensorStatusChangedSubscriber] = []

    def subscribe(self, observer: SensorStatusChangedSubscriber):
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: SensorStatusChangedSubscriber):
        if observer in self._observers:
            self._observers.remove(observer)

    def status(self):
        result = {}
        return result

    async def refresh(self): ...

    def _publish_status_changed(self, status):
        event = SensorStatusChangedEvent(self, status)
        for observer in self._observers:
            observer(event)


class SensorStatusChangedEvent:

    def __init__(self, sensor: BaseSensor, status):
        self.source = sensor
        self.id = sensor.id
        self.status = status


class SensorStatusChangedSubscriber:

    def __call__(self, event: SensorStatusChangedEvent) -> None: ...
