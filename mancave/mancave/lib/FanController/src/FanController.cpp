#include "FanController.h"

const int FanController::FAN_PWM_PINS[FAN_GROUPS] = {14, 12};
const int FanController::FAN_TACH_PINS[FAN_GROUPS] = {13, 15};

FanController::FanController()
    : _groupSpeed(), _powerEnabled(false)
{

    _lastPulse = new volatile unsigned long[FAN_GROUPS]();
    _pulseCount = new volatile unsigned long[FAN_GROUPS]();
    _rpm = new unsigned long[FAN_GROUPS]();

    _groupSpeed[0] = 0;
    _groupSpeed[1] = 0;
}

void FanController::begin()
{
    // Initialize power control pin
    Serial.println("Fan power pin " + String(FAN_POWER_PIN) + " set to OUTPUT");
    pinMode(FAN_POWER_PIN, OUTPUT);
    disablePower(); // Start with fans off

    // Initialize PWM groups
    for (int i = 0; i < FAN_GROUPS; i++)
    {
        Serial.println("Fan Group " + String(i + 1) + " PWM pin " + String(FAN_PWM_PINS[i]) + " set to OUTPUT");

        pinMode(FAN_PWM_PINS[i], OUTPUT);
        analogWrite(FAN_PWM_PINS[i], map(_groupSpeed[i], 0, 100, 0, 1023));
    }

    // Initialize RPM pins
    for (int i = 0; i < FAN_GROUPS; i++)
    {
        // Setup interrupt pins for RPM reading
        Serial.println("Fan tach " + String(i + 1) + " pin " + String(FAN_TACH_PINS[i]) + " set to INPUT_PULLUP");
        pinMode(FAN_TACH_PINS[i], INPUT_PULLUP);
        attachInterruptArg(digitalPinToInterrupt(FAN_TACH_PINS[i]),
                           FanController::handleInterrupt,
                           (void *)&_pulseCount[i],
                           FALLING);
    }
}

void FanController::enablePower()
{
    digitalWrite(FAN_POWER_PIN, HIGH);
    _powerEnabled = true;
    
    setGroupSpeed(0, 50);
    setGroupSpeed(1, 50);
    
    Serial.println("Fan power enabled (pin " + String(FAN_POWER_PIN) + " HIGH)");
}

void FanController::disablePower()
{
    digitalWrite(FAN_POWER_PIN, LOW);

    setGroupSpeed(0, 0);
    setGroupSpeed(1, 0);

    _powerEnabled = false;
    Serial.println("Fan power disabled (pin " + String(FAN_POWER_PIN) + " LOW)");
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
        for (int i = 0; i < FAN_GROUPS; i++)
        {
            // Calculate RPM (pulses * 60 seconds / 2 pulses per revolution)
            _rpm[i] = (_pulseCount[i] * 60) / 2;
            _pulseCount[i] = 0;

            // Check if fan is stopped (no pulses for 2 seconds)
            if (now - _lastPulse[i] > 2000)
            {
                _rpm[i] = 0;
            }

            // dummy RPM assignment for testing
            _rpm[i] = _groupSpeed[i];

            // Debug output
            Serial.println("Fan Group " + String(i + 1) + " RPM: " + String(_rpm[i]));
        }
        lastRpmUpdate = now;
    }
}

void FanController::setGroupSpeed(int group, int speed)
{
    if (_powerEnabled && group >= 0 && group < FAN_GROUPS)
    {
        _groupSpeed[group] = speed;
        analogWrite(FAN_PWM_PINS[group], map(speed, 0, 100, 0, 1023));

        Serial.println("Fan Group " + String(group + 1) + " speed set to " + String(speed) + "%");
    }
}

unsigned long FanController::getGroupRPM(int group)
{
    if (group >= 0 && group < FAN_GROUPS)
    {
        return _rpm[group];
    }
    return 0;
}

int FanController::getGroupSpeed(int group)
{
    if (group >= 0 && group < FAN_GROUPS)
    {
        return _groupSpeed[group];
    }
    return 0;
}