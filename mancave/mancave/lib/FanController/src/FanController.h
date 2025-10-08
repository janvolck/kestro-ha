#ifndef FAN_CONTROLLER_H
#define FAN_CONTROLLER_H

#include <Arduino.h>

class FanController
{
public:
    FanController(const int *pwmPins, const int *tachPins, int numFans, int fansPerGroup, int powerPin);
    void begin();
    void update();
    void setGroupSpeed(int group, int speed);
    int getGroupSpeed(int group);
    unsigned long getFanRPM(int fanIndex);
    void enablePower();
    void disablePower();
    bool isPowerEnabled() const;

private:
    const int *_pwmPins;
    const int *_tachPins;
    const int _powerPin;
    int _numFans;
    int _fansPerGroup;
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