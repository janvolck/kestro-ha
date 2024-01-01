import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

from .base_display import BaseDisplay


class Ssd1306(BaseDisplay):
    def __init__(self, configuration: dict):
        super().__init__()

        displayio.release_displays()

        self._width = 128
        self._height = 64
        self._brightness = 1.0
        self._display_bus = None
        self._display = None
        self._text_format = "Hello Ssd1306"

        if "width" in configuration:
            self._width = int(configuration["width"])

        if "height" in configuration:
            self._height = int(configuration["height"])

        if "brightness" in configuration:
            self._brightness = float(configuration["brightness"])

        if "text_format" in configuration:
            self._text_format = str(configuration["text_format"]).replace("\\n", "\n")

        if "connection" in configuration:
            if configuration["connection"] == "spi":
                spi = board.SPI()
                pin_cs = None
                pin_dc = None
                pin_reset = None
                baudrate = 1000000

                if "pin_cs" in configuration and hasattr(
                    board, configuration["pin_cs"]
                ):
                    pin_cs = getattr(board, configuration["pin_cs"])

                if "pin_dc" in configuration and hasattr(
                    board, configuration["pin_dc"]
                ):
                    pin_dc = getattr(board, configuration["pin_dc"])

                if "pin_reset" in configuration and hasattr(
                    board, configuration["pin_reset"]
                ):
                    pin_reset = getattr(board, configuration["pin_reset"])

                if "baudrate" in configuration and hasattr(
                    board, configuration["baudrate"]
                ):
                    baudrate = getattr(board, configuration["baudrate"])

                self._display_bus = displayio.FourWire(
                    spi,
                    command=pin_dc,
                    chip_select=pin_cs,
                    reset=pin_reset,
                    baudrate=baudrate,
                )

        if self._display_bus is not None:
            self._display_bus.reset()
            self._display = adafruit_displayio_ssd1306.SSD1306(
                self._display_bus, width=self._width, height=self._height
            )
            self._display.brightness = self._brightness

    def refresh(self):
        root = displayio.Group()

        background = displayio.Bitmap(self._width, self._height, 1)
        background_color = displayio.Palette(1)
        background_color[0] = 0x000000  # Black

        background_grid = displayio.TileGrid(
            background, pixel_shader=background_color, x=0, y=0
        )
        root.append(background_grid)

        # Draw a label
        text = self._text_format.format(property=self._properties)
        text_area = label.Label(
            terminalio.FONT, text=text, color=0xFFFFFF, x=0, y=12
        )
        root.append(text_area)
        self._display.root_group = root