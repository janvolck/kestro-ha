#include "ADS1115Controller.h"

ADS1115Controller::ADS1115Controller()
{
    _gain = GAIN_TWOTHIRDS; // default gain
}

bool ADS1115Controller::begin(uint8_t i2cAddress)
{
    if (!_ads.begin(i2cAddress))
    {
        return false;
    }
    _ads.setGain(_gain);
    _updateVoltageConversion();
    return true;
}

float ADS1115Controller::readVoltage(uint8_t channel)
{
    return readRaw(channel) * _voltageConversion;
}

int16_t ADS1115Controller::readRaw(uint8_t channel)
{
    if (channel > 3)
        return 0;

    return _ads.readADC_SingleEnded(channel);
}

void ADS1115Controller::setGain(adsGain_t gain)
{
    _gain = gain;
    _ads.setGain(gain);
    _updateVoltageConversion();
}

adsGain_t ADS1115Controller::getGain() const
{
    return _gain;
}

void ADS1115Controller::_updateVoltageConversion()
{
    switch (_gain)
    {

    case GAIN_TWOTHIRDS: // ±6.144V
        _voltageConversion = 0.1875F;
        break;

    case GAIN_ONE: // ±4.096V
        _voltageConversion = 0.125F;
        break;

    case GAIN_TWO: // ±2.048V
        _voltageConversion = 0.0625F;
        break;

    case GAIN_FOUR: // ±1.024V
        _voltageConversion = 0.03125F;
        break;

    case GAIN_EIGHT: // ±0.512V
        _voltageConversion = 0.015625F;
        break;

    case GAIN_SIXTEEN: // ±0.256V
        _voltageConversion = 0.0078125F;
        break;

    default: // ±6.144V
        _voltageConversion = 0.1875F;
        break;
    }

    // Convert mV to V
    _voltageConversion = _voltageConversion / 1000.0F;
}
