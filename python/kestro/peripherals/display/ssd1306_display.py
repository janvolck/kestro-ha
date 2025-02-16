import board
import displayio
import terminalio
import adafruit_displayio_ssd1306

from adafruit_display_text import label
from configparser import ConfigParser
from .base_display import BaseDisplay


class Ssd1306(BaseDisplay):
    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__()

        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.__ssd1306_config = configuration[id]
        self._width = 128
        self._height = 64
        self._brightness = 1.0
        self._display_bus = None
        self._display = None
        self._text_format = ""

        if "width" in self.__ssd1306_config:
            self._width = int(self.__ssd1306_config["width"])

        if "height" in self.__ssd1306_config:
            self._height = int(self.__ssd1306_config["height"])

        if "brightness" in self.__ssd1306_config:
            self._brightness = float(self.__ssd1306_config["brightness"])

        if "text_format" in self.__ssd1306_config:
            self._text_format = str(self.__ssd1306_config["text_format"]).replace(
                "\\n", "\n"
            )

        if "connection" in self.__ssd1306_config:
            if self.__ssd1306_config["connection"] == "spi":
                spi = board.SPI()
                pin_cs = None
                pin_dc = None
                pin_reset = None
                baudrate = 1000000

                if "pin_cs" in self.__ssd1306_config and hasattr(
                    board, self.__ssd1306_config["pin_cs"]
                ):
                    pin_cs = getattr(board, self.__ssd1306_config["pin_cs"])

                if "pin_dc" in self.__ssd1306_config and hasattr(
                    board, self.__ssd1306_config["pin_dc"]
                ):
                    pin_dc = getattr(board, self.__ssd1306_config["pin_dc"])

                if "pin_reset" in self.__ssd1306_config and hasattr(
                    board, self.__ssd1306_config["pin_reset"]
                ):
                    pin_reset = getattr(board, self.__ssd1306_config["pin_reset"])

                if "baudrate" in self.__ssd1306_config and hasattr(
                    board, self.__ssd1306_config["baudrate"]
                ):
                    baudrate = getattr(board, self.__ssd1306_config["baudrate"])

                self._display_bus = displayio.FourWire(
                    spi,
                    command=pin_dc,
                    chip_select=pin_cs,
                    reset=pin_reset,
                    baudrate=baudrate,
                )

            if self.__ssd1306_config["connection"] == "i2c":
                i2c = board.I2C()
                pin_reset = None
                address = 0x3C

                if "pin_reset" in self.__ssd1306_config and hasattr(
                    board, self.__ssd1306_config["pin_reset"]
                ):
                    pin_reset = getattr(board, self.__ssd1306_config["pin_reset"])

                if "address" in self.__ssd1306_config:
                    address = int(self.__ssd1306_config["address"], 0)

                self._display_bus = displayio.I2CDisplay(
                    i2c, device_address=address, reset=pin_reset
                )

        if self._display_bus is not None:
            self._display_bus.reset()
            self._display = adafruit_displayio_ssd1306.SSD1306(
                self._display_bus, width=self._width, height=self._height
            )
            self._display.auto_refresh = False
            self._display.brightness = self._brightness

    async def refresh(self, properties: dict[str, any]):
        root = displayio.Group()

        background = displayio.Bitmap(self._width, self._height, 1)
        background_color = displayio.Palette(1)
        background_color[0] = 0x000000  # Black

        background_grid = displayio.TileGrid(
            background, pixel_shader=background_color, x=0, y=0
        )
        root.append(background_grid)

        # Draw a label
        text = None
        try:
            text = self._text_format.format(property=properties)
        except Exception as e:
            text = "Format Error"
            pass

        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=0, y=12)
        root.append(text_area)
        self._display.root_group = root
        self._display.refresh()
