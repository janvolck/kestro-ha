import board
import digitalio

from adafruit_mcp230xx.mcp23017 import MCP23017, _MCP23017_ADDRESS
from adafruit_mcp230xx.digital_inout import DigitalInOut
from configparser import ConfigParser
from .base_gpio import BaseGpio


class Mcp23017Gpio(BaseGpio):

    _PINS = [
        "gpa0",
        "gpa1",
        "gpa2",
        "gpa3",
        "gpa4",
        "gpa5",
        "gpa6",
        "gpa7",
        "gpb0",
        "gpb1",
        "gpb2",
        "gpb3",
        "gpb4",
        "gpb5",
        "gpb6",
        "gpb7",
    ]

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._configuration = configuration[id]
        self.__pin_to_gpio_id: dict[int, str] = {}
        self.__pin_states: dict[int, bool] = {}
        self.__pins: dict[int, DigitalInOut] = {}

        address = _MCP23017_ADDRESS
        if "address" in self._configuration:
            address = int(self._configuration["address"], 0)

        i2c = board.I2C()
        self.mcp = MCP23017(i2c, address=address)

        input_interrupts = 0
        for pin in range(0, len(self._PINS)):
            pin_id = self._PINS[pin]
            mcp_pin = self.mcp.get_pin(pin)
            gpio_config = None
            gpio_id: str = None
            gpio_mode: str = None
            gpio_state: digitalio.Pull = None
            gpio_value: bool = False

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
                        self._invert_value.append(gpio_id)

                self.__pin_to_gpio_id[pin] = gpio_id

            if gpio_mode:
                if "input" == gpio_mode:
                    input_interrupts |= 1 << pin
                    mcp_pin.switch_to_input(pull=gpio_state)
                    self._inputs[gpio_id] = mcp_pin.value
                    self.__pins[gpio_id] = mcp_pin
                    self.__pin_states[gpio_id] = mcp_pin.value

                elif "output" == gpio_mode:
                    mcp_pin.switch_to_output(
                        value=self._convert_pin_state(gpio_id, gpio_value)
                    )
                    self._outputs[gpio_id] = mcp_pin.value
                    self.__pins[gpio_id] = mcp_pin
                    self.__pin_states[gpio_id] = mcp_pin.value

        self.mcp.interrupt_enable = input_interrupts
        self.mcp.interrupt_configuration = 0x0000
        self.mcp.io_control = 0x44
        self.mcp.clear_ints()

    def __del__(self):
        pass

    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []

        for id, input in self._inputs.items():
            inputs.append({"pin": id, "value": self._convert_pin_state(id, input)})

        for id, output in self._outputs.items():
            outputs.append({"pin": id, "value": self._convert_pin_state(id, output)})

        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

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
        flags = self.mcp.int_flag
        self.mcp.clear_ints()

        interrupts = []
        for pin in flags:
            if pin in self.__pin_to_gpio_id:
                gpio_id = self.__pin_to_gpio_id[pin]
                interrupts.append(gpio_id)

        status_changed = False
        for gpio_id, pin in self.__pins.items():
            known_state = None
            current_state = self.__pins[gpio_id].value

            if gpio_id in self.__pin_states:
                known_state = self.__pin_states[gpio_id]

            # check if we might have missed a state change via one of the interrupt flags
            if known_state == current_state and gpio_id in interrupts:
                current_state = not current_state

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
