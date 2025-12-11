/*
 * ESP32 Hybrid Navigation System (ST7735 — FINAL, fixed)
 * - Uses Adafruit_ST7735 + Adafruit_GFX
 * - Display: 128x160, INITR_BLACKTAB, rotation 1
 * - Wiring: CS=5, DC=15, RST=4, SCK=18, MOSI=23, VCC=3.3V, GND=GND, LED=3.3V
 *
 * Changes:
 *  - Replaced N/E/S/W with Front/Right/Back/Left
 *  - Removed Brg/Hdg/Acc overlay fields (only Dist remains)
 *  - Now fetches calculated direction from Server (/calculate-direction)
 *  - Update interval: 0.5s
 *  - Trigger Logic: Remote Trigger OR (Button Count % 3 == 0)
 *  - Inactive State: Display shows nothing (Black screen)
 *
 * Libraries required:
 *  - Adafruit GFX
 *  - Adafruit ST7735 and ST7789
 *  - ArduinoJson
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <math.h>

// ------------------------ WiFi & Server ------------------------
const char* WIFI_SSID     = "BIT-SIH";
const char* WIFI_PASSWORD = "bitsih@2025";

const char* SERVER_IP   = "172.16.7.78";
const int   SERVER_PORT = 8001;
const char* DIRECTION_ENDPOINT = "/calculate-direction";
const char* TRIGGER_ENDPOINT = "/iot/trigger?variable_name=start_navigation";

// ------------------------ DESTINATION ------------------------
const float ARRIVAL_RADIUS_M = 4.0;

// ------------------------ ST7735 (Adafruit) ------------------------
#define TFT_CS   5
#define TFT_DC   15
#define TFT_RST  4
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_RST);

// ------------------------ BUTTON ------------------------
#define BUTTON_PIN 12
int buttonCount = 0;
bool lastButtonState = HIGH;
unsigned long lastDebounce = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// ------------------------ TIMERS ------------------------
unsigned long lastUpdate = 0;
unsigned long lastTriggerCheck = 0;
const unsigned long GPS_UPDATE_INTERVAL = 500; // 0.5 seconds
const unsigned long TRIGGER_CHECK_INTERVAL = 1000;

// For non-blocking status blink when waiting for GPS
unsigned long lastStatusBlink = 0;
const unsigned long STATUS_BLINK_MS = 500;
bool statusLedState = false;

// ------------------------ STATE ------------------------
bool navigationActive = false;
bool wifiPreviouslyConnected = false;
bool remoteTriggerActive = false; // Track remote trigger state

// Onboard status LED (most devkits use GPIO2)
#define STATUS_LED 2

// ------------------------ STRUCT ------------------------
struct NavigationData {
  String direction;       // "FRONT", "RIGHT", "LEFT", "BACK"
  float  bearing;
  float  distance;
  float  heading_diff;
  bool   valid;
  String message;
};
NavigationData currentNav = {"", 0, 0, 0, false, ""};

// ============================================================
// Forward declarations
void connectWiFi();
void readButton();
void checkRemoteTrigger();
void fetchNavigationData();
void parseNavigationData(String jsonString);
void startNavigation();
void stopNavigation();

// ============================================================
// Helper Functions
// ============================================================

void drawCenteredText(const char *txt, int y, uint8_t size = 2, uint16_t color = ST77XX_WHITE) {
  tft.setTextSize(size);
  tft.setTextColor(color, ST77XX_BLACK);
  int16_t x1, y1;
  uint16_t w, h;
  tft.getTextBounds(txt, 0, y, &x1, &y1, &w, &h);
  int16_t x = (tft.width() - w) / 2;
  tft.setCursor(x, y);
  tft.print(txt);
}

void drawRotatedArrow(int cx, int cy, float angleDeg, int length, uint16_t color) {
  float rad = radians(angleDeg - 90.0f);
  int x2 = cx + (int)(cos(rad) * length);
  int y2 = cy + (int)(sin(rad) * length);

  for (int o = -1; o <= 1; ++o) {
    tft.drawLine(cx + o, cy, x2 + o, y2, color);
    tft.drawLine(cx, cy + o, x2, y2 + o, color);
  }

  float headLen = max(8, length / 4);
  float backRad = radians(angleDeg - 90.0f + 180.0f);
  int bx = x2 + (int)(cos(backRad) * headLen);
  int by = y2 + (int)(sin(backRad) * headLen);
  float perpRad = rad + M_PI/2.0;
  int px = (int)(cos(perpRad) * (headLen/2.0));
  int py = (int)(sin(perpRad) * (headLen/2.0));
  tft.fillTriangle(x2, y2, bx + px, by + py, bx - px, by - py, color);
}

void drawNavigationScreen(String direction, float diff, float dist) {
  tft.fillScreen(ST77XX_BLACK);

  const int cx = tft.width() / 2;
  const int cy = (tft.height() / 2) - 8;
  const int radius = min(cx, cy) - 10;

  tft.drawCircle(cx, cy, radius, ST77XX_WHITE);
  tft.drawCircle(cx, cy, radius-2, ST77XX_WHITE);

  // Labels
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);

  // Front (top)
  int16_t x1, y1; uint16_t w, h;
  tft.getTextBounds("Front", 0, 0, &x1, &y1, &w, &h);
  tft.setCursor(cx - (w/2), cy - radius - 10); 
  if (direction == "FRONT") tft.setTextColor(ST77XX_GREEN, ST77XX_BLACK);
  else tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.print("Front");

  // Right
  tft.getTextBounds("Right", 0, 0, &x1, &y1, &w, &h);
  tft.setCursor(cx + radius - (w + 4), cy - 4); 
  if (direction == "RIGHT") tft.setTextColor(ST77XX_GREEN, ST77XX_BLACK);
  else tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.print("Right");

  // Back (bottom)
  tft.getTextBounds("Back", 0, 0, &x1, &y1, &w, &h);
  tft.setCursor(cx - (w/2), cy + radius - (h + 2)); 
  if (direction == "BACK") tft.setTextColor(ST77XX_GREEN, ST77XX_BLACK);
  else tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.print("Back");

  // Left
  tft.getTextBounds("Left", 0, 0, &x1, &y1, &w, &h);
  tft.setCursor(cx - radius + 4, cy - 4); 
  if (direction == "LEFT") tft.setTextColor(ST77XX_GREEN, ST77XX_BLACK);
  else tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.print("Left");

  // Arrow
  drawRotatedArrow(cx, cy, diff, radius - 12, ST77XX_RED);

  // Distance overlay
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  char buf[32];
  snprintf(buf, sizeof(buf), "Dist: %.1f m", dist);
  tft.setCursor(4, tft.height() - 12); tft.print(buf);
  
  // Direction Text
  tft.setCursor(4, 4);
  tft.setTextColor(ST77XX_CYAN, ST77XX_BLACK);
  tft.print(direction);
}

void drawWaitingScreen(String msg) {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_YELLOW, ST77XX_BLACK);
  drawCenteredText("Waiting for Data...", 44, 1, ST77XX_YELLOW);
  
  tft.setCursor(0, 68);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.println(msg);
}

void drawArrivedScreen() {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(ST77XX_GREEN, ST77XX_BLACK);
  drawCenteredText("ARRIVED!", 40, 2, ST77XX_GREEN);
  tft.fillRect(12, 88, tft.width()-24, 28, ST77XX_GREEN);
  tft.setTextSize(1);
  tft.setCursor(16, 92);
  tft.setTextColor(ST77XX_BLACK, ST77XX_GREEN);
  tft.print("You're at destination");
}

// ============================================================
// Setup
// ============================================================
void setup() {
  Serial.begin(115200);

  tft.initR(INITR_BLACKTAB);   // WORKING_TAB = BLACKTAB
  tft.setRotation(1);          // WORKING_ROTATION = 1
  tft.fillScreen(ST77XX_BLACK);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  lastButtonState = digitalRead(BUTTON_PIN);

  connectWiFi();

  // Initial screen is black (inactive)
  tft.fillScreen(ST77XX_BLACK);
  delay(350);
}

// ============================================================
// Main Loop
// ============================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    if (wifiPreviouslyConnected) {
      Serial.println("WiFi lost - attempting reconnect...");
      wifiPreviouslyConnected = false;
    }
    connectWiFi();
  } else {
    if (!wifiPreviouslyConnected) {
      Serial.println("WiFi connected.");
      wifiPreviouslyConnected = true;
    }
  }

  readButton();

  unsigned long now = millis();

  if (now - lastTriggerCheck >= TRIGGER_CHECK_INTERVAL) {
    lastTriggerCheck = now;
    checkRemoteTrigger();
  }

  // Logic: Active if Remote Trigger is TRUE OR (Button Count > 0 AND Button Count % 3 == 0)
  bool localActive = (buttonCount > 0 && (buttonCount % 3 == 0));
  bool shouldBeActive = remoteTriggerActive || localActive;

  // State Transition Handling
  if (shouldBeActive && !navigationActive) {
    startNavigation();
  } else if (!shouldBeActive && navigationActive) {
    stopNavigation();
  }

  if (navigationActive) {
    if (now - lastUpdate >= GPS_UPDATE_INTERVAL) {
      lastUpdate = now;
      fetchNavigationData();
      
      if (currentNav.valid) {
        Serial.println("--- NAV UPDATE ---");
        Serial.printf("Direction: %s\n", currentNav.direction.c_str());
        Serial.printf("Dist: %.2f m, Diff: %.2f\n", currentNav.distance, currentNav.heading_diff);

        if (currentNav.distance <= ARRIVAL_RADIUS_M) {
          drawArrivedScreen();
          Serial.println("ARRIVED at destination!");
          delay(1800);
          // Note: We don't force stop here because the trigger condition might still be true.
          // But usually we want to stop. 
          // If we stop, we need to reset the trigger or button count?
          // For now, let's just let it stay active or maybe reset button count?
          // User didn't specify, but stopping usually implies resetting state.
          // Let's reset button count to stop local trigger. Remote trigger might still be active though.
          buttonCount++; // Increment to break % 3 == 0
          // If remote trigger is active, it will restart immediately. 
          // Ideally remote trigger should be reset by server, but we can't do that easily here without a POST.
          // We'll just stop locally.
          stopNavigation();
        } else {
          drawNavigationScreen(currentNav.direction, currentNav.heading_diff, currentNav.distance);
        }
      } else {
        drawWaitingScreen(currentNav.message);
      }
    }

    if (!currentNav.valid) {
      if (now - lastStatusBlink >= STATUS_BLINK_MS) {
        lastStatusBlink = now;
        statusLedState = !statusLedState;
        digitalWrite(STATUS_LED, statusLedState ? HIGH : LOW);
      }
    } else {
      digitalWrite(STATUS_LED, LOW);
    }
  } else {
    // Inactive state: Display shows nothing
    digitalWrite(STATUS_LED, LOW);
  }

  delay(10);
}

// ============================================================
// Button Logic
// ============================================================
void readButton() {
  bool state = digitalRead(BUTTON_PIN);
  if (state != lastButtonState) lastDebounce = millis();

  if ((millis() - lastDebounce) > DEBOUNCE_DELAY) {
    if (state == LOW && lastButtonState == HIGH) {
      buttonCount++;
      Serial.printf("Button pressed: %d\n", buttonCount);
    }
  }
  lastButtonState = state;
}

// ============================================================
// WiFi
// ============================================================
void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  const int maxAttempts = 40; // ~20s
  while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi Connection Failed (will retry in loop).");
  }
}

// ============================================================
// Remote Trigger Check
// ============================================================
void checkRemoteTrigger() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + String(TRIGGER_ENDPOINT);
  http.begin(url.c_str());
  http.setTimeout(3000);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      bool triggered = false;
      if (doc.containsKey("triggered")) {
        triggered = doc["triggered"].as<bool>();
      } else if (doc.containsKey("value")) {
        int v = doc["value"].as<int>();
        triggered = (v != 0);
      } else if (doc.containsKey("start_navigation")) {
        triggered = doc["start_navigation"].as<bool>();
      } else {
        // Fallback: check any boolean true
        for (JsonPair kv : doc.as<JsonObject>()) {
          if (kv.value().is<bool>() && kv.value().as<bool>() == true) {
            triggered = true;
            break;
          }
        }
      }
      
      // Update global state
      if (triggered != remoteTriggerActive) {
        Serial.printf("Remote trigger changed: %d -> %d\n", remoteTriggerActive, triggered);
        remoteTriggerActive = triggered;
      }

    } else {
      Serial.print("Trigger JSON parse error: ");
      Serial.println(error.c_str());
    }
  } else if (httpCode > 0) {
    Serial.printf("HTTP Error (trigger): %d\n", httpCode);
  }
  http.end();
}

// ============================================================
// Navigation Logic (fetch from Server)
// ============================================================
void fetchNavigationData() {
  if (WiFi.status() != WL_CONNECTED) {
    currentNav.valid = false;
    currentNav.message = "WiFi Disconnected";
    return;
  }

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + String(DIRECTION_ENDPOINT);
  http.begin(url.c_str());
  http.setTimeout(2000); 
  int code = http.GET();

  if (code == 200) {
    String payload = http.getString();
    parseNavigationData(payload);
  } else {
    currentNav.valid = false;
    if (code == 400) {
       String payload = http.getString();
       StaticJsonDocument<256> doc;
       deserializeJson(doc, payload);
       const char* msg = doc["message"];
       if (msg) currentNav.message = String(msg);
       else currentNav.message = "Server Error 400";
    } else {
       currentNav.message = "HTTP Error " + String(code);
    }
    Serial.printf("Nav fetch error: %d\n", code);
  }
  http.end();
}

void parseNavigationData(String jsonString) {
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, jsonString);

  if (error) {
    Serial.print(F("Nav JSON parse error: "));
    Serial.println(error.c_str());
    currentNav.valid = false;
    currentNav.message = "JSON Error";
    return;
  }

  if (doc["status"] == "ok") {
    currentNav.direction = doc["direction"].as<String>();
    
    JsonObject nav = doc["navigation"];
    currentNav.bearing = nav["bearing"].as<float>();
    currentNav.distance = nav["distance"].as<float>();
    currentNav.heading_diff = nav["heading_diff"].as<float>();
    
    currentNav.valid = true;
    currentNav.message = "OK";
  } else {
    currentNav.valid = false;
    const char* msg = doc["message"];
    if (msg) currentNav.message = String(msg);
    else currentNav.message = "Unknown Status";
  }
}

// ============================================================
// Start/Stop Navigation
// ============================================================
void startNavigation() {
  navigationActive = true;
  currentNav.valid = false;
  currentNav.message = "Starting...";
  digitalWrite(STATUS_LED, HIGH);
  delay(150);
  digitalWrite(STATUS_LED, LOW);
  tft.fillScreen(ST77XX_BLACK);
  drawCenteredText("Navigation Started", 8, 2, ST77XX_WHITE);
  Serial.println("✅ Navigation System Activated");
}

void stopNavigation() {
  navigationActive = false;
  digitalWrite(STATUS_LED, HIGH);
  delay(250);
  digitalWrite(STATUS_LED, LOW);
  
  // Clear screen to black (show nothing)
  tft.fillScreen(ST77XX_BLACK);
  
  Serial.println("🛑 Navigation System Stopped");
}
