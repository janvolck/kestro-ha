from .base_sensor import BaseSensor

class BaseHumiditySensor(BaseSensor):

    def __init__(self):
        self.humidity = None

    def status(self):
        result = {"humidity": self.humidity}
        return result

    def refresh(self):
        pass
