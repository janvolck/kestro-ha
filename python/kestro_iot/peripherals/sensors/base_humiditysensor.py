from .base_sensor import BaseSensor
from configparser import ConfigParser


class BaseHumiditySensor(BaseSensor):

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self.humidity = None

    def status(self):
        result = {"humidity": self.humidity}
        return result

    async def refresh(self): ...
