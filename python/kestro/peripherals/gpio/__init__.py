import platform
from .base_gpio import BaseGpio

if 'raspberrypi' in  platform.uname():
    from .mcp23017_gpio import Mcp23017Gpio
    gpio = Mcp23017Gpio()
else:
    gpio = BaseGpio()