import board
import digitalio

from adafruit_mcp230xx.mcp23017 import MCP23017, _MCP23017_ADDRESS
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
        super().__init__()

        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.mcp_config = configuration[id]
        self.outputs = dict[str, any]
        self.inputs = dict[str, any]

        address = _MCP23017_ADDRESS
        if "address" in self.mcp_config:
            address = int(self.mcp_config["address"], 0)

        i2c = board.I2C()
        self.mcp = MCP23017(i2c, address=address)

        for pin in range(0, len(self._PINS)):
            pin_id = self._PINS[pin]
            mcp_pin = self.mcp.get_pin(pin)
            gpio_config = None
            gpio_id = None
            gpio_mode = None
            gpio_state: digitalio.Pull = None
            gpio_value = False

            if pin_id in self.mcp_config:
                gpio_id = self.mcp_config.get(pin_id)
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

            if gpio_mode:
                if "input" == gpio_mode:
                    mcp_pin.switch_to_input(pull=gpio_state)
                    self.inputs[gpio_id] = mcp_pin

                elif "output" == gpio_mode:
                    mcp_pin.switch_to_output(value=gpio_value)
                    self.outputs[gpio_id] = mcp_pin

        # TODO check for adafruit keypad logic on configured inputs or use some async thread for polling
        # self.mcp.interrupt_enable = 0x00FF
        # self.mcp.interrupt_configuration = 0x0000
        # self.mcp.io_control = 0x44
        # self.mcp.clear_ints()
        
        # interrupt = digitalio.DigitalInOut(board.D13)
        # interrupt.direction = digitalio.Direction.INPUT
        # interrupt.pull = digitalio.Pull.UP

    def __del__(self):
        pass

    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []

        for key in self.inputs.keys:
            inputs.append({"pin": key, "value": not (self.inputs[key].value)})

        for key in self.outputs.keys:
            outputs.append({"pin": key, "value": not (self.outputs[key].value)})

        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        return result

    def output_status(self, pin: str):
        result = None
        if pin in self.outputs:
            result = {"pin": pin, "value": not (self.outputs[pin].value)}
        else:
            raise ValueError("pin not found")

        return result

    def enable(self, pin):
        if pin in self.outputs:
            self.outputs[pin].value = False
        else:
            raise ValueError("pin not found")

    def disable(self, pin):
        if pin in self.outputs:
            self.outputs[pin].value = True
        else:
            raise ValueError("pin not found")

    def toggle(self, pin):
        if pin in self.outputs:
            self.outputs[pin].value = not self.outputs[pin].value
        else:
            raise ValueError("pin not found")
