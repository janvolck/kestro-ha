from .base_sensor import BaseSensor
from configparser import ConfigParser


class BasePowerSensor(BaseSensor):

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self.voltage = None
        self.current = None

    def status(self):
        result = {"voltage": self.voltage, "current": self.current}
        return result

    async def refresh(self):
        pass
