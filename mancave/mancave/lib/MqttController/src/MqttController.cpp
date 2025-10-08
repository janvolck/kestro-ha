#include "MqttController.h"

MqttController::MqttController(Config config)
    : _config(config), mqtt(_wifiClient)
{
}

void MqttController::begin(MessageCallback callback)
{
    _callback = callback;
    mqtt.setServer(_config.server.c_str(), _config.port);
    mqtt.setCallback([this](char *topic, byte *payload, unsigned int length)
                     { mqttCallback(topic, payload, length, this); });
}

void MqttController::update()
{
    if (!mqtt.connected())
    {
        reconnect();
    }
    mqtt.loop();
}

void MqttController::publish(const char *subtopic, const char *value, bool retained)
{
    String topic = _config.topic_prefix + "/" + subtopic;
    mqtt.publish(topic.c_str(), value, retained);
}

bool MqttController::reconnect()
{
    if (mqtt.connected())
        return true;

    Serial.print("Connecting to MQTT... ");

    if (mqtt.connect(_config.client_id.c_str(),
                     _config.username.c_str(),
                     _config.password.c_str()))
    {
        Serial.println("connected");

        // Subscribe to control topics
        String prefix = _config.topic_prefix + "/";
        mqtt.subscribe((prefix + "fan/power").c_str());
        mqtt.subscribe((prefix + "fan/group/+").c_str());

        // Publish initial states
        publish("status", "online");
        return true;
    }

    Serial.println("failed");
    return false;
}

void MqttController::mqttCallback(char *topic, byte *payload, unsigned int length, void *controller)
{
    MqttController *mqtt = (MqttController *)controller;

    // Create a null-terminated string from payload
    char message[length + 1];
    memcpy(message, payload, length);
    message[length] = '\0';

    String topicStr = String(topic);
    String payloadStr = String(message);

    // Remove prefix from topic
    if (topicStr.startsWith(mqtt->_config.topic_prefix))
    {
        topicStr = topicStr.substring(mqtt->_config.topic_prefix.length() + 1);
    }

    if (mqtt->_callback)
    {
        mqtt->_callback(topicStr, payloadStr);
    }
}