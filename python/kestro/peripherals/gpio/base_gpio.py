class BaseGpio:

    def __init__(self):
        self.outputs: dict[str, any] = {}
        self.inputs: dict[str, any] = {}

    def status(self):
        result = {"inputs": None, "outputs": None}
        return result

    def has_pin(self, id: str):
        if id in self.inputs:
            return True

        if id in self.outputs:
            return True

        return False

    def pin_status(self, id: str):
        result = None
        return result

    def enable(self, id: str):
        pass

    def disable(self, id: str):
        pass

    def toggle(self, id: str):
        pass
