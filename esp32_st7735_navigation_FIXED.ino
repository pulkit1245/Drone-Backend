/*
 * ESP32 Hybrid Navigation System (ST7735 — FIXED)
 * - Uses Adafruit_ST7735 + Adafruit_GFX
 * - Display: 128x160, INITR_BLACKTAB, rotation 1
 * - Wiring: CS=5, DC=15, RST=4, SCK=18, MOSI=23, VCC=3.3V, GND=GND, LED=3.3V
 *
 * FIXED: Changed GPS_ENDPOINT from "/coordinates" to "/history"
 * - /coordinates is POST-only (for phone to send data)
 * - /history is GET (for ESP32 to fetch data)
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
const char* GPS_ENDPOINT = "/history";  // FIXED: Changed from /coordinates to /history
const char* TRIGGER_ENDPOINT = "/iot/trigger?variable_name=start_navigation";

// ------------------------ DESTINATION ------------------------
const float destLat = 11.494946;
const float destLon = 77.2767853;
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
const unsigned long GPS_UPDATE_INTERVAL = 1000;
const unsigned long TRIGGER_CHECK_INTERVAL = 1000;

// For non-blocking status blink when waiting for GPS
unsigned long lastStatusBlink = 0;
const unsigned long STATUS_BLINK_MS = 500;
bool statusLedState = false;

// ------------------------ STATE ------------------------
bool navigationActive = false;
bool wifiPreviouslyConnected = false;

// Onboard status LED (most devkits use GPIO2) — used only for tiny status feedback
#define STATUS_LED 2

// ------------------------ STRUCT ------------------------
struct LocationData {
  double latitude;
  double longitude;
  long   timestamp;
  float  accuracy;
  float  altitude;
  float  speed;
  float  azimuth; // degrees 0..360
  bool   valid;
};
LocationData currentData = {0,0,0,0,0,0,NAN,false};

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
            cos(phi1) * cos(phi2) * sin(dLambda/2) * sin(dLambda/2);
  float c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a));
  return R * c;
}

float normalizeRelative(float angle) {
  while (angle > 180.0) angle -= 360.0;
  while (angle < -180.0) angle += 360.0;
  return angle;
}

void setAllPixelsBlack() { tft.fillScreen(ST77XX_BLACK); }

// Draw helpers
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
  // Map 0° = pointing up; convert to rad for drawing (adjust so 0 points up)
  float rad = radians(angleDeg - 90.0f);
  int x2 = cx + (int)(cos(rad) * length);
  int y2 = cy + (int)(sin(rad) * length);

  // shaft (thick)
  for (int o = -1; o <= 1; ++o) {
    tft.drawLine(cx + o, cy, x2 + o, y2, color);
    tft.drawLine(cx, cy + o, x2, y2 + o, color);
  }

  // head triangle
  float headLen = max(8, length / 4);
  float backRad = radians(angleDeg - 90.0f + 180.0f);
  int bx = x2 + (int)(cos(backRad) * headLen);
  int by = y2 + (int)(sin(backRad) * headLen);
  float perpRad = rad + M_PI/2.0;
  int px = (int)(cos(perpRad) * (headLen/2.0));
  int py = (int)(sin(perpRad) * (headLen/2.0));
  tft.fillTriangle(x2, y2, bx + px, by + py, bx - px, by - py, color);
}

void drawNavigationScreen(float diff, float bearing, float heading, float dist, float accuracy) {
  tft.fillScreen(ST77XX_BLACK);

  // center and radii
  const int cx = tft.width() / 2;
  const int cy = (tft.height() / 2) - 8;
  const int radius = min(cx, cy) - 10;

  // Draw compass circle
  tft.drawCircle(cx, cy, radius, ST77XX_WHITE);
  tft.drawCircle(cx, cy, radius-2, ST77XX_WHITE);

  // Cardinal labels
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  tft.setCursor(cx - 6, cy - radius - 6); tft.print("N");
  tft.setCursor(cx + radius - 6, cy - 4); tft.print("E");
  tft.setCursor(cx - 4, cy + radius - 2); tft.print("S");
  tft.setCursor(cx - radius + 2, cy - 4); tft.print("W");

  // Arrow: arrow points toward target relative to device heading
  drawRotatedArrow(cx, cy, diff, radius - 12, ST77XX_RED);

  // Overlays
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  char buf[48];
  snprintf(buf, sizeof(buf), "Dist: %.1f m", dist);
  tft.setCursor(4, tft.height() - 44); tft.print(buf);
  snprintf(buf, sizeof(buf), "Brg: %.0f°", bearing);
  tft.setCursor(4, tft.height() - 32); tft.print(buf);
  snprintf(buf, sizeof(buf), "Hdg: %.0f°", heading);
  tft.setCursor(4, tft.height() - 20); tft.print(buf);
  snprintf(buf, sizeof(buf), "Acc: %.1f m", accuracy);
  tft.setCursor(4, tft.height() - 8); tft.print(buf);
}

void drawWaitingScreen() {
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_YELLOW, ST77XX_BLACK);
  drawCenteredText("Waiting for GPS...", 44, 1, ST77XX_YELLOW);
  drawCenteredText("Need azimuth & location", 68, 1, ST77XX_WHITE);
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

  // Initialize display with confirmed settings
  tft.initR(INITR_BLACKTAB);   // WORKING_TAB = BLACKTAB
  tft.setRotation(1);          // WORKING_ROTATION = 1
  tft.fillScreen(ST77XX_BLACK);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  // initial button state
  lastButtonState = digitalRead(BUTTON_PIN);

  connectWiFi();

  tft.setTextWrap(true);
  tft.setTextSize(1);
  tft.setTextColor(ST77XX_WHITE, ST77XX_BLACK);
  drawCenteredText("Navigation Ready", 6, 2, ST77XX_WHITE);
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

  if (navigationActive) {
    if (now - lastUpdate >= GPS_UPDATE_INTERVAL) {
      lastUpdate = now;
      fetchLocationData();
      if (currentData.valid) {
        float heading = currentData.azimuth; // 0..360
        float brng = bearingToTarget(currentData.latitude, currentData.longitude, destLat, destLon);
        float diff = normalizeRelative(brng - heading);
        float dist = distanceToTarget(currentData.latitude, currentData.longitude, destLat, destLon);

        // ARRIVED
        if (dist <= ARRIVAL_RADIUS_M) {
          drawArrivedScreen();
          Serial.println("ARRIVED at destination!");
          delay(1800);
          stopNavigation();
        } else {
          drawNavigationScreen(diff, brng, heading, dist, currentData.accuracy);
        }
      } else {
        drawWaitingScreen();
      }
    }

    // blink status LED when waiting for GPS
    if (!currentData.valid) {
      if (now - lastStatusBlink >= STATUS_BLINK_MS) {
        lastStatusBlink = now;
        statusLedState = !statusLedState;
        digitalWrite(STATUS_LED, statusLedState ? HIGH : LOW);
      }
    } else {
      digitalWrite(STATUS_LED, LOW);
    }
  } else {
    // not navigating — idle hint
    tft.fillRect(0, 40, tft.width(), 40, ST77XX_BLACK);
    drawCenteredText("Press button x3 to start", 56, 1, ST77XX_WHITE);
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
      if (buttonCount % 3 == 0) {
        Serial.println("Local trigger activated!");
        startNavigation();
      }
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
        for (JsonPair kv : doc.as<JsonObject>()) {
          if (kv.value().is<bool>() && kv.value().as<bool>() == true) {
            triggered = true;
            break;
          }
        }
      }

      if (triggered && !navigationActive) {
        Serial.println("Remote trigger activated!");
        startNavigation();
      } else if (!triggered && navigationActive) {
        Serial.println("Remote trigger reset - stopping navigation");
        stopNavigation();
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
// Navigation Logic (fetch & parse GPS)
// ============================================================
void fetchLocationData() {
  if (WiFi.status() != WL_CONNECTED) {
    currentData.valid = false;
    return;
  }

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + String(GPS_ENDPOINT);
  http.begin(url.c_str());
  http.setTimeout(3000);
  int code = http.GET();

  if (code == 200) {
    String payload = http.getString();
    parseLocationData(payload);
  } else {
    currentData.valid = false;
    if (code > 0) {
      Serial.printf("GPS fetch error: %d\n", code);
    }
  }
  http.end();
}

void parseLocationData(String jsonString) {
  StaticJsonDocument<2048> doc;
  DeserializationError error = deserializeJson(doc, jsonString);

  if (error) {
    Serial.print("GPS parse error: ");
    Serial.println(error.c_str());
    currentData.valid = false;
    return;
  }

  if (!doc.containsKey("data")) {
    Serial.println("GPS JSON: missing 'data' key");
    currentData.valid = false;
    return;
  }

  JsonArray data = doc["data"].as<JsonArray>();
  if (data.isNull() || data.size() == 0) {
    currentData.valid = false;
    return;
  }

  JsonObject latest = data[data.size() - 1].as<JsonObject>();

  if (!latest.containsKey("latitude") || !latest.containsKey("longitude")) {
    Serial.println("GPS JSON: latitude/longitude missing");
    currentData.valid = false;
    return;
  }

  currentData.latitude = latest["latitude"].as<double>();
  currentData.longitude = latest["longitude"].as<double>();
  currentData.azimuth = latest.containsKey("azimuth") ? latest["azimuth"].as<float>() : NAN;
  currentData.timestamp = latest.containsKey("timestamp") ? latest["timestamp"].as<long>() : 0;
  currentData.accuracy = latest.containsKey("accuracy") ? latest["accuracy"].as<float>() : 0.0;
  currentData.altitude = latest.containsKey("altitude") ? latest["altitude"].as<float>() : 0.0;
  currentData.speed = latest.containsKey("speed") ? latest["speed"].as<float>() : 0.0;

  if (isnan(currentData.azimuth)) {
    Serial.println("GPS data has no azimuth -> mark invalid (needs compass)");
    currentData.valid = false;
    return;
  }
  while (currentData.azimuth < 0.0) currentData.azimuth += 360.0;
  while (currentData.azimuth >= 360.0) currentData.azimuth -= 360.0;

  currentData.valid = true;
}

// ============================================================
// Start/Stop Navigation
// ============================================================
void startNavigation() {
  navigationActive = true;
  currentData.valid = false;
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
  tft.fillScreen(ST77XX_BLACK);
  drawCenteredText("Navigation Stopped", 8, 2, ST77XX_WHITE);
  Serial.println("🛑 Navigation System Stopped");
}
