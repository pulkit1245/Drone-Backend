/*
 * ESP32 Navigation with IoT Trigger Integration
 * ==============================================
 * 
 * Features:
 * 1. Fetches GPS + compass data from phone server (/history)
 * 2. Shows direction using 4 LEDs (N/E/S/W)
 * 3. Monitors 3 buttons - auto-triggers when count reaches 3 (or multiples of 3)
 * 4. Checks IoT trigger status every second
 * 5. Navigation system only active when triggered
 * 
 * Hardware:
 * - LED_N (GPIO 25) - Front/North
 * - LED_E (GPIO 26) - Right/East
 * - LED_S (GPIO 27) - Back/South
 * - LED_W (GPIO 14) - Left/West
 * - BUTTON_1 (GPIO 12) - with pull-up
 * - BUTTON_2 (GPIO 13) - with pull-up
 * - BUTTON_3 (GPIO 15) - with pull-up
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <math.h>

// ======================== WiFi & Server ========================

const char* WIFI_SSID     = "BIT-SIH";
const char* WIFI_PASSWORD = "bitsih@2025";

const char* SERVER_IP   = "172.16.7.78";   // Phone/laptop server IP
const int   SERVER_PORT = 8001;
const char* GPS_ENDPOINT = "/history";     // GPS data endpoint
const char* IOT_TRIGGER_ENDPOINT = "/iot/trigger";  // IoT trigger check

// Device ID for this ESP32
const char* DEVICE_ID = "esp32_nav_001";

// Variable name to monitor
const char* TRIGGER_VARIABLE = "start_navigation";

// Update intervals
const unsigned long GPS_UPDATE_INTERVAL = 1000;      // 1 second
const unsigned long TRIGGER_CHECK_INTERVAL = 1000;   // 1 second
const unsigned long BUTTON_SEND_INTERVAL = 2000;     // 2 seconds

unsigned long lastGpsUpdate = 0;
unsigned long lastTriggerCheck = 0;
unsigned long lastButtonSend = 0;

// ======================== LED PINS ========================

#define LED_N 25   // Front
#define LED_E 26   // Right
#define LED_S 27   // Back
#define LED_W 14   // Left

// ======================== BUTTON PINS ========================

#define BUTTON_1 12
#define BUTTON_2 13
#define BUTTON_3 15

// Button state tracking
int button1Count = 0;
int button2Count = 0;
int button3Count = 0;
int totalButtonCount = 0;

bool button1LastState = HIGH;
bool button2LastState = HIGH;
bool button3LastState = HIGH;

// Debounce
const unsigned long DEBOUNCE_DELAY = 50;
unsigned long button1LastDebounce = 0;
unsigned long button2LastDebounce = 0;
unsigned long button3LastDebounce = 0;

// ======================== DESTINATION ========================

const float destLat = 28.7536382;
const float destLon = 77.4983311;
const float ARRIVAL_RADIUS_M = 4.0;

// ======================== System State ========================

bool systemInitialized = false;  // True when navigation system is active
bool navigationActive = false;   // True when actively navigating

// ======================== Location Data ========================

struct LocationData {
  double latitude;
  double longitude;
  long   timestamp;
  float  accuracy;
  float  altitude;
  float  speed;
  float  azimuth;
  float  pitch;
  float  roll;
  bool   valid;
};

LocationData currentData;

// ============================================================
// Helper Functions
// ============================================================

float bearingToTarget(float lat1, float lon1, float lat2, float lon2) {
  float phi1 = radians(lat1);
  float phi2 = radians(lat2);
  float dLon = radians(lon2 - lon1);

  float y = sin(dLon) * cos(phi2);
  float x = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dLon);

  float brng = atan2(y, x);
  brng = degrees(brng);

  if (brng < 0) brng += 360.0;
  return brng;
}

float distanceToTarget(float lat1, float lon1, float lat2, float lon2) {
  const float R = 6371000.0;

  float phi1 = radians(lat1);
  float phi2 = radians(lat2);
  float dPhi = radians(lat2 - lat1);
  float dLambda = radians(lon2 - lon1);

  float a = sin(dPhi/2) * sin(dPhi/2) +
            cos(phi1) * cos(phi2) *
            sin(dLambda/2) * sin(dLambda/2);

  float c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a));
  float d = R * c;

  return d;
}

float normalizeRelative(float angle) {
  while (angle > 180.0) angle -= 360.0;
  while (angle < -180.0) angle += 360.0;
  return angle;
}

// ============================================================
// WiFi Connection
// ============================================================

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Server: http://");
    Serial.print(SERVER_IP);
    Serial.print(":");
    Serial.println(SERVER_PORT);
    
    // Blink all LEDs to indicate WiFi connected
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_N, HIGH);
      digitalWrite(LED_E, HIGH);
      digitalWrite(LED_S, HIGH);
      digitalWrite(LED_W, HIGH);
      delay(200);
      digitalWrite(LED_N, LOW);
      digitalWrite(LED_E, LOW);
      digitalWrite(LED_S, LOW);
      digitalWrite(LED_W, LOW);
      delay(200);
    }
  } else {
    Serial.println("\n✗ WiFi Connection Failed!");
  }
}

// ============================================================
// Setup
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ESP32 Navigation with IoT Trigger ===");
  Serial.println("Press any button 3 times to start navigation");
  Serial.println("Or trigger via app: POST /iot/trigger");
  Serial.println();

  // Initialize LED pins
  pinMode(LED_N, OUTPUT);
  pinMode(LED_E, OUTPUT);
  pinMode(LED_S, OUTPUT);
  pinMode(LED_W, OUTPUT);

  digitalWrite(LED_N, LOW);
  digitalWrite(LED_E, LOW);
  digitalWrite(LED_S, LOW);
  digitalWrite(LED_W, LOW);

  // Initialize button pins
  pinMode(BUTTON_1, INPUT_PULLUP);
  pinMode(BUTTON_2, INPUT_PULLUP);
  pinMode(BUTTON_3, INPUT_PULLUP);

  connectWiFi();

  currentData.valid = false;
  systemInitialized = false;
  navigationActive = false;
}

// ============================================================
// Main Loop
// ============================================================

void loop() {
  unsigned long currentTime = millis();

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    connectWiFi();
    delay(1000);
    return;
  }

  // Read buttons
  readButtons();

  // Send button counts periodically
  if (currentTime - lastButtonSend >= BUTTON_SEND_INTERVAL) {
    lastButtonSend = currentTime;
    sendButtonCounts();
  }

  // Check trigger status every second
  if (currentTime - lastTriggerCheck >= TRIGGER_CHECK_INTERVAL) {
    lastTriggerCheck = currentTime;
    checkTriggerStatus();
  }

  // Only fetch GPS and update navigation if system is initialized
  if (systemInitialized) {
    if (currentTime - lastGpsUpdate >= GPS_UPDATE_INTERVAL) {
      lastGpsUpdate = currentTime;
      fetchLocationData();
    }

    if (currentData.valid) {
      updateDirectionLeds();
      navigationActive = true;
    }
  } else {
    // System not initialized - turn off all LEDs
    digitalWrite(LED_N, LOW);
    digitalWrite(LED_E, LOW);
    digitalWrite(LED_S, LOW);
    digitalWrite(LED_W, LOW);
    navigationActive = false;
  }

  delay(20);
}

// ============================================================
// Button Reading with Debouncing
// ============================================================

void readButtons() {
  readButton1();
  readButton2();
  readButton3();
}

void readButton1() {
  bool currentState = digitalRead(BUTTON_1);
  
  if (currentState != button1LastState) {
    button1LastDebounce = millis();
  }
  
  if ((millis() - button1LastDebounce) > DEBOUNCE_DELAY) {
    if (currentState == LOW && button1LastState == HIGH) {
      button1Count++;
      totalButtonCount++;
      Serial.print("Button 1 pressed! Count: ");
      Serial.println(button1Count);
      
      checkAutoTrigger();
    }
  }
  
  button1LastState = currentState;
}

void readButton2() {
  bool currentState = digitalRead(BUTTON_2);
  
  if (currentState != button2LastState) {
    button2LastDebounce = millis();
  }
  
  if ((millis() - button2LastDebounce) > DEBOUNCE_DELAY) {
    if (currentState == LOW && button2LastState == HIGH) {
      button2Count++;
      totalButtonCount++;
      Serial.print("Button 2 pressed! Count: ");
      Serial.println(button2Count);
      
      checkAutoTrigger();
    }
  }
  
  button2LastState = currentState;
}

void readButton3() {
  bool currentState = digitalRead(BUTTON_3);
  
  if (currentState != button3LastState) {
    button3LastDebounce = millis();
  }
  
  if ((millis() - button3LastDebounce) > DEBOUNCE_DELAY) {
    if (currentState == LOW && button3LastState == HIGH) {
      button3Count++;
      totalButtonCount++;
      Serial.print("Button 3 pressed! Count: ");
      Serial.println(button3Count);
      
      checkAutoTrigger();
    }
  }
  
  button3LastState = currentState;
}

// ============================================================
// Auto-trigger when button count reaches 3 or multiples of 3
// ============================================================

void checkAutoTrigger() {
  if (totalButtonCount % 3 == 0 && totalButtonCount > 0) {
    Serial.println();
    Serial.println("*** AUTO-TRIGGER: Button count reached multiple of 3! ***");
    Serial.print("Total button presses: ");
    Serial.println(totalButtonCount);
    
    // Trigger the navigation system via server
    triggerNavigationSystem();
    
    // Flash all LEDs rapidly to indicate trigger
    for (int i = 0; i < 5; i++) {
      digitalWrite(LED_N, HIGH);
      digitalWrite(LED_E, HIGH);
      digitalWrite(LED_S, HIGH);
      digitalWrite(LED_W, HIGH);
      delay(100);
      digitalWrite(LED_N, LOW);
      digitalWrite(LED_E, LOW);
      digitalWrite(LED_S, LOW);
      digitalWrite(LED_W, LOW);
      delay(100);
    }
  }
}

// ============================================================
// Send button counts to server
// ============================================================

void sendButtonCounts() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/iot/button-count";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["device_id"] = DEVICE_ID;
  doc["button_1"] = button1Count;
  doc["button_2"] = button2Count;
  doc["button_3"] = button3Count;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  int httpCode = http.POST(jsonPayload);
  
  if (httpCode == 200) {
    Serial.println("✓ Button counts sent to server");
  }
  
  http.end();
}

// ============================================================
// Trigger navigation system via server
// ============================================================

void triggerNavigationSystem() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + String(IOT_TRIGGER_ENDPOINT);
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<200> doc;
  doc["variable_name"] = TRIGGER_VARIABLE;
  doc["triggered"] = true;
  doc["triggered_by"] = DEVICE_ID;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.println("\n--- Triggering Navigation System ---");
  Serial.print("URL: ");
  Serial.println(url);
  Serial.print("Payload: ");
  Serial.println(jsonPayload);
  
  int httpCode = http.POST(jsonPayload);
  
  if (httpCode == 200) {
    Serial.println("✓ Navigation system triggered successfully!");
    systemInitialized = true;
  } else {
    Serial.print("✗ Trigger failed: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

// ============================================================
// Check trigger status from server
// ============================================================

void checkTriggerStatus() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + 
               String(IOT_TRIGGER_ENDPOINT) + "?variable_name=" + String(TRIGGER_VARIABLE);
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String response = http.getString();
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      bool triggered = doc["triggered"];
      
      if (triggered && !systemInitialized) {
        Serial.println("\n*** NAVIGATION SYSTEM TRIGGERED FROM APP! ***");
        systemInitialized = true;
        
        // Flash LEDs to indicate activation
        for (int i = 0; i < 3; i++) {
          digitalWrite(LED_N, HIGH);
          digitalWrite(LED_E, HIGH);
          digitalWrite(LED_S, HIGH);
          digitalWrite(LED_W, HIGH);
          delay(200);
          digitalWrite(LED_N, LOW);
          digitalWrite(LED_E, LOW);
          digitalWrite(LED_S, LOW);
          digitalWrite(LED_W, LOW);
          delay(200);
        }
      } else if (!triggered && systemInitialized) {
        Serial.println("\n*** NAVIGATION SYSTEM STOPPED FROM APP ***");
        systemInitialized = false;
        navigationActive = false;
      }
    }
  }
  
  http.end();
}

// ============================================================
// Fetch GPS data from phone server
// ============================================================

void fetchLocationData() {
  HTTPClient http;

  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + String(GPS_ENDPOINT);
  http.begin(url);
  http.setTimeout(5000);

  int httpCode = http.GET();

  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    parseLocationData(payload);
  } else {
    currentData.valid = false;
  }

  http.end();
}

// ============================================================
// Parse GPS JSON data
// ============================================================

void parseLocationData(String jsonString) {
  StaticJsonDocument<2048> doc;

  DeserializationError error = deserializeJson(doc, jsonString);
  if (error) {
    currentData.valid = false;
    return;
  }

  JsonArray dataArray = doc["data"];
  int count = doc["count"];

  if (count == 0 || dataArray.size() == 0) {
    currentData.valid = false;
    return;
  }

  JsonObject latestData = dataArray[dataArray.size() - 1];

  currentData.latitude  = latestData["latitude"]  | 0.0;
  currentData.longitude = latestData["longitude"] | 0.0;
  currentData.timestamp = latestData["timestamp"] | 0;
  currentData.accuracy  = latestData["accuracy"]  | 0.0;
  currentData.altitude  = latestData["altitude"]  | 0.0;
  currentData.speed     = latestData["speed"]     | 0.0;
  currentData.azimuth   = latestData["azimuth"]   | 0.0;
  currentData.pitch     = latestData["pitch"]     | 0.0;
  currentData.roll      = latestData["roll"]      | 0.0;

  currentData.valid = true;
}

// ============================================================
// Update Direction LEDs based on navigation
// ============================================================

void updateDirectionLeds() {
  if (!currentData.valid || !systemInitialized) {
    digitalWrite(LED_N, LOW);
    digitalWrite(LED_E, LOW);
    digitalWrite(LED_S, LOW);
    digitalWrite(LED_W, LOW);
    return;
  }

  float heading = currentData.azimuth;

  float brng = bearingToTarget(
                 (float)currentData.latitude,
                 (float)currentData.longitude,
                 destLat,
                 destLon
               );

  float diff = normalizeRelative(brng - heading);
  float dist = distanceToTarget(
                 (float)currentData.latitude,
                 (float)currentData.longitude,
                 destLat,
                 destLon
               );

  // ARRIVED condition
  if (dist <= ARRIVAL_RADIUS_M) {
    digitalWrite(LED_N, HIGH);
    digitalWrite(LED_E, HIGH);
    digitalWrite(LED_S, HIGH);
    digitalWrite(LED_W, HIGH);

    Serial.print("🎯 ARRIVED! Distance: ");
    Serial.print(dist, 2);
    Serial.println(" m");
    return;
  }

  // Clear all LEDs
  digitalWrite(LED_N, LOW);
  digitalWrite(LED_E, LOW);
  digitalWrite(LED_S, LOW);
  digitalWrite(LED_W, LOW);

  // Show direction based on 8 sectors
  if (diff > -22.5 && diff <= 22.5) {
    digitalWrite(LED_N, HIGH);  // N
  }
  else if (diff > 22.5 && diff <= 67.5) {
    digitalWrite(LED_N, HIGH);  // NE
    digitalWrite(LED_E, HIGH);
  }
  else if (diff > 67.5 && diff <= 112.5) {
    digitalWrite(LED_E, HIGH);  // E
  }
  else if (diff > 112.5 && diff <= 157.5) {
    digitalWrite(LED_S, HIGH);  // SE
    digitalWrite(LED_E, HIGH);
  }
  else if (diff > 157.5 || diff <= -157.5) {
    digitalWrite(LED_S, HIGH);  // S
  }
  else if (diff > -157.5 && diff <= -112.5) {
    digitalWrite(LED_S, HIGH);  // SW
    digitalWrite(LED_W, HIGH);
  }
  else if (diff > -112.5 && diff <= -67.5) {
    digitalWrite(LED_W, HIGH);  // W
  }
  else if (diff > -67.5 && diff <= -22.5) {
    digitalWrite(LED_N, HIGH);  // NW
    digitalWrite(LED_W, HIGH);
  }

  Serial.print("→ Bearing: ");
  Serial.print(brng, 1);
  Serial.print("° | Diff: ");
  Serial.print(diff, 1);
  Serial.print("° | Dist: ");
  Serial.print(dist, 1);
  Serial.println(" m");
}
