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

        if (
            "trigger_pin" in configuration
            and configuration["trigger_pin"] is str
            and hasattr(board, str(configuration["trigger_pin"]))
        ):
            trigger_pin = getattr(board, str(configuration["trigger_pin"]))

        if (
            "echo_pin" in configuration
            and configuration["echo_pin"] is str
            and hasattr(board, str(configuration["echo_pin"]))
        ):
            echo_pin = getattr(board, str(configuration["echo_pin"]))

        if trigger_pin and echo_pin:
            self._hcsr04 = adafruit_hcsr04.HCSR04(
                trigger_pin=trigger_pin, echo_pin=echo_pin
            )

        self.distance = None

    async def refresh(self):
        if self._hcsr04:
            try:
                distance = self._hcsr04.distance

                if self.distance != distance:
                    self.distance = distance
                    self._publish_status_changed(self.status())

            except RuntimeError:
                pass
            except Exception:
                pass
