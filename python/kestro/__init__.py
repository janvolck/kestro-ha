import os

from .webapp.controllers import (kestro_controller, peripherals_controller)
from .webapp.webserver import WebServer
from .peripherals.peripheral_service import PeripheralService


def create_app():
    peripheral_service = PeripheralService()
    peripheral_service.start()

    webserver = WebServer(__name__)
    peripherals_controller.peripheral_service = peripheral_service

    webserver.add_controller(kestro_controller.api)
    webserver.add_controller(peripherals_controller.api)

    return webserver.app
