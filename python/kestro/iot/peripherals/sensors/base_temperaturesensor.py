from .base_sensor import BaseSensor
from configparser import ConfigParser


class BaseTemperatureSensor(BaseSensor):

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self.temperature = None

    def status(self):
        result = {"temperature": self.temperature}
        return result

    async def refresh(self):
        pass
