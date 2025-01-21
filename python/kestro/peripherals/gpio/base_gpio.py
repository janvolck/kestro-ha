class BaseGpio:

    def __init__(self):
        self.inputs = {}
        self.outputs = {}

    def status(self):
        result = {"inputs": None, "outputs": None}
        return result

    def has_pin(self, id):
        if id in self.inputs:
            return True
        
        if id in self.outputs:
            return True
        
        return False

    def output_status(self, id):
        result = None
        return result

    def enable(self, id):
        pass
    
    def disable(self, id):
        pass

    def toggle(self, id):
        pass
