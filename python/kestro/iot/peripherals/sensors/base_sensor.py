from configparser import ConfigParser


class BaseSensor:

    def __init__(self, id: str, configuration: ConfigParser):
        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.id = id
        self._configuration = configuration[id]

        pass

    def status(self):
        result = {}
        return result

    async def refresh(self):
        pass
