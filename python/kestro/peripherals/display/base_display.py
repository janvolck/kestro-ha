from configparser import ConfigParser
import chevron


class BaseDisplay:
    def __init__(self, id: str, configuration: ConfigParser):

        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.id = id
        self._configuration = configuration[id]
        self._text_format = "N/A"

    def formatDisplayText(self, properties: dict[str, any]):
        return chevron.render(template=self._text_format, data=properties)

    async def refresh(self, properties: dict[str, any]):
        pass
