import board
import terminalio
import displayio
import adafruit_displayio_ssd1306

from .base_display import BaseDisplay
from fourwire import FourWire
from i2cdisplaybus import I2CDisplayBus
from adafruit_display_text import label
from configparser import ConfigParser


def noop():
    pass


displayio._start_background = noop


class Ssd1306Display(BaseDisplay):
    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        displayio.release_displays()

        self._width = 128
        self._height = 64
        self._brightness = 1.0
        self._display_bus = None
        self._display = None

        if "width" in self._configuration:
            self._width = int(self._configuration["width"])

        if "height" in self._configuration:
            self._height = int(self._configuration["height"])

        if "brightness" in self._configuration:
            self._brightness = float(self._configuration["brightness"])

        if "text_format" in self._configuration:
            self._text_format = str(self._configuration["text_format"]).replace(
                "\\n", "\n"
            )

        if "connection" in self._configuration:
            if self._configuration["connection"] == "spi":
                spi = board.SPI()
                pin_cs = None
                pin_dc = None
                pin_reset = None
                baudrate = 1000000

                if "pin_cs" in self._configuration and hasattr(
                    board, self._configuration["pin_cs"]
                ):
                    pin_cs = getattr(board, self._configuration["pin_cs"])

                if "pin_dc" in self._configuration and hasattr(
                    board, self._configuration["pin_dc"]
                ):
                    pin_dc = getattr(board, self._configuration["pin_dc"])
                else:
                    raise KeyError(
                        "Configuration for pin_dc is required for SPI connection"
                    )

                if "pin_reset" in self._configuration and hasattr(
                    board, self._configuration["pin_reset"]
                ):
                    pin_reset = getattr(board, self._configuration["pin_reset"])

                if "baudrate" in self._configuration and hasattr(
                    board, self._configuration["baudrate"]
                ):
                    baudrate = getattr(board, self._configuration["baudrate"])

                self._display_bus = FourWire(
                    spi,
                    command=pin_dc,
                    chip_select=pin_cs,
                    reset=pin_reset,
                    baudrate=baudrate,
                )

            if self._configuration["connection"] == "i2c":
                i2c = board.I2C()
                pin_reset = None
                address = 0x3C

                if "pin_reset" in self._configuration and hasattr(
                    board, self._configuration["pin_reset"]
                ):
                    pin_reset = getattr(board, self._configuration["pin_reset"])

                if "address" in self._configuration:
                    address = int(self._configuration["address"], 0)

                self._display_bus = I2CDisplayBus(
                    i2c, device_address=address, reset=pin_reset
                )

        if self._display_bus is not None:
            self._display_bus.reset()
            self._display = adafruit_displayio_ssd1306.SSD1306(
                self._display_bus, width=self._width, height=self._height
            )
            self._display.brightness = self._brightness
            self._display.auto_refresh = False

    async def refresh(self, properties: dict[str, str]):
        
        if self._display:
            root = displayio.Group()

            background = displayio.Bitmap(self._width, self._height, 1)
            background_color = displayio.Palette(1)
            background_color[0] = 0x000000  # Black

            background_grid = displayio.TileGrid(
                background, pixel_shader=background_color, x=0, y=0
            )
            root.append(background_grid)

            # Draw a label
            text = self.formatDisplayText(properties)
            text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=0, y=12)
            root.append(text_area)
            self._display.root_group = root
            self._display.refresh()
