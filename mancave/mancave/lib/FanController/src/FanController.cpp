#include "FanController.h"

FanController::FanController(const int *pwmPins, const int *tachPins, int numFans, int fansPerGroup, int powerPin)
    : _pwmPins(pwmPins), _tachPins(tachPins), _powerPin(powerPin), _numFans(numFans),
      _fansPerGroup(fansPerGroup), _powerEnabled(false)
{

    _lastPulse = new volatile unsigned long[numFans]();
    _pulseCount = new volatile unsigned long[numFans]();
    _rpm = new unsigned long[numFans]();

    _groupSpeed[0] = 50;
    _groupSpeed[1] = 50;
}

void FanController::begin()
{
    // Initialize power control pin
    pinMode(_powerPin, OUTPUT);
    disablePower(); // Start with fans off

    // Initialize PWM pins
    for (int i = 0; i < _numFans; i++)
    {
        pinMode(_pwmPins[i], OUTPUT);
        analogWrite(_pwmPins[i], map(_groupSpeed[i / _fansPerGroup], 0, 100, 0, 1023));

        // Setup interrupt pins for RPM reading
        pinMode(_tachPins[i], INPUT_PULLUP);
        attachInterruptArg(digitalPinToInterrupt(_tachPins[i]),
                           handleInterrupt,
                           (void *)&_pulseCount[i],
                           FALLING);
    }
}

void FanController::enablePower()
{
    digitalWrite(_powerPin, HIGH);
    _powerEnabled = true;
    Serial.println("Fan power enabled");
}

void FanController::disablePower()
{
    digitalWrite(_powerPin, LOW);
    _powerEnabled = false;
    Serial.println("Fan power disabled");
}

bool FanController::isPowerEnabled() const
{
    return _powerEnabled;
}

void ICACHE_RAM_ATTR FanController::handleInterrupt(void *arg)
{
    volatile unsigned long *count = (volatile unsigned long *)arg;
    (*count)++;
}

void FanController::update()
{
    unsigned long now = millis();
    if (now - lastRpmUpdate >= RPM_UPDATE_INTERVAL)
    {
        for (int i = 0; i < _numFans; i++)
        {
            // Calculate RPM (pulses * 60 seconds / 2 pulses per revolution)
            _rpm[i] = (_pulseCount[i] * 60) / 2;
            _pulseCount[i] = 0;

            // Check if fan is stopped (no pulses for 2 seconds)
            if (now - _lastPulse[i] > 2000)
            {
                _rpm[i] = 0;
            }
        }
        lastRpmUpdate = now;
    }
}

void FanController::setGroupSpeed(int group, int speed)
{
    if (group < 0 || group > 1 || speed < 0 || speed > 100)
        return;

    _groupSpeed[group] = speed;
    int startIdx = group * _fansPerGroup;
    int endIdx = startIdx + _fansPerGroup;

    for (int i = startIdx; i < endIdx; i++)
    {
        if (i < _numFans)
        {
            analogWrite(_pwmPins[i], map(speed, 0, 100, 0, 1023));
        }
    }
}

unsigned long FanController::getFanRPM(int fanIndex)
{
    if (fanIndex >= 0 && fanIndex < _numFans)
    {
        return _rpm[fanIndex];
    }
    return 0;
}

int FanController::getGroupSpeed(int group)
{
    if (group >= 0 && group < 2)
    {
        return _groupSpeed[group];
    }
    return 0;
}