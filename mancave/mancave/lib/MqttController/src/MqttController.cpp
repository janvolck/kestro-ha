#include "MqttController.h"
#include <ArduinoJson.h>
#include <LittleFS.h>

MqttController::MqttController(Config config)
    : _config(config), mqtt(_wifiClient)
{
    // start with empty last rpm vector; will resize on first setFanRpm call
    _lastFanRpms = std::vector<unsigned long>();
    _lastAdcValues = std::vector<float>();

    // Increase MQTT buffer size for large birth messages
    mqtt.setBufferSize(8192); // Increase from default 256 bytes to 8KB
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
    String availabilityTopic = prefix + "ventilation/availability";

    // Set Last Will message so broker will mark us offline if we disconnect unexpectedly.
    // willTopic, willQos=1, willRetain=true, willMessage="offline"
    if (mqtt.connect(_config.client_id.c_str(),
                     _config.username.c_str(),
                     _config.password.c_str(),
                     availabilityTopic.c_str(), 1, true, "offline"))
    {
        Serial.println("connected");

        // Subscribe to control topics
        mqtt.subscribe((prefix + "ventilation/control").c_str());
        mqtt.subscribe((prefix + "ventilation/group/#").c_str());

        // Publish initial states
        // Publish retained birth message so other clients know we're online
        publish("ventilation/availability", "online", true);

        // Publish Home Assistant MQTT Discovery payloads from birth.json
        publishBirthMessage();
        return true;
    }

    Serial.println("failed");
    return false;
}

void MqttController::stop()
{
    // Publish retained offline status and disconnect cleanly
    publish("ventilation/availability", "offline", true);
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

    Serial.print("Received message on topic: ");
    Serial.println(topicStr);
    Serial.print("Payload: ");
    Serial.println(payloadStr);

    // Remove prefix from topic
    if (topicStr.startsWith(mqtt->_config.topic_prefix))
    {
        topicStr = topicStr.substring(mqtt->_config.topic_prefix.length() + 1);
    }

    // Dispatch to appropriate callbacks based on topic
    if (topicStr == "ventilation/control")
    {
        if (mqtt->_powerCallback)
        {
            bool on = (payloadStr == "ON" || payloadStr == "on" || payloadStr == "1");
            mqtt->_powerCallback(on);
            mqtt->publish("ventilation/state", payloadStr.c_str(), false);
        }
    }
    else if (topicStr.startsWith("ventilation/group/"))
    {
        if (mqtt->_groupCallback)
        {
            // Parse pattern: ventilation/group/X/speed/set using sscanf
            int groupIdx;
            if (sscanf(topicStr.c_str(), "ventilation/group/%d/speed/set", &groupIdx) == 1)
            {
                int speed = payloadStr.toInt();
                mqtt->_groupCallback(groupIdx - 1, speed);
            }
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
        char subtopic[64];
        char value[32];
        snprintf(subtopic, sizeof(subtopic), "ventilation/group/%d/speed/state", index + 1);
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

void MqttController::publishBirthMessage()
{
    // Read birth.json from LittleFS
    if (!LittleFS.exists("/birth.json"))
    {
        Serial.println("ERROR: birth.json not found, skipping birth message");
        return;
    }

    File file = LittleFS.open("/birth.json", "r");
    if (!file)
    {
        Serial.println("ERROR: Could not open birth.json");
        return;
    }

    // Parse the birth.json file
    DynamicJsonDocument birthDoc(4096); // Adjust size as needed
    DeserializationError error = deserializeJson(birthDoc, file);
    file.close();

    if (error)
    {
        Serial.print("ERROR: parsing birth.json: ");
        Serial.println(error.c_str());
        return;
    }

    // Replace template variables in the entire birth document
    String birthStr;
    serializeJson(birthDoc, birthStr);

    birthStr.replace("${topic_prefix}", _config.topic_prefix);
    birthStr.replace("${client_id}", _config.client_id);

    // Build birth message topic: homeassistant/device/<client_id>/config
    String birthTopic = String("homeassistant/device/") + _config.client_id + "/config";

    // Check if MQTT is connected before publishing
    if (!mqtt.connected())
    {
        Serial.println("ERROR: MQTT not connected, cannot publish birth message");
        return;
    }

    // Check if the message fits in the MQTT buffer
    if (birthStr.length() > mqtt.getBufferSize())
    {
        Serial.println("ERROR: Birth message too large for MQTT buffer!");
        Serial.println("Consider increasing MQTT_MAX_PACKET_SIZE or splitting the message");
        return;
    }

    // Publish the complete birth message
    bool publishResult = mqtt.publish(birthTopic.c_str(), birthStr.c_str(), true);
    if (publishResult)
    {
        Serial.print("SUCCESS: Published birth message to: ");
        Serial.println(birthTopic);
    }
    else
    {
        Serial.println("ERROR: Failed to publish birth message - message may be too large or network issue");
    }
}
