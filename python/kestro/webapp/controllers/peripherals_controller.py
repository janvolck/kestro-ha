from flask import Blueprint, jsonify, abort, request

from kestro.peripherals.peripheral_service import PeripheralService

peripheral_service: PeripheralService = None

api = Blueprint("kestro_peripherals", __name__, url_prefix="/api/kestro/peripherals")


@api.route("/gpios")
def gpios_status():
    if not peripheral_service:
        abort(500)

    return jsonify(peripheral_service.gpio().status())


@api.route("/gpios/output/<int:pin_id>")
def gpio_output_status(pin_id):
    if not peripheral_service:
        abort(500)

    return jsonify(peripheral_service.gpio().output_status(pin_id))


@api.route("/gpios/output/<int:pin_id>/on", methods=["POST"])
def on(pin_id):
    if not peripheral_service:
        abort(500)

    peripheral_service.gpio().enable(pin_id)
    return ("", 204)


@api.route("/gpios/output/<int:pin_id>/off", methods=["POST"])
def off(pin_id):
    if not peripheral_service:
        abort(500)

    peripheral_service.gpio().disable(pin_id)
    return ("", 204)


@api.route("/gpios/output/<int:pin_id>/toggle", methods=["POST"])
def toggle(pin_id):
    if not peripheral_service:
        abort(500)

    peripheral_service.gpio().toggle(pin_id)
    return ("", 204)


@api.route("/sensors/power")
def power_status():
    if not peripheral_service:
        abort(500)

    if not peripheral_service.power_sensor():
        abort(404)

    return jsonify(peripheral_service.power_sensor().status())


@api.route("/sensors/temperature")
def temperature_status():
    if not peripheral_service:
        abort(500)

    if not peripheral_service.temperature_sensor():
        abort(404)

    return jsonify(peripheral_service.temperature_sensor().status())


@api.route("/sensors/humidity")
def humidity_status():
    if not peripheral_service:
        abort(500)

    if not peripheral_service.humidity_sensor():
        abort(404)

    return jsonify(peripheral_service.humidity_sensor().status())
