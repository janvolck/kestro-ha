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
    boolean enable_ads1115;
    struct
    {
        String ssid;
        String password;
    } wifi;
    MqttController::Config mqtt;
} config;

// Controller pointers
FanController *fanController;
ADS1115Controller *adc;
MqttController *mqttController;

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
    config.enable_ads1115 = doc["device"]["enable_ads1115"] | true;

    config.wifi.ssid = doc["wifi"]["ssid"].as<String>();
    config.wifi.password = doc["wifi"]["password"].as<String>();

    config.mqtt.server = doc["mqtt"]["server"].as<String>();
    config.mqtt.port = doc["mqtt"]["port"] | 1883;
    config.mqtt.username = doc["mqtt"]["username"].as<String>();
    config.mqtt.password = doc["mqtt"]["password"].as<String>();
    config.mqtt.client_id = doc["mqtt"]["client_id"] | config.hostname;
    config.mqtt.topic_prefix = doc["mqtt"]["topic_prefix"] | "kestro";

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
        if (mqttController)
            mqttController->stop(); });

    ArduinoOTA.begin();
}

// Named callback functions (prefer methods over lambdas)
void mqttPowerCallback(bool on)
{
    if (on)
        fanController->enablePower();
    else
        fanController->disablePower();
}

void mqttGroupCallback(int groupIdx, int speed)
{
    if (groupIdx >= 0 && groupIdx <= 1 && speed >= 0 && speed <= 100)
    {
        fanController->setGroupSpeed(groupIdx, speed);
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

    // Initialize ADC
    adc = new ADS1115Controller();
    if (config.enable_ads1115)
    {
        Serial.println("Connecting to ADS1115...");
        if (!adc->begin())
        {
            Serial.println("Failed to initialize ADS1115");
            while (true)
            {
                delay(1000);
            }
        }
        adc->setGain(GAIN_TWOTHIRDS); // For reading 0-6.144V
    }

    Serial.println("Connecting to Wifi " + config.wifi.ssid + "(" + config.wifi.password + ")" + "...");

    WiFi.mode(WIFI_STA);
    WiFi.begin(config.wifi.ssid.c_str(), config.wifi.password.c_str());
    while (WiFi.waitForConnectResult() != WL_CONNECTED)
    {

        Serial.println("Failed to connect to WiFi(" + String(WiFi.status()) + "), retrying...");
        delay(5000);
        ESP.restart();
    }

    // Setup OTA after WiFi is connected
    setupOTA();
    Serial.println("OTA configured");
    Serial.println("Connecting to MQTT " + config.mqtt.server + "...");

    Serial.println("Connecting to FanController...");
    fanController = new FanController();
    fanController->begin();

    // Setup MQTT
    MqttController::Config mqttConfig = {
        config.mqtt.server,
        config.mqtt.port,
        config.mqtt.username,
        config.mqtt.password,
        config.mqtt.client_id,
        config.mqtt.topic_prefix};
    mqttController = new MqttController(mqttConfig);
    // register named callback functions so main doesn't need MQTT logic
    mqttController->begin(mqttPowerCallback, mqttGroupCallback);

    Serial.println("Setup done");
}

void loop()
{
    // check for new updates
    ArduinoOTA.handle();

    mqttController->update();
    fanController->update();

    static unsigned long lastUpdate = 0;
    if (millis() - lastUpdate >= 10000)
    {
        // Publish fan states
        for (int i = 0; i < FanController::FAN_GROUPS; ++i)
        {
            unsigned long speed = fanController->getGroupSpeed(i);
            unsigned long rpm = fanController->getGroupRPM(i);

            mqttController->setFanState(i, speed);
            mqttController->setFanRpm(i, rpm);

            Serial.printf("Fan %d Speed: %lu RPM: %lu\n", i, speed, rpm);
        }

        // Publish waterlevel values via MQTT controller
        if (config.enable_ads1115)
        {
            float voltage = adc->readVoltage(0);
            mqttController->setWaterLevel(0, voltage);
            Serial.printf("Water Level: %.3f\n", voltage);
        }

        lastUpdate = millis();
    }
}