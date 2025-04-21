import board
import digitalio

from configparser import ConfigParser
from .base_gpio import BaseGpio


class BoardGpio(BaseGpio):

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._configuration = configuration[id]
        self.__pin_states: dict[str, bool] = {}
        self.__pins: dict[str, digitalio.DigitalInOut] = {}
        self.__invert_value: list[str] = []

        for pin_id in self._configuration:
            board_pin: digitalio.Pin = None
            gpio_config = None
            gpio_id: str = None
            gpio_mode: str = None
            gpio_state: digitalio.Pull = None
            gpio_value: bool = False

            if pin_id.startswith("d") and hasattr(board, pin_id.upper()):
                board_pin = getattr(board, pin_id.upper())
            else:
                continue

            if pin_id in self._configuration:
                gpio_id = self._configuration.get(pin_id)
                if configuration.has_section(gpio_id):
                    gpio_config = configuration[gpio_id]

            if gpio_config:
                if "mode" in gpio_config:
                    gpio_mode = gpio_config.get("mode")

                if "state" in gpio_config:
                    __state = gpio_config.get("state")
                    if "DOWN" == __state:
                        gpio_state = digitalio.Pull.DOWN
                    elif "UP" == __state:
                        gpio_state = digitalio.Pull.UP

                if "value" in gpio_config:
                    __value = gpio_config.get("value").lower()
                    if "true" == __value:
                        gpio_value = True

                if "invert_value" in gpio_config:
                    __invert = gpio_config.get("invert_value")
                    if "true" == __invert:
                        self.__invert_value.append(gpio_id)
                        gpio_value = not gpio_value

            if gpio_mode and board_pin:
                board_io = digitalio.DigitalInOut(board_pin)
                if "input" == gpio_mode:
                    board_io.switch_to_input(pull=gpio_state)
                    self.inputs[gpio_id] = board_io.value
                    self.__pins[gpio_id] = board_io
                    self.__pin_states[gpio_id] = board_io.value

                elif "output" == gpio_mode:
                    board_io.switch_to_output(value=gpio_value)
                    self.outputs[gpio_id] = board_io.value
                    self.__pins[gpio_id] = board_io
                    self.__pin_states[gpio_id] = board_io.value

    def __del__(self):
        pass

    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []

        for id, input in self.inputs.items():
            inputs.append({"pin": id, "value": not (input)})

        for id, output in self.outputs.items():
            outputs.append({"pin": id, "value": not (output)})

        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        return result

    def get_pin_state(self, pin: str):
        result = None
        if pin in self.__pin_states:
            result = {"pin": pin, "value": not (self.__pin_states[pin])}
        else:
            raise ValueError(f"""pin {pin} not found""")

        return result

    def set_pin_state(self, pin: str, status: bool):
        if pin in self.outputs and pin in self.__pins:
            if pin in self.__invert_value:
                self.__pins[pin].value = not status
            else:
                self.__pins[pin].value = status
        else:
            raise ValueError(f"""pin {pin} not found""")

    def toggle(self, pin):
        if pin in self.outputs and pin in self.__pins:
            self.__pins[pin].value = not self.__pins[pin].value
        else:
            raise ValueError(f"""pin {pin} not found""")

    async def refresh(self):

        for gpio_id, pin in self.__pins.items():
            known_state = None
            current_state = self.__pins[gpio_id].value

            if gpio_id in self.__pin_states:
                known_state = self.__pin_states[gpio_id]

            if known_state != current_state:
                print(
                    f"""Pin number: {pin} mapped to {gpio_id} changed to value {current_state}"""
                )
                self.__pin_states[gpio_id] = current_state

                if gpio_id in self.inputs:
                    self.inputs[gpio_id] = current_state
                elif gpio_id in self.outputs:
                    self.outputs[gpio_id] = current_state
