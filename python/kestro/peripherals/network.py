import netifaces as ni
import logging


class Network:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Network instance created')

        self.adress = None
        self.addresses = dict()
        self.ifaces = {"wifi": "wlan0", "lan": "eth0"}

    def refresh(self):

        address = None
        addresses = dict()

        for name in self.ifaces.keys():
            iface = self.ifaces[name]
            if iface in ni.interfaces():                        
                addrs = ni.ifaddresses(iface)
                if ni.AF_INET in addrs:
                    self.logger.debug('Network address %s on iface %s' %
                                    (addrs[ni.AF_INET][0]['addr'], iface))

                    if not address:
                        address = addrs[ni.AF_INET][0]['addr']

                    addresses[name] = addrs[ni.AF_INET][0]['addr']

        if address is None:
            address = "No Connection"

        self.address = address
        self.addresses = addresses
