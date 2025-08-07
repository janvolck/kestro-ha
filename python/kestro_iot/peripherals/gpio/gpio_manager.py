from .base_gpio import (
    BaseGpio,
    GpioStatusChangedSubscriber,
    GpioPinStateChangedSubscriber,
    GpioStatusChangedEvent,
    GpioPinStateChangedEvent,
)
from configparser import ConfigParser


class GpioManager:

    def __init__(self):
        self._devices: dict[str, BaseGpio] = {}
        self._status_changed_observers: list[GpioStatusChangedSubscriber] = []
        self._pin_state_changed_observers: list[GpioPinStateChangedSubscriber] = []

    def load_config(self, config: ConfigParser):
        if config.has_option("gpio", "devices"):
            devices = config.get("gpio", "devices")
            for device in devices.split(" "):
                if config.has_option(device, "type"):

                    device_type = config.get(device, "type")
                    if device_type == "mcp23017":
                        from .mcp23017_gpio import Mcp23017Gpio

                        gpio_device = Mcp23017Gpio(id=device, configuration=config)
                        gpio_device.subscribe_to_status_changed(
                            self._on_gpio_status_changed  # type: ignore
                        )
                        gpio_device.subscribe_to_pin_state_changed(
                            self._on_pin_state_changed  # type: ignore
                        )
                        self.add(device, gpio_device)
                    elif device_type == "board":
                        from .board_gpio import BoardGpio

                        gpio_device = BoardGpio(id=device, configuration=config)
                        gpio_device.subscribe_to_status_changed(
                            self._on_gpio_status_changed  # type: ignore
                        )
                        gpio_device.subscribe_to_pin_state_changed(
                            self._on_pin_state_changed  # type: ignore
                        )
                        self.add(device, gpio_device)

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

    def add(self, id: str, device: BaseGpio):
        self._devices[id] = device

    def remove(self, id: str):
        self._devices.pop(id)

    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []

        for device in self._devices.values():
            device_status = device.status()
            if device_status:
                if "outputs" in device_status and device_status["outputs"]:
                    for output in device_status["outputs"]:
                        outputs.append(output)

                if "inputs" in device_status and device_status["inputs"]:
                    for input in device_status["inputs"]:
                        inputs.append(input)

        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        return result

    def get_pin_state(self, pin: str):
        result = None
        for device in self._devices.values():
            if device.has_pin(pin):
                result = device.get_pin_state(pin)
                break

        if not result:
            raise ValueError(f"""pin {pin} not found""")

        return result

    def set_pin_state(self, pin: str, status: bool):
        pinFound = False

        for device in self._devices.values():
            if device.has_pin(pin):
                pinFound = True
                device.set_pin_state(pin, status)

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

        return pinFound

    def enable(self, pin):
        pinFound = False

        for device in self._devices.values():
            if device.has_pin(pin):
                device.enable(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

    def disable(self, pin):
        pinFound = False

        for device in self._devices.values():
            if device.has_pin(pin):
                device.disable(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

    def toggle(self, pin):
        pinFound = False

        for device in self._devices.values():
            if device.has_pin(pin):
                device.toggle(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

    def push(self, pin):
        pinFound = False

        for device in self._devices.values():
            if device.has_pin(pin):
                device.push(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

    async def refresh(self):
        for device in self._devices.values():
            await device.refresh()

    def _on_gpio_status_changed(self, event: GpioStatusChangedEvent) -> None:
        for observer in self._status_changed_observers:
            observer(event)

    def _on_pin_state_changed(self, event: GpioPinStateChangedEvent) -> None:
        for observer in self._pin_state_changed_observers:
            observer(event)
