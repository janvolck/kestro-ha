from .base_display import BaseDisplay
from configparser import ConfigParser


class DisplayManager():

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
                        from .ssd1306_display import Ssd1306

                        display = Ssd1306(id=device, configuration=config)
                        self.add(device, display)

                    elif config["display"]["type"] == "hd44780":
                        from .hd44780_8bit import HD44780Display

                        if "host" in config["display"]:
                            display_host = config["display"]["host"]
                            display = HD44780Display(host="rpi4-k8s-master")
                        else:
                            display = HD44780Display()

    def add(self, id: str, driver: BaseDisplay):
        self._devices[id] = driver

    def remove(self, id: str):
        self._devices.pop(id)

    async def refresh(self, properties: dict[str, any]):
        for device in self._devices.values():
            await device.refresh(properties)
