from .base_display import BaseDisplay
from configparser import ConfigParser


class DisplayManager:

    def __init__(self):
        super().__init__()
        self._devices: dict[str, BaseDisplay] = {}

    def __del__(self):
        pass

    def load_config(self, config: ConfigParser):
        if config.has_option("displays", "devices"):
            devices = config.get("displays", "devices")
            for device in devices.split(" "):
                if config.has_option(device, "type"):

                    device_type = config.get(device, "type")
                    if device_type == "ssd1306":
                        from .ssd1306_display import Ssd1306Display

                        display = Ssd1306Display(id=device, configuration=config)
                        self.add(device, display)

                    elif device_type == "hd44780":
                        from .hd44780_display import Hd44780Display

                        display = Hd44780Display(id=device, configuration=config)
                        self.add(device, display)

    def add(self, id: str, driver: BaseDisplay):
        self._devices[id] = driver

    def remove(self, id: str):
        self._devices.pop(id)

    async def refresh(self, properties: dict[str, object]):
        for device in self._devices.values():
            await device.refresh(properties)
