import platform
from .base_display import BaseDisplay

if 'raspberrypi' in platform.uname():
    from .ssd1306_display import Ssd1306Display
    display = Ssd1306Display()
else:
    from .hd44780_8bit import HD44780Display
    display = HD44780Display(host='rpi4-k8s-master')
#    display = BaseDisplay()
