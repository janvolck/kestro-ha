from .base_sensor import BaseSensor
from configparser import ConfigParser


class BaseDistanceSensor(BaseSensor):

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self.distance = None

    def status(self):
        result = {"distance": self.distance}
        return result

    async def refresh(self): ...
