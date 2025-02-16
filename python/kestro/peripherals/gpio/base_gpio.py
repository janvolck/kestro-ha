import asyncio

from configparser import ConfigParser


class BaseGpio:

    def __init__(self, id: str, configuration: ConfigParser):

        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.id = id
        self._configuration = configuration[id]

        self.outputs: dict[str, bool] = {}
        self.inputs: dict[str, bool] = {}

    def status(self):
        result = {"inputs": None, "outputs": None}
        return result

    def has_pin(self, id: str):
        if id in self.inputs:
            return True

        if id in self.outputs:
            return True

        return False

    def has_input(self, id: str):
        if id in self.inputs:
            return True

        return False

    def has_output(self, id: str):
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

    async def push(self, id: str, time: float = 1.0):
        if self.has_input(str):
            self.toggle(id)
            await asyncio.sleep(time)
            self.toggle(id)

    async def refresh(self):
        pass
