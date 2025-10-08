#ifndef ADS1115_CONTROLLER_H
#define ADS1115_CONTROLLER_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>

class ADS1115Controller
{
public:
    ADS1115Controller();
    bool begin(uint8_t i2cAddress = 0x48);

    float readVoltage(uint8_t channel);
    int16_t readRaw(uint8_t channel);

    void setGain(adsGain_t gain);
    adsGain_t getGain() const;

private:
    void _updateVoltageConversion();

private:
    Adafruit_ADS1115 _ads;
    adsGain_t _gain;
    float _voltageConversion;
};

#endif