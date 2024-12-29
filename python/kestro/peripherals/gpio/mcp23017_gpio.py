# import board
# import busio
# from digitalio import Direction, Pull
# from RPi import GPIO
# from adafruit_mcp230xx.mcp23017 import MCP23017
from .base_gpio import BaseGpio


class Mcp23017Gpio(BaseGpio):

    def __init__(self):
        super().__init__()

#         i2c = busio.I2C(board.SCL, board.SDA)
#         self.mcp = MCP23017(i2c)
# 
#         for pin in range(0, 8):
#             mcp_pin = self.mcp.get_pin(pin)
#             mcp_pin.switch_to_input(pull=Pull.UP)
#             self.inputs.append(mcp_pin)
# 
#         for pin in range(8, 16):
#             mcp_pin = self.mcp.get_pin(pin)
#             mcp_pin.switch_to_output(value=True)
#             self.outputs.append(self.mcp.get_pin(pin))
# 
#         self.mcp.interrupt_enable = 0x00FF
#         self.mcp.interrupt_configuration = 0x0000
#         self.mcp.io_control = 0x44
#         self.mcp.clear_inta()
# 
#         interrupt = 17
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(interrupt, GPIO.IN, GPIO.PUD_UP)
#         GPIO.add_event_detect(interrupt, GPIO.FALLING,
#                               callback=self.print_interrupt)

    def __del__(self):
        pass
#        GPIO.cleanup()

    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []

        for pin in range(0, 8):
            outputs.append({
                "pin": pin,
                "value": not(self.outputs[pin].value)
            })

            inputs.append({
                "pin": pin,
                "value": not(self.inputs[pin].value)
            })

        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        return result

    def output_status(self, pin):
        result = None
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            result = {
                "pin": pin,
                "value": not(self.outputs[pin].value)
            }

        return result

    def enable(self, pin):
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            self.outputs[pin].value = False

    def disable(self, pin):
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            self.outputs[pin].value = True

    def toggle(self, pin):
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            self.outputs[pin].value = not self.outputs[pin].value

    def print_interrupt(self, port):
        flags = self.mcp.int_flaga
        self.mcp.clear_inta()
        for pin_flag in flags:
            print("Interrupt connected to Pin: {}".format(port))
            print("Pin number: {} changed to: {}".format(
                pin_flag, self.inputs[pin_flag].value))

            if self.inputs[pin_flag].value:
                if self.outputs[pin_flag].value:
                    self.outputs[pin_flag].value = False
                else:
                    self.outputs[pin_flag].value = True
