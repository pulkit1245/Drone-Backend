/*
 * ESP32 Hybrid Trigger System
 * ===========================
 * 1. Button Logic: Counts presses on GPIO 12. Triggers if Count % 3 == 0.
 * 2. Server Logic: Polls server every 1 second. Triggers if server variable is true.
 * * Hardware Setup:
 * - Button: GPIO 12 (with pull-up resistor)
 * - LED: GPIO 2 (Built-in)
 * * Modified: 2025-12-11
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- CONFIGURATION ---
const char* ssid = "BIT-SIH";
const char* password = "bitsih@2025";
const char* serverUrl = "https://drone-backend-xg9s.onrender.com"; // Replace with your server IP
const char* deviceId = "esp32_001";

// Pins
const int BUTTON_PIN = 12;
const int LED_PIN = 2;

// State Variables
int buttonCount = 0;
bool buttonLastState = HIGH;

// Timing Variables
unsigned long lastSendTime = 0;
unsigned long lastCheckTime = 0; // For server polling

const unsigned long SEND_INTERVAL = 5000;   // Send count every 5s
const unsigned long CHECK_INTERVAL = 1000;  // Check server variable every 1s

// Debounce
const unsigned long DEBOUNCE_DELAY = 50;
unsigned long buttonLastDebounce = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n=== ESP32 Hybrid Monitor ===");
  
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  
  // Quick blink on startup
  digitalWrite(LED_PIN, HIGH); delay(200); digitalWrite(LED_PIN, LOW);
  
  connectWiFi();
}

void loop() {
  unsigned long currentTime = millis();
  
  // 1. Maintain WiFi Connection
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  
  // 2. Read Button (Local Trigger)
  readButton();
  
  // 3. Send Data Periodically (Every 5s)
  if (currentTime - lastSendTime >= SEND_INTERVAL) {
    sendDataToServer();
    lastSendTime = currentTime;
  }
  
  // 4. Check Server Variable (Remote Trigger) - Every 1s
  if (currentTime - lastCheckTime >= CHECK_INTERVAL) {
    checkServerVariable();
    lastCheckTime = currentTime;
  }
  
  delay(10); // Stability delay
}

// --- NETWORK FUNCTIONS ---

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? "\nConnected!" : "\nFailed.");
}

void sendDataToServer() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = String(serverUrl) + "/iot/button-count";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["device_id"] = deviceId;
  doc["count"] = buttonCount;
  doc["is_divisible_by_3"] = (buttonCount % 3 == 0 && buttonCount != 0);
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  if (httpCode > 0) Serial.printf("Data Sent (Code %d)\n", httpCode);
  else Serial.printf("Send Failed: %s\n", http.errorToString(httpCode).c_str());
  
  http.end();
}

void checkServerVariable() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  // Checking for a variable named 'remote_trigger' on the server
  String url = String(serverUrl) + "/iot/status?variable_name=remote_trigger";
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      bool isTriggered = doc["triggered"]; // Assuming JSON is {"triggered": true}
      
      if (isTriggered) {
        Serial.println("!!! REMOTE TRIGGER RECEIVED FROM SERVER !!!");
        performTriggerAction();
      }
    }
  } else {
    Serial.print("Check Failed: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

// --- INPUT/OUTPUT FUNCTIONS ---

void readButton() {
  bool currentState = digitalRead(BUTTON_PIN);
  
  if (currentState != buttonLastState) buttonLastDebounce = millis();
  
  if ((millis() - buttonLastDebounce) > DEBOUNCE_DELAY) {
    // Detect Press (Falling Edge)
    if (currentState == LOW && buttonLastState == HIGH) {
      buttonCount++;
      Serial.printf("Button Pressed. Count: %d\n", buttonCount);
      
      // Local Trigger Check
      if (buttonCount % 3 == 0 && buttonCount != 0) {
        Serial.println("!!! LOCAL TRIGGER (Divisible by 3) !!!");
        performTriggerAction();
        // Immediately sync with server on critical event
        sendDataToServer(); 
      }
    }
  }
  buttonLastState = currentState;
}

void performTriggerAction() {
  // Alert Action (Rapid Blinking)
  for(int i=0; i<5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}