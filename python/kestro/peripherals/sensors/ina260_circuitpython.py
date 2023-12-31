import board
import adafruit_ina260
from .base_powersensor import BasePowerSensor


class Ina260(BasePowerSensor):
    def __init__(self, address: int = 0x40):
        super().__init__()

        self._ina260 = None
        self._i2c = board.I2C()
                
        if self._i2c:
            self._ina260 = adafruit_ina260.INA260(self._i2c, address=address)

        self.voltage = 0
        self.current = 0


    def refresh(self):
        if self._ina260:
            self.voltage = self._ina260.voltage
            self.current = self._ina260.current / 1000.0
