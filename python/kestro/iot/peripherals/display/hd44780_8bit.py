import pigpio
import time
import datetime
from .base_display import BaseDisplay


class HD44780Display(BaseDisplay):
    # Define GPIO to LCD mapping
    __LCD_RS = 17
    __LCD_ENABLE = 22
    __LCD_DB0 = 10
    __LCD_DB1 = 9
    __LCD_DB2 = 11
    __LCD_DB3 = 27
    __LCD_DB4 = 5
    __LCD_DB5 = 6
    __LCD_DB6 = 13
    __LCD_DB7 = 19

    # Define some device constants
    __LCD_WIDTH = 20    # Maximum characters per line
    __LCD_CHR = True
    __LCD_CMD = False

    __LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
    __LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
    __LCD_LINE_3 = 0x94  # LCD RAM address for the 3rd line
    __LCD_LINE_4 = 0xD4  # LCD RAM address for the 4th line

    # Timing constants
    __E_PULSE = 0.0005
    __E_DELAY = 0.0005

    def __init__(self, host: str = None):
        super().__init__()

        if host:
            self.__lcd = pigpio.pi(host=host)
        else:
            self.__lcd = pigpio.pi()

        self.__lcd.set_mode(self.__LCD_ENABLE, pigpio.OUTPUT)  # E
        self.__lcd.set_mode(self.__LCD_RS, pigpio.OUTPUT)  # RS
        self.__lcd.set_mode(self.__LCD_DB0, pigpio.OUTPUT)  # DB0
        self.__lcd.set_mode(self.__LCD_DB1, pigpio.OUTPUT)  # DB1
        self.__lcd.set_mode(self.__LCD_DB2, pigpio.OUTPUT)  # DB2
        self.__lcd.set_mode(self.__LCD_DB3, pigpio.OUTPUT)  # DB3
        self.__lcd.set_mode(self.__LCD_DB4, pigpio.OUTPUT)  # DB4
        self.__lcd.set_mode(self.__LCD_DB5, pigpio.OUTPUT)  # DB5
        self.__lcd.set_mode(self.__LCD_DB6, pigpio.OUTPUT)  # DB6
        self.__lcd.set_mode(self.__LCD_DB7, pigpio.OUTPUT)  # DB7

        # Initialise display by soft reset

        # 0011 0000 initialise 8-bit
        self._lcd_command(0x30)
        # 0011 0000 initialise 8-bit
        self._lcd_command(0x30)
        # 0011 0000 initialise 8-bit
        self._lcd_command(0x30)
        # 0011 1100 function set
        self._lcd_command(0x38)
        # 0000 0110 Cursor move direction
        self._lcd_command(0x06)
        # 0000 1100 Display On,Cursor Off, Blink Off
        self._lcd_command(0x0C)
        # 000001 Clear display
        self._lcd_command(0x01)

        time.sleep(self. __E_DELAY)

        # Blank display
        self._lcd_command(0x01)

    def _lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = True  for character
        #        False for command

        self.__lcd.write(self.__LCD_RS, mode)  # RS

        self.__lcd.write(self.__LCD_DB0, (bits & 0x01 == 0x01))
        self.__lcd.write(self.__LCD_DB1, (bits & 0x02 == 0x02))
        self.__lcd.write(self.__LCD_DB2, (bits & 0x04 == 0x04))
        self.__lcd.write(self.__LCD_DB3, (bits & 0x08 == 0x08))
        self.__lcd.write(self.__LCD_DB4, (bits & 0x10 == 0x10))
        self.__lcd.write(self.__LCD_DB5, (bits & 0x20 == 0x20))
        self.__lcd.write(self.__LCD_DB6, (bits & 0x40 == 0x40))
        self.__lcd.write(self.__LCD_DB7, (bits & 0x80 == 0x80))

        self._lcd_toggle_enable()

    def _lcd_toggle_enable(self):
        # Toggle enable
        self.__lcd.write(self.__LCD_ENABLE, False)
        time.sleep(self.__E_DELAY)
        self.__lcd.write(self.__LCD_ENABLE, True)
        time.sleep(self.__E_PULSE)
        self.__lcd.write(self.__LCD_ENABLE, False)
        time.sleep(self.__E_DELAY)

    def _lcd_command(self, command):
        self._lcd_byte(command, self.__LCD_CMD)

    def _lcd_string(self, message, line):
        self._lcd_byte(line, self.__LCD_CMD)

        message = message.ljust(self.__LCD_WIDTH, " ")
        for i in range(self.__LCD_WIDTH):
            self._lcd_byte(ord(message[i]), self.__LCD_CHR)

    def refresh(self):
        t = time.localtime()
        now = datetime.datetime.now()

        self._lcd_string(now.strftime("%d/%m/%Y  %H:%M:%S"), self.__LCD_LINE_1)
        self._lcd_string(f"{self.voltage} / {self.current}", self.__LCD_LINE_2)
        self._lcd_string("", self.__LCD_LINE_3)
        self._lcd_string("", self.__LCD_LINE_4)
