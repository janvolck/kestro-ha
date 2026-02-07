import board
import digitalio

from configparser import ConfigParser
from .base_gpio import BaseGpio


class BoardGpio(BaseGpio):

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._configuration = configuration[id]
        self.__pin_states: dict[str, bool] = {}
        self.__pin_intervals: dict[str, float] = {}
        self.__pins: dict[str, digitalio.DigitalInOut] = {}

        for pin_id in self._configuration:
            from typing import Optional
            board_pin: Optional[digitalio.Pin] = None
            gpio_config = None
            from typing import Optional
            gpio_id: str = ""
            gpio_mode: Optional[str] = None
            gpio_state: Optional[digitalio.Pull] = None
            gpio_value: bool = False

            if pin_id.startswith("d") and hasattr(board, pin_id.upper()):
                board_pin = getattr(board, pin_id.upper())
            else:
                continue

            if pin_id in self._configuration and self._configuration.get(pin_id) is str:
                gpio_id = str(self._configuration.get(pin_id))
                if gpio_id and configuration.has_section(gpio_id):
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
                    __value = gpio_config.get("value")
                    if __value and "true" == __value.lower():
                        gpio_value = True

                if "invert_value" in gpio_config:
                    __invert = gpio_config.get("invert_value")
                    if gpio_id and "true" == __invert:
                        self._invert_value.append(gpio_id)

            if gpio_mode and board_pin:
                board_io = digitalio.DigitalInOut(board_pin)
                if "input" == gpio_mode or "pulses" == gpio_mode:
                    board_io.switch_to_input(pull=gpio_state)
                    self._inputs[gpio_id] = board_io.value
                    self.__pins[gpio_id] = board_io
                    self.__pin_states[gpio_id] = board_io.value
                    
                    if "pulses" == gpio_mode:
                        self._pulses[gpio_id] = ''

                elif "output" == gpio_mode:
                    board_io.switch_to_output(
                        value=self._convert_pin_state(gpio_id, gpio_value)
                    )
                    self._outputs[gpio_id] = board_io.value
                    self.__pins[gpio_id] = board_io
                    self.__pin_states[gpio_id] = board_io.value

    def __del__(self):
        pass

    def status(self):        
        result = {"inputs": [], "outputs": [], "pulses": []}
        inputs = []
        outputs = []
        pulses = []
        
        for id, input in self._inputs.items():
            inputs.append({"pin": id, "value": self._convert_pin_state(id, input)})

        for id, output in self._outputs.items():
            outputs.append({"pin": id, "value": self._convert_pin_state(id, output)})

        for id, pulse in self._pulses.items():
            pulses.append({"pin": id, "value": pulse})
            
        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        if len(pulses) > 0:
            result["pulses"] = pulses

        return result

    def get_pin_state(self, pin: str):
        result = None
        if pin in self.__pin_states:
            result = {
                "pin": pin,
                "value": self._convert_pin_state(pin, self.__pin_states[pin]),
            }
        else:
            raise ValueError(f"""pin {pin} not found""")

        return result

    def set_pin_state(self, pin: str, status: bool):
        if pin in self._outputs and pin in self.__pins:
            self.__pins[pin].value = self._convert_pin_state(pin, status)
        else:
            raise ValueError(f"""pin {pin} not found""")

    def toggle(self, pin):
        if pin in self._outputs and pin in self.__pins:
            self.__pins[pin].value = not self.__pins[pin].value
        else:
            raise ValueError(f"""pin {pin} not found""")

    async def refresh(self):

        status_changed = False
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
                status_changed = True

                if gpio_id in self._inputs:
                    self._inputs[gpio_id] = current_state
                elif gpio_id in self._outputs:
                    self._outputs[gpio_id] = current_state

                self._publish_pin_state_changed(
                    gpio_id, self._convert_pin_state(gpio_id, current_state)
                )

        if status_changed:
            self._publish_status_changed(self.status())
