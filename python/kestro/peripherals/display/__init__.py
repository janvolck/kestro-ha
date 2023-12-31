from configparser import ConfigParser
from .base_display import BaseDisplay

config = ConfigParser()
config.read('kestro.ini')

display:BaseDisplay = None

if 'display' in config:
    if 'type' in config['display']:
        if config['display']['type'] == 'ssd1306':
            if 'connection' in config['display']:
                if config['display']['connection'] == 'spi':
                    from .ssd1306_display_spi import Ssd1306
                    display = Ssd1306()
                else:
                    from .ssd1306_display import Ssd1306
                    display = Ssd1306()
                    
        elif config['display']['type'] == 'hd44780':
            from .hd44780_8bit import HD44780Display

            if 'host' in config['display']:
                display_host = config['display']['host']
                display = HD44780Display(host='rpi4-k8s-master')
            else:
                display = HD44780Display()

if display == None:
    display = BaseDisplay()
