import os

from .webapp.controllers import kestro_controller, peripherals_controller
from .webapp.webserver import WebServer
from .peripherals.peripheral_service import PeripheralService
from .mqtt.mqtt_service import MqttService


def create_app():
    config_path = os.getenv("KESTRO_CONFIG", "kestro.ini")

    peripheral_service = PeripheralService()
    peripheral_service.load_config(config_path)
    peripheral_service.start()

    mqtt_service = MqttService(peripheral_service)
    mqtt_service.load_config(config_path)
    mqtt_service.start()

    webserver = WebServer(__name__)
    peripherals_controller.peripheral_service = peripheral_service

    webserver.add_controller(kestro_controller.api)
    webserver.add_controller(peripherals_controller.api)

    return webserver.app
