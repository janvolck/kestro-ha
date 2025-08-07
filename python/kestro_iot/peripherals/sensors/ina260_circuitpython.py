import board
import adafruit_ina260

from .base_powersensor import BasePowerSensor
from configparser import ConfigParser


class Ina260(BasePowerSensor):
    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._ina260 = None
        self._i2c = board.I2C()

        address: int = 0x40
        if "address" in self._configuration:
            address = int(self._configuration["address"])

        if self._i2c:
            self._ina260 = adafruit_ina260.INA260(self._i2c, address=address)

        self.voltage = 0
        self.current = 0

    async def refresh(self):
        if self._ina260:
            voltage = self._ina260.voltage
            current = self._ina260.current / 1000.0

            if self.voltage != voltage or self.current != current:
                self.voltage = voltage
                self.current = current
                self._publish_status_changed(self.status())
