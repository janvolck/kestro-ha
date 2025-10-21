#ifndef MQTT_CONTROLLER_H
#define MQTT_CONTROLLER_H

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <functional>
#include <vector>
#include <LittleFS.h>

class MqttController
{
public:
    struct Config
    {
        String server;
        int port;
        String username;
        String password;
        String client_id;
        String topic_prefix;
    };

    typedef std::function<void(const String &, const String &)> MessageCallback;
    typedef std::function<void(bool)> PowerCallback;
    typedef std::function<void(int, int)> GroupSpeedCallback;

    MqttController(Config config);
    void begin(PowerCallback powerCallback, GroupSpeedCallback groupCallback);
    void update();
    void publish(const char *subtopic, const char *value, bool retained = true);
    void setFanRpm(int index, unsigned long rpm);
    void setAdc(int channel, float voltage);
    void stop();
    bool isConnected() { return mqtt.connected(); }
    void publishBirthMessage();

private:
    Config _config;
    WiFiClient _wifiClient;
    PubSubClient mqtt;
    MessageCallback _callback;
    PowerCallback _powerCallback;
    GroupSpeedCallback _groupCallback;
    std::vector<unsigned long> _lastFanRpms;
    std::vector<float> _lastAdcValues;

    bool reconnect();
    static void mqttCallback(char *topic, byte *payload, unsigned int length, void *controller);
};

#endif