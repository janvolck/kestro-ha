
class BasePowerSensor:

    def __init__(self):
        self.voltage = None
        self.current = None

    def status(self):
        result = {"voltage": self.voltage, "current": self.current}
        return result

    def refresh(self):
        pass
