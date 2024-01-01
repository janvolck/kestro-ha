from .base_sensor import BaseSensor

class BaseDistanceSensor(BaseSensor):

    def __init__(self):
        self.distance = None

    def status(self):
        result = {"distance": self.distance}
        return result

    def refresh(self):
        pass
