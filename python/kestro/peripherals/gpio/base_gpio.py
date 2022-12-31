class BaseGpio:

    def __init__(self):
        self.inputs = []
        self.outputs = []

    def status(self):
        result = {"inputs": None, "outputs": None}
        return result

    def output_status(self, pin):
        result = None
        return result

    def enable(self, pin):
        pass
    
    def disable(self, pin):
        pass

    def toggle(self, pin):
        pass
