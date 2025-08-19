from flask import Blueprint, jsonify, abort, request
from typing import Optional

from ...peripherals.peripheral_service import PeripheralService

peripheral_service: Optional[PeripheralService] = None

api = Blueprint("kestro_peripherals", __name__, url_prefix="/api/kestro/peripherals")


@api.route("/gpios")
def gpios_status():
    if not peripheral_service:
        abort(500)

    return jsonify(peripheral_service.gpio().status())


@api.route("/gpios/<string:pin_id>")
def gpio_pin_status(pin_id):
    if not peripheral_service:
        abort(500)

    return jsonify(peripheral_service.gpio().get_pin_state(pin_id))


@api.route("/gpios/<string:pin_id>/on", methods=["POST"])
def on(pin_id):
    if not peripheral_service:
        abort(500)

    peripheral_service.gpio().enable(pin_id)
    return ("", 204)


@api.route("/gpios/<string:pin_id>/off", methods=["POST"])
def off(pin_id):
    if not peripheral_service:
        abort(500)

    peripheral_service.gpio().disable(pin_id)
    return ("", 204)


@api.route("/gpios/<string:pin_id>/toggle", methods=["POST"])
def toggle(pin_id):
    if not peripheral_service:
        abort(500)

    peripheral_service.gpio().toggle(pin_id)
    return ("", 204)

@api.route("/sensors")
def sensors_status():
    if not peripheral_service:
        abort(500)

    if not peripheral_service.sensors():
        abort(404)

    return jsonify(peripheral_service.sensors().status())

