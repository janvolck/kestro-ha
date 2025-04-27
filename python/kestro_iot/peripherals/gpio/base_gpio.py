from __future__ import annotations
from configparser import ConfigParser

import asyncio


class BaseGpio:

    def __init__(self, id: str, configuration: ConfigParser):

        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.id = id
        self._configuration = configuration[id]
        self._status_changed_observers: list[GpioStatusChangedSubscriber] = []
        self._pin_state_changed_observers: list[GpioPinStateChangedSubscriber] = []

        self.outputs: dict[str, bool] = {}
        self.inputs: dict[str, bool] = {}

    def subscribe_to_status_changed(self, observer: GpioStatusChangedSubscriber):
        if observer not in self._status_changed_observers:
            self._status_changed_observers.append(observer)

    def unsubscribe_from_status_changed(self, observer: GpioStatusChangedSubscriber):
        if observer in self._status_changed_observers:
            self._status_changed_observers.remove(observer)

    def subscribe_to_pin_state_changed(self, observer: GpioPinStateChangedSubscriber):
        if observer not in self._pin_state_changed_observers:
            self._pin_state_changed_observers.append(observer)

    def unsubscribe_from_pin_state_changed(
        self, observer: GpioPinStateChangedSubscriber
    ):
        if observer in self._pin_state_changed_observers:
            self._pin_state_changed_observers.remove(observer)

    def status(self):
        result = {"inputs": None, "outputs": None}
        return result

    def has_pin(self, id: str):
        if id in self.inputs:
            return True

        if id in self.outputs:
            return True

        return False

    def has_input(self, id: str):
        if id in self.inputs:
            return True

        return False

    def has_output(self, id: str):
        if id in self.outputs:
            return True

        return False

    def get_pin_state(self, id: str):
        result = None
        return result

    def enable(self, id: str):
        self.set_pin_state(id, True)

    def disable(self, id: str):
        self.set_pin_state(id, False)

    async def push(self, id: str, time: float = 1.0):
        if self.has_input(str):
            self.toggle(id)
            await asyncio.sleep(time)
            self.toggle(id)

    def set_pin_state(self, id: str, status: bool): ...

    def toggle(self, id: str): ...

    async def refresh(self): ...

    def _publish_status_changed(self, status: any):
        event = GpioStatusChangedEvent(self, status)
        for observer in self._status_changed_observers:
            observer(event)

    def _publish_pin_state_changed(self, id: str, status: bool):
        event = GpioPinStateChangedEvent(self, id, status)
        for observer in self._pin_state_changed_observers:
            observer(event)


class GpioStatusChangedEvent:

    def __init__(self, sensor: BaseGpio, status: any):
        self.source = sensor
        self.status = status


class GpioStatusChangedSubscriber:

    def __call__(self, event: GpioStatusChangedEvent) -> None: ...


class GpioPinStateChangedEvent:

    def __init__(self, sensor: BaseGpio, id: str, status: bool):
        self.source = sensor
        self.id = id
        self.status = status


class GpioPinStateChangedSubscriber:

    def __call__(self, event: GpioPinStateChangedEvent) -> None: ...
