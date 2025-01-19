from .base_gpio import BaseGpio

class ProxyGpio(BaseGpio):

    def __init__(self):
        super().__init__()
        self.drivers: dict[str,BaseGpio]


    def __del__(self):
        pass


    def add(self, id:str, driver:BaseGpio):
        self.drivers[id] = driver


    def remove(self,id:str):
        self.drivers.pop(id)


    def status(self):
        result = {"inputs": None, "outputs": None}
        inputs = []
        outputs = []



        if len(inputs) > 0:
            result["inputs"] = inputs

        if len(outputs) > 0:
            result["outputs"] = outputs

        return result


    def enable(self, pin):
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            self.outputs[pin].value = False


    def disable(self, pin):
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            self.outputs[pin].value = True


    def toggle(self, pin):
        if pin < 0 or pin >= len(self.outputs):
            raise ValueError(
                f"""pin must be between 0 and {len(self.outputs)}""")
        else:
            self.outputs[pin].value = not self.outputs[pin].value

