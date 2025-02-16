import board
import adafruit_hcsr04

from .base_distancesensor import BaseDistanceSensor
from configparser import ConfigParser


class HcSr04(BaseDistanceSensor):
    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._hcsr04 = None
        trigger_pin = None
        echo_pin = None

        if "trigger_pin" in configuration and hasattr(
            board, configuration["trigger_pin"]
        ):
            trigger_pin = getattr(board, configuration["trigger_pin"])

        if "echo_pin" in configuration and hasattr(board, configuration["echo_pin"]):
            echo_pin = getattr(board, configuration["echo_pin"])

        if trigger_pin and echo_pin:
            self._hcsr04 = adafruit_hcsr04.HCSR04(
                trigger_pin=trigger_pin, echo_pin=echo_pin
            )

        self.distance = None

    async def refresh(self):
        if self._hcsr04:
            try:
                self.distance = self._hcsr04.distance
            except RuntimeError:
                pass
            except Exception:
                pass
