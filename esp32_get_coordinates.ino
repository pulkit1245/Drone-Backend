/*
 * ESP32 Example: Get Coordinates from Server
 * 
 * This example shows how to fetch coordinates from the /get-coordinates-drone endpoint
 * and parse the JSON array response.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server URL
const char* serverUrl = "http://YOUR_SERVER_IP:5000/get-coordinates-drone?cached=true";

// Coordinate storage
struct Coordinates {
  double latitude;
  double longitude;
  double reserved;
  double accuracy;
};

Coordinates currentCoords = {0.0, 0.0, 0.0, 0.0};

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nConnected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (getCoordinates()) {
      // Successfully got coordinates
      Serial.println("\n=== Current Coordinates ===");
      Serial.print("Latitude:  ");
      Serial.println(currentCoords.latitude, 6);
      Serial.print("Longitude: ");
      Serial.println(currentCoords.longitude, 6);
      Serial.print("Reserved:  ");
      Serial.println(currentCoords.reserved, 1);
      Serial.print("Accuracy:  ±");
      Serial.print(currentCoords.accuracy, 1);
      Serial.println(" meters");
      Serial.println("===========================\n");
      
      // Example: Use coordinates for navigation
      // navigateToCoordinates(currentCoords.latitude, currentCoords.longitude);
    } else {
      Serial.println("Failed to get coordinates");
    }
  } else {
    Serial.println("WiFi disconnected!");
  }
  
  delay(5000); // Poll every 5 seconds
}

bool getCoordinates() {
  HTTPClient http;
  
  Serial.print("Fetching coordinates from server... ");
  
  http.begin(serverUrl);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    Serial.println("OK");
    
    // Parse JSON array
    // Expected format: [37.7749, -122.4194, 1.0, 65.0]
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);
    
    if (error) {
      Serial.print("JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    
    // Extract coordinates from array
    currentCoords.latitude = doc[0];
    currentCoords.longitude = doc[1];
    currentCoords.reserved = doc[2];
    currentCoords.accuracy = doc[3];
    
    http.end();
    return true;
    
  } else {
    Serial.print("Failed, HTTP code: ");
    Serial.println(httpCode);
    http.end();
    return false;
  }
}

// Example function: Navigate to coordinates
void navigateToCoordinates(double targetLat, double targetLon) {
  // Implement your navigation logic here
  // This is where you would use the coordinates for drone navigation
  Serial.println("Navigating to target coordinates...");
  
  // Example: Calculate distance, bearing, etc.
  // moveToTarget(targetLat, targetLon);
}
