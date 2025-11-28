# ✅ GET /get-coordinates-drone - UPDATED!

## 🎯 What Changed

The `/get-coordinates-drone` endpoint now returns **signal strength** at index 3 instead of accuracy!

## 📡 New Format

### Response
```json
[28.7522491, 77.4985427, 1.0, 95.0]
```

### Array Structure
- **`[0]`** = **Latitude** (degrees) - from Android GPS
- **`[1]`** = **Longitude** (degrees) - from Android GPS
- **`[2]`** = **Reserved** (always 1.0)
- **`[3]`** = **Signal Strength** (0-100%) - from ESP32 helmet

## 🔄 Data Sources

The endpoint combines data from **two sources**:

1. **GPS Coordinates** (indices 0-1) → from Android app via `POST /coordinates`
2. **Signal Strength** (index 3) → from ESP32 helmet via `POST /rssi`

```
Android App ──POST /coordinates──> GPS (lat, lon)
                                      ↓
ESP32 Helmet ──POST /rssi──────────> Signal (0-100%)
                                      ↓
                            [lat, lon, 1, signal]
                                      ↓
Drone ──GET /get-coordinates-drone──> Combined Data
```

## 🧪 Test It

### Send GPS from Android
```bash
curl -X POST http://localhost:8001/coordinates \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.7522491,
    "longitude": 77.4985427,
    "timestamp": 1732713392000,
    "accuracy": 100.0
  }'
```

### Send Signal from ESP32
```bash
curl -X POST http://localhost:8001/rssi \
  -H "Content-Type: application/json" \
  -d '{"helmet_id": 1234, "signal": 95}'
```

### Get Combined Data
```bash
curl http://localhost:8001/get-coordinates-drone
```

**Response:**
```json
[28.7522491, 77.4985427, 1.0, 95.0]
```

## 📱 ESP32/Arduino Usage

```cpp
#include <HTTPClient.h>
#include <ArduinoJson.h>

void getTargetWithSignal() {
    HTTPClient http;
    http.begin("https://adahrs-ip-157-49-184-22.tunnelmole.net/get-coordinates-drone");
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String payload = http.getString();
        
        StaticJsonDocument<200> doc;
        deserializeJson(doc, payload);
        
        double targetLat = doc[0];      // 28.7522491
        double targetLon = doc[1];      // 77.4985427
        double reserved = doc[2];       // 1.0
        double signal = doc[3];         // 95.0 (NEW!)
        
        Serial.printf("Target: %.6f, %.6f\n", targetLat, targetLon);
        Serial.printf("Signal: %.0f%%\n", signal);
        
        // Check signal before navigating
        if (signal < 30) {
            Serial.println("WARNING: Weak signal, navigation may be unreliable!");
        } else {
            navigateToTarget(targetLat, targetLon);
        }
    }
    
    http.end();
}
```

## 🎯 Use Cases

### 1. Navigate with Signal Awareness
```cpp
// Only navigate if signal is strong enough
if (signal > 50) {
    navigateToTarget(lat, lon);
} else {
    Serial.println("Signal too weak, waiting...");
}
```

### 2. Return to Home with Connection Check
```cpp
// Return to Android device location
// Check signal to ensure connection during flight
double lat = coordinates[0];
double lon = coordinates[1];
double signal = coordinates[3];

if (signal > 30) {
    returnToHome(lat, lon);
} else {
    emergencyLand();  // Signal lost!
}
```

### 3. Follow Me Mode
```cpp
// Continuously follow Android device
// Monitor signal strength for safety
void followMe() {
    while (true) {
        auto coords = getCoordinates();
        
        if (coords[3] > 40) {  // Good signal
            flyTo(coords[0], coords[1]);
        } else {
            hover();  // Weak signal, stay in place
        }
        
        delay(2000);
    }
}
```

## 📊 Signal Strength Guide

| Signal % | Quality | Action |
|----------|---------|--------|
| 90-100% | ⭐⭐⭐⭐⭐ Excellent | Full navigation |
| 70-89% | ⭐⭐⭐⭐ Very Good | Safe to navigate |
| 50-69% | ⭐⭐⭐ Good | Navigate with caution |
| 30-49% | ⭐⭐ Fair | Limited navigation |
| 0-29% | ⭐ Weak | Hover or land |

## 🔍 Example Responses

### Good Signal
```json
[28.7522491, 77.4985427, 1.0, 95.0]
```
✅ Strong signal (95%), safe to navigate

### Weak Signal
```json
[28.7522491, 77.4985427, 1.0, 25.0]
```
⚠️ Weak signal (25%), navigation risky

### No Signal Data
```json
[28.7522491, 77.4985427, 1.0, 0.0]
```
❌ No RSSI data received yet

### No GPS Data
```json
[0.0, 0.0, 0.0, 0.0]
```
❌ No coordinates received yet

## ⚡ Real-Time Updates

- **GPS**: Updates every ~2 seconds from Android app
- **Signal**: Updates when ESP32 helmet sends RSSI data
- **Endpoint**: Always returns latest data from both sources

## 💡 Best Practices

1. **Check Signal First**: Always verify signal strength before navigation
2. **Set Thresholds**: Define minimum signal level for safe operation (e.g., 30%)
3. **Emergency Protocol**: Have a fallback plan for signal loss
4. **Poll Regularly**: Request coordinates every 1-2 seconds for smooth tracking
5. **Monitor Both**: Track both GPS accuracy and signal strength

## ✅ Summary

The endpoint now provides:
- ✅ **Latitude** from Android GPS
- ✅ **Longitude** from Android GPS
- ✅ **Signal Strength** from ESP32 helmet (NEW!)
- ✅ Simple 4-element array format
- ✅ Real-time updates from both sources

Perfect for drone navigation with connection awareness! 🚁📡✨
