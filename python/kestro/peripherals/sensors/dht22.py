from .base_temperaturesensor import BaseTemperatureSensor
from .base_humiditysensor import BaseHumiditySensor

import board
import adafruit_dht


class Dht22(BaseTemperatureSensor, BaseHumiditySensor):
    def __init__(self, pin: str = None):
        super().__init__()

        self._dht22 = None
        if pin and hasattr(board, pin):
            self._dht22 = adafruit_dht.DHT22(getattr(board, pin))

        self.temperature = None
        self.humidity = None
        
    def status(self):
        result = {"temperature": self.temperature, "humidity": self.humidity}
        return result

    def refresh(self):
        if self._dht22:
            try:
                self.temperature = self._dht22.temperature
                self.humidity = self._dht22.humidity
            except RuntimeError:
                pass
            except Exception:
                pass
