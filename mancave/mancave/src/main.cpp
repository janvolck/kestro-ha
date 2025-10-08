#include <PubSubClient.h> // Add this include at the top
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ArduinoJson.h>
#include <LittleFS.h>
#include <Wire.h>
#include "FanController.h"
#include "ADS1115Controller.h"
#include "MqttController.h"

// Config structure
struct Config
{
    String hostname;
    struct
    {
        String ssid;
        String password;
    } wifi;
    MqttController::Config mqtt;
} config;

// Fan configuration
const int NUM_FANS = 6;
const int FANS_PER_GROUP = 3;

// PWM pins for fan control (GPIO numbers) - One pin per group
const int FAN_PWM_PINS[2] = {14, 12}; // D5, D6 (one pin per group)

// Tach pins for RPM reading (GPIO numbers)
const int FAN_TACH_PINS[NUM_FANS] = {16, 0, 2, 3, 1, 10}; // D0, D3, D4, RX, TX, SD3

// Power pin for fan control
const int FAN_POWER_PIN = 9; // GPIO9 (SD2)

// Controller pointers
FanController *fanController;
ADS1115Controller *adc;
MqttController *mqttController;

// Last published values
struct
{
    unsigned long rpm[NUM_FANS] = {0};
    float adc[4] = {0};
} lastPublished;

bool loadConfig()
{
    if (!LittleFS.begin())
    {
        return false;
    }

    File configFile = LittleFS.open("/config.json", "r");
    if (!configFile)
    {
        return false;
    }

    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, configFile);
    configFile.close();

    if (error)
    {
        return false;
    }

    config.hostname = doc["device"]["hostname"].as<String>();

    config.wifi.ssid = doc["wifi"]["ssid"].as<String>();
    config.wifi.password = doc["wifi"]["password"].as<String>();

    config.mqtt.server = doc["mqtt"]["server"].as<String>();
    config.mqtt.port = doc["mqtt"]["port"] | 1883;
    config.mqtt.username = doc["mqtt"]["username"].as<String>();
    config.mqtt.password = doc["mqtt"]["password"].as<String>();
    config.mqtt.client_id = doc["mqtt"]["client_id"] | config.hostname;
    config.mqtt.topic_prefix = doc["mqtt"]["topic_prefix"] | "mancave";

    return true;
}

void setupOTA()
{
    ArduinoOTA.setHostname(config.hostname.c_str());

    // Stop fans and set MQTT status to offline on OTA(Over-The-Air update) start
    ArduinoOTA.onStart([]()
                       {
        Serial.println("OTA update starting...");
        // Safely shutdown systems before update
        fanController->disablePower();
        mqttController->publish("status", "offline", true); });

    ArduinoOTA.begin();
}

void handleMqttMessage(const String &topic, const String &payload)
{
    if (topic == "fan/power")
    {
        if (payload == "ON")
            fanController->enablePower();
        else if (payload == "OFF")
            fanController->disablePower();
    }
    else if (topic == "fan/group/0")
    {
        int speed = payload.toInt();
        if (speed >= 0 && speed <= 100)
            fanController->setGroupSpeed(0, speed);
    }
    else if (topic == "fan/group/1")
    {
        int speed = payload.toInt();
        if (speed >= 0 && speed <= 100)
            fanController->setGroupSpeed(1, speed);
    }
}

void publishFanRPM(int fanIndex, unsigned long rpm)
{
    if (lastPublished.rpm[fanIndex] != rpm)
    {
        char subtopic[20], value[10];
        snprintf(subtopic, sizeof(subtopic), "fan/%d/rpm", fanIndex);
        snprintf(value, sizeof(value), "%lu", rpm);
        mqttController->publish(subtopic, value);
        lastPublished.rpm[fanIndex] = rpm;
    }
}

void publishADC(int channel, float voltage)
{
    if (abs(lastPublished.adc[channel] - voltage) > 0.01)
    {
        char subtopic[20], value[10];
        snprintf(subtopic, sizeof(subtopic), "adc/%d", channel);
        snprintf(value, sizeof(value), "%.3f", voltage);
        mqttController->publish(subtopic, value);
        lastPublished.adc[channel] = voltage;
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.println("\nStarting up...");

    Wire.begin(); // Initialize I2C

    if (!loadConfig())
    {
        Serial.println("Failed to load config");
        while (true)
        {
            delay(1000);
        }
    }

    Serial.println("Connecting to ADS1115...");
    // Initialize ADC
    adc = new ADS1115Controller();
    if (!adc->begin())
    {
        Serial.println("Failed to initialize ADS1115");
        while (true)
        {
            delay(1000);
        }
    }
    adc->setGain(GAIN_TWOTHIRDS); // For reading 0-6.144V

    Serial.println("Connecting to FanController...");

    // Initialize Fan Controller
    fanController = new FanController(FAN_PWM_PINS, FAN_TACH_PINS, NUM_FANS, FANS_PER_GROUP, FAN_POWER_PIN);

    Serial.println("Connecting to Wifi " + config.wifi.ssid + "(" + config.wifi.password + ")" + "...");

    WiFi.mode(WIFI_STA);
    WiFi.begin(config.wifi.ssid.c_str(), config.wifi.password.c_str());
    while (WiFi.waitForConnectResult() != WL_CONNECTED)
    {

        Serial.println("Failed to connect to WiFi(" + String(WiFi.status()) + "), retrying...");
        delay(5000);
        ESP.restart();
    }

    Serial.println("Connecting to MQTT " + config.mqtt.server + "...");
    // Setup MQTT
    MqttController::Config mqttConfig = {
        config.mqtt.server,
        config.mqtt.port,
        config.mqtt.username,
        config.mqtt.password,
        config.mqtt.client_id,
        config.mqtt.topic_prefix};
   mqttController = new MqttController(mqttConfig);
   mqttController->begin(handleMqttMessage);

    Serial.println("Setup done");
}

void loop()
{
    // check for new updates
    ArduinoOTA.handle();

    mqttController->update();
    fanController->update();

    static unsigned long lastUpdate = 0;
    if (millis() - lastUpdate >= 5000)
    {
        // Publish fan RPM values
        for (int i = 0; i < NUM_FANS; i++)
        {
            unsigned long rpm = fanController->getFanRPM(i);
            publishFanRPM(i, rpm);
            Serial.printf("Fan %d RPM: %lu\n", i, rpm);
        }

        // Publish ADC values
        for (int i = 0; i < 4; i++)
        {
            float voltage = adc->readVoltage(i);
            publishADC(i, voltage);
            Serial.printf("ADC Channel %d: %.3fV\n", i, voltage);
        }

        lastUpdate = millis();
    }
}