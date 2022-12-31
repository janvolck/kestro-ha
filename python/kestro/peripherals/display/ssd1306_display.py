# import board
# import busio
# import adafruit_ssd1306
from .base_display import BaseDisplay
from PIL import Image, ImageDraw, ImageFont


class Ssd1306Display(BaseDisplay):

    def __init__(self):
        super().__init__()

        # i2c = busio.I2C(board.SCL, board.SDA)
        # self.screen = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
        self.screen.fill(0)
        self.screen.show()

        self.font = ImageFont.load_default()

    def refresh(self):
        fb = Image.new("1", (self.screen.width, self.screen.height))

        draw = ImageDraw.Draw(fb)
        draw.rectangle(
            (0, 0, self.screen.width, self.screen.height), outline=0, fill=0)

        (ip_width, ip_height) = self.font.getsize(self.ip_info)
        (voltage_width, voltage_height) = self.font.getsize(self.voltage)
        (current_width, current_height) = self.font.getsize(self.current)

        draw.text(
            (0, 0),
            self.ip_info,
            font=self.font,
            fill=255
        )

        draw.text(
            (0, ip_height + 2),
            self.voltage,
            font=self.font,
            fill=255
        )

        draw.text(
            (voltage_width + 10, ip_height + 2),
            self.current,
            font=self.font,
            fill=255
        )

        # self.screen.image(fb)
        # self.screen.show()
