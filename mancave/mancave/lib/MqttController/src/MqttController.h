#ifndef MQTT_CONTROLLER_H
#define MQTT_CONTROLLER_H

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <functional>

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

    MqttController(Config config);
    void begin(MessageCallback callback);
    void update();
    void publish(const char *subtopic, const char *value, bool retained = true);
    bool isConnected() { return mqtt.connected(); }

private:
    Config _config;
    WiFiClient _wifiClient;
    PubSubClient mqtt;
    MessageCallback _callback;

    bool reconnect();
    static void mqttCallback(char *topic, byte *payload, unsigned int length, void *controller);
};

#endif