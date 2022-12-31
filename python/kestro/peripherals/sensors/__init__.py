import platform
from .base_powersensor import BasePowerSensor

if 'raspberrypi' in platform.uname():
    from .ina260_powersensor import Ina260PowerSensor
    power_sensor = Ina260PowerSensor()
else:
    from .ina260_powersensor import Ina260PowerSensor
    power_sensor = Ina260PowerSensor(host='rpi4-k8s-master')
    # power_sensor = BasePowerSensor()
