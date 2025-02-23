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
        self.__log = logging.getLogger(__name__)
        self.__log.debug("Network instance created")

        self._dbus = sdbus.sd_bus_open_system()
        self._address = None
        self._addresses = dict()
        self._ifaces: dict[str, str] = {}
        self._iface_names: dict[str, str] = {}

    def __del__(self):
        if self._dbus:
            self._dbus.close()

        self.__log.debug("Network instance destroyed")

    def load_config(self, config: ConfigParser):
        if config.has_option("network", "interfaces"):
            interfaces = config.get("network", "interfaces")
            for interface in interfaces.split(" "):
                iface = None
                name = None

                if config.has_option(interface, "interface"):
                    iface = config.get(interface, "interface")
                    name = config.get(interface, "interface")

                if config.has_option(interface, "name"):
                    name = config.get(interface, "name")

            if iface:
                self._ifaces[interface] = iface

            if name:
                self._iface_names[interface] = name

    async def refresh(self):
        address = None
        addresses = []

        for key, iface in self._ifaces.items():
            try:
                nm = NetworkManager(self._dbus)
                device_path = await nm.get_device_by_ip_iface(iface)
                if device_path:
                    generic_device = NetworkDeviceGeneric(device_path, self._dbus)
                    device_ip4_conf_path: str = await generic_device.ip4_config
                    if device_ip4_conf_path == "/":
                        continue
                    if not generic_device.managed:
                        continue

                    ip4_conf = IPv4Config(device_ip4_conf_path, self._dbus)
                    address_data: NetworkManagerAddressData = (
                        await ip4_conf.address_data
                    )
                    for inetaddr in address_data:
                        iface_address = inetaddr["address"][1]
                        self.__log.debug(
                            f"Network address {iface_address} on iface {iface}"
                        )

                        iface_name = iface
                        if key in self._iface_names:
                            iface_name = self._iface_names[key]

                        address_info = {
                            "id": key,
                            "interface": iface,
                            "name": iface_name,
                            "address": iface_address,
                        }
                        addresses.append(address_info)

                        if not address:
                            address = iface_address

            except NetworkManagerBaseError as e:
                self.__log.error("Failed to get interface " + str(e))
                pass
            except Exception as e:
                self.__log.error("Failed to get interface " + str(e))
                pass

        if address is None:
            address = "No Connection"

        self._address = address
        self._addresses = addresses
