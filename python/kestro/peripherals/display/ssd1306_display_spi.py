import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

from .base_display import BaseDisplay


class Ssd1306(BaseDisplay):
    WIDTH = 128
    HEIGHT = 64
    BORDER = 5

    def __init__(self):
        super().__init__()

        displayio.release_displays()
        spi = board.SPI()
        oled_cs = None
        oled_dc = board.D22
        oled_reset = board.D18
        self.display_bus = displayio.FourWire(
            spi,
            command=oled_dc,
            chip_select=oled_cs,
            reset=oled_reset,
            baudrate=1000000,
        )
        self.display_bus.reset()

        # i2c = busio.I2C(board.SCL, board.SDA)
        self.display = adafruit_displayio_ssd1306.SSD1306(
            self.display_bus, width=self.WIDTH, height=self.HEIGHT
        )
        
        self.display.auto_refresh = False

        
        splash = displayio.Group()
        self.display.show(splash)

        color_bitmap = displayio.Bitmap(self.WIDTH, self.HEIGHT, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0xFFFFFF  # White        

        bg_sprite = displayio.TileGrid(
            color_bitmap, pixel_shader=color_palette, x=0, y=0
        )
        splash.append(bg_sprite)

        # Draw a smaller inner rectangle
        inner_bitmap = displayio.Bitmap(
            self.WIDTH - self.BORDER * 2, self.HEIGHT - self.BORDER * 2, 1
        )

        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000  # Black
        inner_sprite = displayio.TileGrid(
            inner_bitmap, pixel_shader=inner_palette, x=self.BORDER, y=self.BORDER
        )
        splash.append(inner_sprite)


        # Draw a label
        text = "Hello Kestro!"
        text_area = label.Label(
            terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=self.HEIGHT // 2 - 1
        )
        splash.append(text_area)
        self.display.refresh()


    def refresh(self):
        pass
