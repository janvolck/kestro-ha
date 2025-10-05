#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <ArduinoJson.h>
#include <LittleFS.h>

// Config structure
struct Config {
    String wifi_ssid;
    String wifi_password;
    String hostname;
} config;

// Define LED pins array
const int NUM_LEDS = 9;
const int LED_PINS[NUM_LEDS] = {D0, D1, D2, D3, D4, D5, D6, D7, D8};
const int DELAY_MS = 100;  // Delay between steps

bool loadConfig() {
    if (!LittleFS.begin()) {
        return false;
    }

    File configFile = LittleFS.open("/config.json", "r");
    if (!configFile) {
        return false;
    }

    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, configFile);
    configFile.close();

    if (error) {
        return false;
    }

    config.wifi_ssid = doc["wifi"]["ssid"].as<String>();
    config.wifi_password = doc["wifi"]["password"].as<String>();
    config.hostname = doc["device"]["hostname"].as<String>();

    return true;
}

void setupOTA() {
    ArduinoOTA.setHostname(config.hostname.c_str());
    
    ArduinoOTA.onStart([]() {
        for (int i = 0; i < NUM_LEDS; i++) {
            digitalWrite(LED_PINS[i], LOW);
        }
    });
    
    ArduinoOTA.begin();
}

void setup() {
    Serial.begin(115200);  // Add this at the start of setup()
    Serial.println("\nStarting up...");
    
    // Initialize all LED pins as outputs
    for (int i = 0; i < NUM_LEDS; i++) {
        pinMode(LED_PINS[i], OUTPUT);
        digitalWrite(LED_PINS[i], LOW);
    }

    if (!loadConfig()) {
        Serial.println("Failed to load config");  // Add debug output
        // Configuration loading failed, blink error pattern
        while (true) {
            digitalWrite(LED_PINS[0], HIGH);
            delay(100);
            digitalWrite(LED_PINS[0], LOW);
            delay(100);
        }
    }
    Serial.println("Config loaded successfully");  // Add debug output

    // Connect to WiFi
    WiFi.mode(WIFI_STA);
    WiFi.begin(config.wifi_ssid.c_str(), config.wifi_password.c_str());
    while (WiFi.waitForConnectResult() != WL_CONNECTED) {
        delay(5000);
        ESP.restart();
    }

    setupOTA();
}

void loop() {
    ArduinoOTA.handle();  // Handle OTA updates
  
    // Forward running light
    for (int i = 0; i < NUM_LEDS; i++) {
        digitalWrite(LED_PINS[i], HIGH);
        delay(DELAY_MS);
        digitalWrite(LED_PINS[i], LOW);
    }
  
    // Backward running light
    for (int i = NUM_LEDS - 2; i >= 0; i--) {
        digitalWrite(LED_PINS[i], HIGH);
        delay(DELAY_MS);
        digitalWrite(LED_PINS[i], LOW);
    }
}