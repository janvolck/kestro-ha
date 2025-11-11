#ifndef FAN_CONTROLLER_H
#define FAN_CONTROLLER_H

#include <Arduino.h>

class FanController
{
public:
    // Fan configuration
    static const int FAN_POWER_PIN = 3;
    static const int FAN_GROUPS = 2;
    static const int FAN_PWM_PINS[FAN_GROUPS];
    static const int FAN_TACH_PINS[FAN_GROUPS];

public:
    FanController();
    void begin();
    void update();
    void setGroupSpeed(int group, int speed);
    int getGroupSpeed(int group);
    unsigned long getGroupRPM(int group);
    void enablePower();
    void disablePower();
    bool isPowerEnabled() const;

private:
    int _groupSpeed[2];
    bool _powerEnabled;

    volatile unsigned long *_lastPulse;
    volatile unsigned long *_pulseCount;
    unsigned long *_rpm;

    static void handleInterrupt(void *arg);
    unsigned long lastRpmUpdate;
    static const unsigned long RPM_UPDATE_INTERVAL = 1000;
};

#endif