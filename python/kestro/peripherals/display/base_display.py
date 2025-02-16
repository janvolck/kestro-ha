from configparser import ConfigParser

class BaseDisplay:
    def __init__(self, id: str, configuration: ConfigParser):
        
        if not configuration.has_section(id):
            raise KeyError(f"""configuration section {id} not found""")
    
        self.id = id
        self._configuration = configuration[id]
        

    async def refresh(self, properties: dict[str, any]):
        pass
