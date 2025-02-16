import sdbus
from sdbus_async.networkmanager import (
    IPv4Config,
    NetworkDeviceGeneric,
    NetworkManager,
    NetworkManagerBaseError,
)
import logging

from typing import Any, Dict, List, Tuple
from configparser import ConfigParser


NetworkManagerAddressData = List[Dict[str, Tuple[str, Any]]]


class Network:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Network instance created")

        self._nm = None
        self._address = None
        self._addresses = dict()
        self._ifaces = dict()

    def load_config(self, config: ConfigParser):
        if "network" in config:
            for name in config.options("network"):
                value = config.get("network", name)
                self._ifaces[name] = value

    async def refresh(self):
        address = None
        addresses = dict()

        for name in self._ifaces.keys():
            try:
                iface = self._ifaces[name]
                nm = NetworkManager(sdbus.sd_bus_open_system())
                device_path = await nm.get_device_by_ip_iface(iface)
                if device_path:
                    generic_device = NetworkDeviceGeneric(
                        device_path, sdbus.sd_bus_open_system()
                    )
                    device_ip4_conf_path: str = await generic_device.ip4_config
                    if device_ip4_conf_path == "/":
                        continue
                    if not generic_device.managed:
                        continue

                    ip4_conf = IPv4Config(
                        device_ip4_conf_path, sdbus.sd_bus_open_system()
                    )
                    address_data: NetworkManagerAddressData = (
                        await ip4_conf.address_data
                    )
                    for inetaddr in address_data:
                        self.logger.debug(
                            "Network address %s on iface %s"
                            % (inetaddr["address"][1], iface)
                        )

                        if not address:
                            address = inetaddr["address"][1]

                        addresses[name] = inetaddr["address"][1]
            except NetworkManagerBaseError as e:
                self.logger.error("Failed to get interface " + e)
                pass
            except Exception as e:
                self.logger.error("Failed to get interface " + e)
                pass

        if address is None:
            address = "No Connection"

        self._address = address
        self._addresses = addresses
