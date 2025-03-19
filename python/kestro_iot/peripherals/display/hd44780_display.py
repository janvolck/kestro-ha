import board
import adafruit_character_lcd.character_lcd as characterlcd
import digitalio

from .base_display import BaseDisplay
from configparser import ConfigParser


class Hd44780Display(BaseDisplay):
    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._cols = int(self._configuration.get("cols", 20))
        self._rows = int(self._configuration.get("rows", 4))
        self._display: characterlcd.Character_LCD_Mono = None

        if "text_format" in self._configuration:
            self._text_format = str(self._configuration["text_format"]).replace(
                "\\n", "\n"
            )

        # Create IO pins using _create_io
        rs = self._create_io("rs")
        enable = self._create_io("enable")
        db0 = self._create_io("db0")
        db1 = self._create_io("db1")
        db2 = self._create_io("db2")
        db3 = self._create_io("db3")
        db4 = self._create_io("db4")
        db5 = self._create_io("db5")
        db6 = self._create_io("db6")
        db7 = self._create_io("db7")

        # Determine if all required settings are found
        all_settings_found = all([rs, enable, db0, db1, db2, db3])
        eight_bit = all([db4, db5, db6, db7])

        if all_settings_found:
            if eight_bit:
                self._display = characterlcd.Character_LCD_Mono(
                    rs,
                    enable,
                    db0,
                    db1,
                    db2,
                    db3,
                    db4,
                    db5,
                    db6,
                    db7,
                    self._cols,
                    self._rows,
                )
            else:
                self._display = characterlcd.Character_LCD_Mono(
                    rs, enable, db0, db1, db2, db3, self._cols, self._rows
                )

    async def refresh(self, properties: dict[str, any]):

        if self._display:
            # Draw a label
            self._display.message = self.formatDisplayText(properties)

    def _create_io(self, key: str):
        pin_name = None
        board_pin = None
        pin = None

        if key in self._configuration:
            pin_name = self._configuration[key]

        if pin_name and hasattr(board, pin_name):
            board_pin = getattr(board, pin_name)

        if board_pin:
            pin = digitalio.DigitalInOut(board_pin)

        return pin
