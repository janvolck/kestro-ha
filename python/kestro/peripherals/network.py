import sdbus
from sdbus_block.networkmanager import (
    IPv4Config,
    NetworkDeviceGeneric,
    NetworkManager,
    NetworkManagerBaseError,
)
import logging

from typing import Any, Dict, List, Optional, Tuple

NetworkManagerAddressData = List[Dict[str, Tuple[str, Any]]]


class Network:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Network instance created")

        self.adress = None
        self.addresses = dict()
        self.ifaces = {"wifi": "wlan0", "lan": "eth0"}

    def refresh(self):
        address = None
        addresses = dict()

        for name in self.ifaces.keys():
            try:
                iface = self.ifaces[name]
                nm = NetworkManager(sdbus.sd_bus_open_system())
                device_path = nm.get_device_by_ip_iface(iface)

                if device_path:
                    generic_device = NetworkDeviceGeneric(device_path, sdbus.sd_bus_open_system())
                    device_ip4_conf_path: str = generic_device.ip4_config
                    if device_ip4_conf_path == "/":
                        continue
                    if not generic_device.managed:
                        continue

                    ip4_conf = IPv4Config(device_ip4_conf_path, sdbus.sd_bus_open_system())
                    address_data: NetworkManagerAddressData = ip4_conf.address_data
                    for inetaddr in address_data:
                        self.logger.debug(
                            "Network address %s on iface %s"
                            % (inetaddr["address"][1], iface)
                        )

                        if not address:
                            address = inetaddr["address"][1]

                        addresses[name] = inetaddr["address"][1]
            except NetworkManagerBaseError:
                pass
            except Exception as e:
                pass

        if address is None:
            address = "No Connection"

        self.address = address
        self.addresses = addresses
