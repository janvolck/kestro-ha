#include "FanController.h"

const int FanController::FAN_PWM_PINS[FAN_GROUPS] = {12, 14};
const int FanController::FAN_TACH_PINS[FAN_GROUPS] = {15, 13};

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

    // Configure PWM frequency and resolution for ESP8266
    // Set PWM frequency to 25kHz (good for fans)
    analogWriteFreq(25000);
    // Set PWM resolution to 10 bits (0-1023)
    analogWriteResolution(10);

    // Initialize PWM groups
    for (int i = 0; i < FAN_GROUPS; i++)
    {
        Serial.println("Fan Group " + String(i + 1) + " PWM pin " + String(FAN_PWM_PINS[i]) + " set to OUTPUT");

        pinMode(FAN_PWM_PINS[i], OUTPUT);
        // Start with PWM off (0 duty cycle)
        analogWrite(FAN_PWM_PINS[i], 0);
        Serial.println("Initial PWM value for pin " + String(FAN_PWM_PINS[i]) + ": 0");
    }

    // Initialize RPM pins
    for (int i = 0; i < FAN_GROUPS; i++)
    {
        // Setup interrupt pins for RPM reading
        Serial.println("Fan tach " + String(i + 1) + " pin " + String(FAN_TACH_PINS[i]) + " set to INPUT");
        pinMode(FAN_TACH_PINS[i], INPUT);
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

    Serial.println("Fan power enabled (pin " + String(FAN_POWER_PIN) + " HIGH)");

    // Apply current speed settings now that power is enabled
    for (int i = 0; i < FAN_GROUPS; i++)
    {
        if (_groupSpeed[i] > 0)
        {
            int pwmValue = map(_groupSpeed[i], 0, 100, 0, 1023);
            analogWrite(FAN_PWM_PINS[i], pwmValue);
            Serial.println("Applying saved speed for Group " + String(i + 1) + ": " + String(_groupSpeed[i]) + "% (PWM: " + String(pwmValue) + ")");
        }
    }

    // Set default speeds if not already set
    if (_groupSpeed[0] == 0)
        setGroupSpeed(0, 50);
    if (_groupSpeed[1] == 0)
        setGroupSpeed(1, 50);
}

void FanController::disablePower()
{
    digitalWrite(FAN_POWER_PIN, LOW);
    _powerEnabled = false;

    // Turn off all PWM outputs
    for (int i = 0; i < FAN_GROUPS; i++)
    {
        analogWrite(FAN_PWM_PINS[i], 0);
        Serial.println("Fan Group " + String(i + 1) + " PWM set to 0 (power disabled)");
    }

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
    unsigned long interval = now - lastRpmUpdate;
    if (interval >= RPM_UPDATE_INTERVAL)
    {
        for (int i = 0; i < FAN_GROUPS; i++)
        {
            // anything under 10 pulses is likely noise
            if (_pulseCount[i] > 10)
            {
                _lastPulse[i] = now;

                // Calculate RPM (pulses * 60000 milliseconds / 2 pulses per interval)
                _rpm[i] = (_pulseCount[i] * 60000) / (2 * interval);
            }

            // reset the pulse count for the next interval
            _pulseCount[i] = 0;

            // Check if fan is stopped (no pulses for 2 seconds)
            if (now - _lastPulse[i] > 2000)
            {
                _rpm[i] = 0;
            }

            // Debug output
            Serial.println("Fan Group " + String(i + 1) + " RPM: " + String(_rpm[i]));
        }
        lastRpmUpdate = now;
    }
}

void FanController::setGroupSpeed(int group, int speed)
{
    if (group >= 0 && group < FAN_GROUPS)
    {
        _groupSpeed[group] = speed;

        // Calculate PWM value (0-1023 for 10-bit resolution)
        int pwmValue = map(speed, 0, 100, 0, 1023);

        // Only apply PWM if power is enabled AND speed > 0
        if (_powerEnabled && speed > 0)
        {
            analogWrite(FAN_PWM_PINS[group], pwmValue);
            Serial.println("Fan Group " + String(group + 1) + " speed set to " + String(speed) + "% (PWM: " + String(pwmValue) + ")");
        }
        else
        {
            // Turn off PWM when power disabled or speed is 0
            analogWrite(FAN_PWM_PINS[group], 0);
            Serial.println("Fan Group " + String(group + 1) + " PWM disabled (Power: " + String(_powerEnabled) + ", Speed: " + String(speed) + ")");
        }
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