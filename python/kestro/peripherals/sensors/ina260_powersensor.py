import pigpio
from .base_powersensor import BasePowerSensor


class Ina260PowerSensor(BasePowerSensor):

    _INA260_CURRENT_ADDR = 0x01
    _INA260_BUS_VOLTAGE_ADDR = 0x02
    _INA260_BUS_VOLTAGE_LSB = 1.25  # mV
    _INA260_CURRENT_LSB = 1.25  # mA

    def __init__(self, host: str = None, address: int = 0x40):
        super().__init__()

        if host:
            self.pi = pigpio.pi(host=host)
        else:
            self.pi = pigpio.pi()

        self._i2c_handle = self.pi.i2c_open(1, address)
        self.voltage = 0
        self.current = 0

    def twos_compliment_to_int(self, val, len):
        # Convert twos compliment to integer
        if (val & (1 << len - 1)):
            val = val - (1 << len)
        return val

    def get_voltage(self):
        size, data = self.pi.i2c_read_i2c_block_data(
            self._i2c_handle, self._INA260_BUS_VOLTAGE_ADDR, 2)
        word_data = data[0] * 256 + data[1]
        vbus = float(word_data) / 1000.0 * self._INA260_BUS_VOLTAGE_LSB
        return vbus

    def get_current(self):
        size, data = self.pi.i2c_read_i2c_block_data(
            self._i2c_handle, self._INA260_CURRENT_ADDR, 2)
        word_data = data[0] * 256 + data[1]

        current_twos_compliment = word_data
        current_sign_bit = current_twos_compliment >> 15

        if (current_sign_bit == 1):
            current = float(self.twos_compliment_to_int(
                current_twos_compliment, 16)) / 1000.0 * self._INA260_CURRENT_LSB
        else:
            current = float(current_twos_compliment) / \
                1000.0 * self._INA260_CURRENT_LSB
        return current

    def refresh(self):
        self.voltage = self.get_voltage()
        self.current = self.get_current()
