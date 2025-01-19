from configparser import ConfigParser
from .proxy_gpio import ProxyGpio

config = ConfigParser()
config.read("kestro.ini")

gpio = ProxyGpio()

if config.has_option("gpio", "drivers"):
    drivers = config.get("gpio", "drivers")
    for driver in drivers.split(" "):
        if config.has_option(driver, "type"):

            driver_type = config.get(driver, "type")
            if driver_type == "mcp23017":
                from .mcp23017_gpio import Mcp23017Gpio

                gpio_driver = Mcp23017Gpio(id=driver, configuration=config)
                gpio.add(driver, gpio_driver)
