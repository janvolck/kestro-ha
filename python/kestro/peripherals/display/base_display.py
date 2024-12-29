class BaseDisplay:
    def __init__(self):
        self._properties = {}

    def update_property(self, key: str, value: any):
        self._properties[key] = value

    def refresh(self):
        pass
