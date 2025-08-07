import board
import digitalio
import time

from .base_display import BaseDisplay
from configparser import ConfigParser


class Hd44780Display(BaseDisplay):

    __HD44780_LCD_CHR = True
    __HD44780_LCD_CMD = False

    __HD44780_LINES = [
        0x80,  # LCD RAM address for the 1st line
        0xC0,  # LCD RAM address for the 2nd line
        0x94,  # LCD RAM address for the 3rd line
        0xD4,  # LCD RAM address for the 4th line
    ]

    # Timing constants
    __HD44780_E_PULSE = 0.0005
    __HD44780_E_DELAY = 0.0005

    def __init__(self, id: str, configuration: ConfigParser):
        super().__init__(id, configuration)

        self._cols = int(self._configuration.get("cols", 20))
        self._rows = int(self._configuration.get("rows", 4))

        if "text_format" in self._configuration:
            self._text_format = str(self._configuration["text_format"]).replace(
                "\\n", "\n"
            )

        # Create IO pins using _create_io
        self.__rs = self._create_io("rs")
        self.__enable = self._create_io("enable")
        self.__db0 = self._create_io("db0")
        self.__db1 = self._create_io("db1")
        self.__db2 = self._create_io("db2")
        self.__db3 = self._create_io("db3")
        self.__db4 = self._create_io("db4")
        self.__db5 = self._create_io("db5")
        self.__db6 = self._create_io("db6")
        self.__db7 = self._create_io("db7")

        # Determine if all required settings are found
        self.__all_settings_found = all(
            [self.__rs, self.__enable, self.__db4, self.__db5, self.__db6, self.__db7]
        )
        self.__8bit = all([self.__db0, self.__db1, self.__db2, self.__db3])

        if self.__all_settings_found:
            self._initialize()

    async def refresh(self, properties: dict[str, object]):

        if self.__all_settings_found:
            message = self.formatDisplayText(properties)
            lines = message.splitlines()

            # Determine the number of lines to display
            num_lines = min(len(lines), len(self.__HD44780_LINES))

            # Display each line on the corresponding LCD line
            for i in range(num_lines):
                self._write_string(lines[i][: self._cols], self.__HD44780_LINES[i])

            # Clear any remaining lines on the display
            for i in range(num_lines, len(self.__HD44780_LINES)):
                self._write_string("", self.__HD44780_LINES[i])

    def _create_io(self, key: str) -> digitalio.DigitalInOut:
        pin_name = None
        board_pin = None
        pin = None

        if key in self._configuration:
            pin_name = self._configuration[key]

        if pin_name and hasattr(board, pin_name):
            board_pin = getattr(board, pin_name)

        if board_pin:
            pin = digitalio.DigitalInOut(board_pin)
            pin.switch_to_output()
            pin.value = False
        else:
            raise KeyError(f"Pin {key} not found in configuration or board.")

        return pin

    def _initialize(self):
        if self.__8bit:
            # 0011 0000 initialise 8-bit
            self._send_command(0x30)
            # 0011 0000 initialise 8-bit
            self._send_command(0x30)
            # 0011 0000 initialise 8-bit
            self._send_command(0x30)
            # 0011 1100 function set
            self._send_command(0x38)
            # 0000 0110 Cursor move direction
            self._send_command(0x06)
            # 0000 1100 Display On,Cursor Off, Blink Off
            self._send_command(0x0C)
            # 000001 Clear display
            self._send_command(0x01)
        else:
            self._send_command(0x33)  # 110011 Initialise
            self._send_command(0x32)  # 110010 Initialise
            self._send_command(0x06)  # 000110 Cursor move direction
            self._send_command(0x0C)  # 001100 Display On,Cursor Off, Blink Off
            self._send_command(0x28)  # 101000 Data length, number of lines, font size
            self._send_command(0x01)  # 000001 Clear display

        time.sleep(self.__HD44780_E_DELAY)

    def _send_command(self, command):
        self._lcd_byte(command, self.__HD44780_LCD_CMD)

    def _write_string(self, message, line):
        self._lcd_byte(line, self.__HD44780_LCD_CMD)

        message = message.ljust(self._cols, " ")
        for i in range(self._cols):
            self._lcd_byte(ord(message[i]), self.__HD44780_LCD_CHR)

    def _lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = True  for character
        #        False for command

        self.__rs.value = mode  # RS

        if self.__8bit:
            self.__db0.value = False
            self.__db1.value = False
            self.__db2.value = False
            self.__db3.value = False

        self.__db4.value = False
        self.__db5.value = False
        self.__db6.value = False
        self.__db7.value = False

        if self.__8bit:
            self.__db0.value = bits & 0x01 == 0x01
            self.__db1.value = bits & 0x02 == 0x02
            self.__db2.value = bits & 0x04 == 0x04
            self.__db3.value = bits & 0x08 == 0x08
            self.__db4.value = bits & 0x10 == 0x10
            self.__db5.value = bits & 0x20 == 0x20
            self.__db6.value = bits & 0x40 == 0x40
            self.__db7.value = bits & 0x80 == 0x80

            self._lcd_toggle_enable()

        else:
            self.__db4.value = bits & 0x10 == 0x10
            self.__db5.value = bits & 0x20 == 0x20
            self.__db6.value = bits & 0x40 == 0x40
            self.__db7.value = bits & 0x80 == 0x80

            self._lcd_toggle_enable()

            self.__db4.value = False
            self.__db5.value = False
            self.__db6.value = False
            self.__db7.value = False

            self.__db4.value = bits & 0x01 == 0x01
            self.__db5.value = bits & 0x02 == 0x02
            self.__db6.value = bits & 0x04 == 0x04
            self.__db7.value = bits & 0x08 == 0x08

            self._lcd_toggle_enable()

    def _lcd_toggle_enable(self):

        if self.__8bit:
            self.__enable.value = False

        time.sleep(self.__HD44780_E_DELAY)
        self.__enable.value = True
        time.sleep(self.__HD44780_E_PULSE)
        self.__enable.value = False
        time.sleep(self.__HD44780_E_DELAY)
