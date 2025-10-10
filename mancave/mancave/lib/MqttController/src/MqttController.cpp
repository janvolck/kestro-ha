#include "MqttController.h"
#include <ArduinoJson.h>

MqttController::MqttController(Config config)
    : _config(config), mqtt(_wifiClient)
{
    // start with empty last rpm vector; will resize on first setFanRpm call
    _lastFanRpms = std::vector<unsigned long>();
    _lastAdcValues = std::vector<float>();
}

void MqttController::begin(PowerCallback powerCallback, GroupSpeedCallback groupCallback)
{
    _powerCallback = powerCallback;
    _groupCallback = groupCallback;
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

    // Prepare topic strings
    String prefix = _config.topic_prefix + "/";
    String statusTopic = prefix + "status";

    // Set Last Will message so broker will mark us offline if we disconnect unexpectedly.
    // willTopic, willQos=1, willRetain=true, willMessage="offline"
    if (mqtt.connect(_config.client_id.c_str(),
                     _config.username.c_str(),
                     _config.password.c_str(),
                     statusTopic.c_str(), 1, true, "offline"))
    {
        Serial.println("connected");

        // Subscribe to control topics
        mqtt.subscribe((prefix + "fan/power").c_str());
        mqtt.subscribe((prefix + "fan/group/+").c_str());

        // Publish initial states
        // Publish retained birth message so other clients know we're online
        publish("status", "online", true);

        // Publish Home Assistant MQTT Discovery payload for a simple fan entity
        // Topic: homeassistant/fan/<unique_id>/config
        // Use retained=true so Home Assistant picks it up
        {
            String uniqueId = _config.client_id + String("_fan");
            String discoveryTopic = String("homeassistant/fan/") + uniqueId + "/config";

            // Build discovery JSON using ArduinoJson
            StaticJsonDocument<512> doc;
            doc["name"] = _config.client_id + String(" Fan");
            doc["unique_id"] = uniqueId;
            doc["command_topic"] = _config.topic_prefix + String("/fan/power");
            doc["state_topic"] = _config.topic_prefix + String("/fan/power");
            doc["availability_topic"] = _config.topic_prefix + String("/status");
            doc["payload_on"] = "on";
            doc["payload_off"] = "off";

            JsonObject device = doc.createNestedObject("device");
            device.createNestedArray("identifiers").add(_config.client_id);
            device["name"] = _config.client_id;
            device["manufacturer"] = "kestro";
            device["model"] = "mancave";

            String payload;
            serializeJson(doc, payload);

            mqtt.publish(discoveryTopic.c_str(), payload.c_str(), true);
        }
        return true;
    }

    Serial.println("failed");
    return false;
}

void MqttController::stop()
{
    // Publish retained offline status and disconnect cleanly
    publish("status", "offline", true);
    if (mqtt.connected())
    {
        mqtt.disconnect();
    }
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

    // Dispatch to appropriate callbacks based on topic
    if (topicStr == "fan/power")
    {
        if (mqtt->_powerCallback)
        {
            bool on = (payloadStr == "ON" || payloadStr == "on" || payloadStr == "1");
            mqtt->_powerCallback(on);
        }
    }
    else if (topicStr.startsWith("fan/group/"))
    {
        if (mqtt->_groupCallback)
        {
            // extract group index
            String idxStr = topicStr.substring(String("fan/group/").length());
            int groupIdx = idxStr.toInt();
            int speed = payloadStr.toInt();
            mqtt->_groupCallback(groupIdx, speed);
        }
    }
}

void MqttController::setFanRpm(int index, unsigned long rpm)
{
    if (index < 0)
        return;

    if ((int)_lastFanRpms.size() <= index)
    {
        // resize and initialize to zero
        _lastFanRpms.resize(index + 1, 0);
    }

    if (_lastFanRpms[index] != rpm)
    {
        char subtopic[32];
        char value[32];
        snprintf(subtopic, sizeof(subtopic), "fan/%d/rpm", index);
        snprintf(value, sizeof(value), "%lu", rpm);
        publish(subtopic, value);
        _lastFanRpms[index] = rpm;
    }
}

void MqttController::setAdc(int channel, float voltage)
{
    if (channel < 0)
        return;

    if ((int)_lastAdcValues.size() <= channel)
    {
        _lastAdcValues.resize(channel + 1, 0.0f);
    }

    if (fabs(_lastAdcValues[channel] - voltage) > 0.01f)
    {
        char subtopic[20], value[16];
        snprintf(subtopic, sizeof(subtopic), "adc/%d", channel);
        snprintf(value, sizeof(value), "%.3f", voltage);
        publish(subtopic, value);
        _lastAdcValues[channel] = voltage;
    }
}