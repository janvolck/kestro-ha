from configparser import ConfigParser
import chevron


class BaseDisplay:
    def __init__(self, id: str, configuration: ConfigParser):

        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")

        self.id = id
        self._configuration = configuration[id]
        self._text_format = "N/A"

    def formatDisplayText(self, properties: dict[str, object]):
        data: dict[str, object] = {}

        for key, value in properties.items():
            chevron_key = key.replace(".", "_")
            data[chevron_key] = value

        return chevron.render(template=self._text_format, data=data)

    async def refresh(self, properties: dict[str, object]): ...
