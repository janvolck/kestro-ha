
class BaseDisplay:

    def __init__(self):
        self.ip_info = None
        self.voltage = None
        self.current = None

    def update_ip_info(self, ip_info):
        self.ip_info = ip_info

    def update_power_info(self, voltage, current):
        if not voltage is None:
            self.voltage = "%2.2fV" % voltage

        if not current is None:
            self.current = "%1.3fA" % current

    def refresh(self):
        pass
