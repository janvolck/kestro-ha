from .base_gpio import BaseGpio


class ProxyGpio(BaseGpio):

    def __init__(self):
        super().__init__()
        self.drivers: dict[str, BaseGpio] = {}

    def __del__(self):
        pass

    def add(self, id: str, driver: BaseGpio):
        self.drivers[id] = driver

    def remove(self, id: str):
        self.drivers.pop(id)

    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []

        for driver in self.drivers.values():
            driver_status = driver.status()
            if driver_status:
                if "outputs" in driver_status and driver_status["outputs"]:
                    for output in driver_status["outputs"]:
                        outputs.append(output)

                if "inputs" in driver_status and driver_status["inputs"]:
                    for input in driver_status["inputs"]:
                        inputs.append(input)

        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        return result

    def pin_status(self, pin: str):
        result = None
        for driver in self.drivers.values():
            if driver.has_pin(pin):
                result = driver.pin_status(pin)
                break

        if not result:
            raise ValueError(f"""pin {pin} not found""")

        return result

    def enable(self, pin):
        pinFound = False

        for driver in self.drivers.values():
            if driver.has_pin(pin):
                driver.enable(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

    def disable(self, pin):
        pinFound = False

        for driver in self.drivers.values():
            if driver.has_pin(pin):
                driver.disable(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")

    def toggle(self, pin):
        pinFound = False

        for driver in self.drivers.values():
            if driver.has_pin(pin):
                driver.toggle(pin)
                pinFound = True

        if not pinFound:
            raise ValueError(f"""pin {pin} not found""")
