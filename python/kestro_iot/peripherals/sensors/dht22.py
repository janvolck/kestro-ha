import board
import adafruit_dht

from .base_temperaturesensor import BaseTemperatureSensor
from .base_humiditysensor import BaseHumiditySensor
from configparser import ConfigParser


class Dht22(BaseTemperatureSensor, BaseHumiditySensor):
    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._dht22 = None

        pin = None
        if "pin" in self._configuration:
            pin = self._configuration["pin"]

        if pin and hasattr(board, pin):
            self._dht22 = adafruit_dht.DHT22(getattr(board, pin))

        self.temperature = None
        self.humidity = None

    def status(self):
        result = {"temperature": self.temperature, "humidity": self.humidity}
        return result

    async def refresh(self):
        if self._dht22:
            try:
                temperature = self._dht22.temperature
                humidity = self._dht22.humidity

                if self.temperature != temperature or self.humidity != humidity:
                    self.temperature = temperature
                    self.humidity = humidity

                    self._publish_status_changed(self.status())

            except RuntimeError:
                pass
            except Exception:
                pass
