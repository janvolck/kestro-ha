#!/usr/bin/python3
import pigpio
import time

# Define GPIO to LCD mapping
LCD_RS = 17
LCD_ENABLE = 22
LCD_DB0 = 10
LCD_DB1 = 9
LCD_DB2 = 11
LCD_DB3 = 13
LCD_DB4 = 5
LCD_DB5 = 6
LCD_DB6 = 13
LCD_DB7 = 19
LCD_PWR = 26

# Define some device constants
LCD_WIDTH = 20    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94  # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4  # LCD RAM address for the 4th line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

lcd = pigpio.pi('rpi4-k8s-master')


def main():

    # initialize connection to pi with lcd
    lcd.set_mode(LCD_ENABLE, pigpio.OUTPUT)  # E
    lcd.set_mode(LCD_RS, pigpio.OUTPUT)  # RS
    lcd.set_mode(LCD_DB0, pigpio.OUTPUT)  # DB0
    lcd.set_mode(LCD_DB1, pigpio.OUTPUT)  # DB1
    lcd.set_mode(LCD_DB2, pigpio.OUTPUT)  # DB2
    lcd.set_mode(LCD_DB3, pigpio.OUTPUT)  # DB3
    lcd.set_mode(LCD_DB4, pigpio.OUTPUT)  # DB4
    lcd.set_mode(LCD_DB5, pigpio.OUTPUT)  # DB5
    lcd.set_mode(LCD_DB6, pigpio.OUTPUT)  # DB6
    lcd.set_mode(LCD_DB7, pigpio.OUTPUT)  # DB7
    lcd.set_mode(LCD_PWR, pigpio.OUTPUT)  # Backlight enable

    # Initialise display
    lcd_init()

    # Toggle backlight on-off-on
    lcd_backlight(True)
    time.sleep(0.5)
    lcd_backlight(False)
    time.sleep(0.5)
    lcd_backlight(True)
    time.sleep(0.5)

    while True:

        # Send some centred test
        lcd_string("--------------------", LCD_LINE_1, 2)
        lcd_string("Rasbperry Pi", LCD_LINE_2, 2)
        lcd_string("Model B", LCD_LINE_3, 2)
        lcd_string("--------------------", LCD_LINE_4, 2)

        time.sleep(3)  # 3 second delay

        lcd_string("Raspberrypi-spy", LCD_LINE_1, 3)
        lcd_string(".co.uk", LCD_LINE_2, 3)
        lcd_string("", LCD_LINE_3, 2)
        lcd_string("20x4 LCD Module Test", LCD_LINE_4, 2)

        time.sleep(20)  # 20 second delay

        # Blank display
        lcd_byte(0x01, LCD_CMD)

        time.sleep(3)  # 3 second delay


def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command

    lcd.write(LCD_RS, mode)  # RS

    # High bits
    lcd.write(LCD_DB4, False)
    lcd.write(LCD_DB5, False)
    lcd.write(LCD_DB6, False)
    lcd.write(LCD_DB7, False)
    if bits & 0x10 == 0x10:
        lcd.write(LCD_DB4, True)
    if bits & 0x20 == 0x20:
        lcd.write(LCD_DB5, True)
    if bits & 0x40 == 0x40:
        lcd.write(LCD_DB6, True)
    if bits & 0x80 == 0x80:
        lcd.write(LCD_DB7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    lcd.write(LCD_DB4, False)
    lcd.write(LCD_DB5, False)
    lcd.write(LCD_DB6, False)
    lcd.write(LCD_DB7, False)
    if bits & 0x01 == 0x01:
        lcd.write(LCD_DB4, True)
    if bits & 0x02 == 0x02:
        lcd.write(LCD_DB5, True)
    if bits & 0x04 == 0x04:
        lcd.write(LCD_DB6, True)
    if bits & 0x08 == 0x08:
        lcd.write(LCD_DB7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()


def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    lcd.write(LCD_ENABLE, True)
    time.sleep(E_PULSE)
    lcd.write(LCD_ENABLE, False)
    time.sleep(E_DELAY)


def lcd_string(message, line, style):
    # Send string to display
    # style=1 Left justified
    # style=2 Centred
    # style=3 Right justified

    if style == 1:
        message = message.ljust(LCD_WIDTH, " ")
    elif style == 2:
        message = message.center(LCD_WIDTH, " ")
    elif style == 3:
        message = message.rjust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


def lcd_backlight(flag):
    # Toggle backlight on-off-on
    lcd.write(LCD_PWR, flag)


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(0x01, LCD_CMD)
        lcd_string("Goodbye!", LCD_LINE_1, 2)
        time.sleep(1.0)
        lcd_backlight(False)
        lcd.stop()
           
