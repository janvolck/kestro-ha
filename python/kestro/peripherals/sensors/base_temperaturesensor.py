from .base_sensor import BaseSensor

class BaseTemperatureSensor(BaseSensor):

    def __init__(self):
        self.temperature = None

    def status(self):
        result = {"temperature": self.temperature}
        return result

    def refresh(self):
        pass
