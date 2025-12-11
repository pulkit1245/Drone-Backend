# Safe Waypoint & Navigation API Documentation

## Overview

The Safe Waypoint system allows mobile apps to set safe destination coordinates that ESP32 devices can navigate to. The server calculates direction (FRONT/BACK/LEFT/RIGHT) based on current GPS position and compass heading.

## Endpoints

### 1. POST /safe-coordinates

**Purpose:** Mobile app sets a safe waypoint (destination) for ESP32 navigation.

**Request:**
```json
{
  "latitude": 11.495504,
  "longitude": 77.278168,
  "timestamp": 1765486157554,  // optional, milliseconds
  "set_by": "mobile_app"        // optional, default: "mobile_app"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Safe waypoint updated",
  "waypoint": {
    "latitude": 11.495504,
    "longitude": 77.278168,
    "timestamp": 1765486157554,
    "timestamp_iso": "2025-12-11T20:49:17.554000",
    "set_by": "mobile_app"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8001/safe-coordinates \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 11.495504,
    "longitude": 77.278168,
    "set_by": "rescue_team"
  }'
```

---

### 2. GET /waypoint

**Purpose:** ESP32 fetches the current safe waypoint to navigate to.

**Request:** No parameters required

**Response (waypoint set):**
```json
{
  "status": "ok",
  "waypoint": {
    "latitude": 11.495504,
    "longitude": 77.278168,
    "timestamp": 1765486157554,
    "set_by": "mobile_app"
  }
}
```

**Response (no waypoint):**
```json
{
  "status": "no_waypoint",
  "message": "No waypoint has been set yet",
  "waypoint": null
}
```

**Example:**
```bash
curl http://localhost:8001/waypoint
```

---

### 3. GET /calculate-direction

**Purpose:** Calculate direction (FRONT/BACK/LEFT/RIGHT) from current position to waypoint.

**Requirements:**
- Waypoint must be set via POST /safe-coordinates
- GPS data with azimuth (compass heading) must be available

**Request:** No parameters required

**Response:**
```json
{
  "status": "ok",
  "direction": "RIGHT",
  "current_position": {
    "latitude": 11.4948379,
    "longitude": 77.2767928,
    "heading": 4.4
  },
  "waypoint": {
    "latitude": 11.495504,
    "longitude": 77.278168
  },
  "navigation": {
    "bearing": 63.7,
    "distance": 167.15,
    "heading_diff": 59.29
  }
}
```

**Direction Logic:**
- `FRONT`: Target is ahead (±15°)
- `RIGHT`: Target is to the right (15° to 90°)
- `LEFT`: Target is to the left (-15° to -90°)
- `BACK`: Target is behind (>90° or <-90°)

**Example:**
```bash
curl http://localhost:8001/calculate-direction
```

---

## Integration Workflow

### Mobile App Integration

```kotlin
// Set safe waypoint
suspend fun setSafeWaypoint(lat: Double, lon: Double) {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("latitude", lat)
        put("longitude", lon)
        put("timestamp", System.currentTimeMillis())
        put("set_by", "android_app")
    }
    
    val request = Request.Builder()
        .url("http://your-server:8001/safe-coordinates")
        .post(json.toString().toRequestBody("application/json".toMediaType()))
        .build()
    
    client.newCall(request).execute()
}
```

### ESP32 Integration

```cpp
// Fetch waypoint
void fetchWaypoint() {
  HTTPClient http;
  http.begin("http://172.16.7.78:8001/waypoint");
  int code = http.GET();
  
  if (code == 200) {
    String payload = http.getString();
    StaticJsonDocument<512> doc;
    deserializeJson(doc, payload);
    
    if (doc["status"] == "ok") {
      float destLat = doc["waypoint"]["latitude"];
      float destLon = doc["waypoint"]["longitude"];
      // Use these coordinates for navigation
    }
  }
  http.end();
}

// Get direction
void getDirection() {
  HTTPClient http;
  http.begin("http://172.16.7.78:8001/calculate-direction");
  int code = http.GET();
  
  if (code == 200) {
    String payload = http.getString();
    StaticJsonDocument<1024> doc;
    deserializeJson(doc, payload);
    
    if (doc["status"] == "ok") {
      String direction = doc["direction"];  // "FRONT", "BACK", "LEFT", "RIGHT"
      float distance = doc["navigation"]["distance"];
      
      // Update LEDs/display based on direction
      if (direction == "FRONT") {
        // Turn on front LED
      } else if (direction == "RIGHT") {
        // Turn on right LED
      }
      // etc.
    }
  }
  http.end();
}
```

---

## Data Storage

### safe_waypoints_log.csv

All waypoints are logged to `safe_waypoints_log.csv`:

```csv
timestamp_iso,timestamp_ms,latitude,longitude,set_by,client_ip
2025-12-11T20:49:17.554000,1765486157554,11.495504,77.278168,mobile_app_test,127.0.0.1
```

---

## Use Cases

### Use Case 1: Rescue Mission
1. **Rescue team** sets safe zone coordinates via mobile app
2. **Miners** with ESP32 helmets fetch waypoint
3. **ESP32** calculates direction and shows LEDs
4. **Miners** follow LED indicators to safety

### Use Case 2: Evacuation Route
1. **Control center** sets evacuation point
2. **All ESP32 devices** automatically fetch new waypoint
3. **Workers** navigate to evacuation point
4. **System** tracks when workers arrive (distance < 4m)

### Use Case 3: Dynamic Waypoints
1. **App** updates waypoint as situation changes
2. **ESP32** polls `/waypoint` every 5 seconds
3. **Direction** recalculates automatically
4. **Workers** always navigate to latest safe location

---

## Testing

Run the test script:
```bash
python3 test_waypoint_api.py
```

**Expected Output:**
```
✅ ALL TESTS PASSED

📋 Summary:
  ✓ App can set safe waypoint via POST /safe-coordinates
  ✓ ESP32 can fetch waypoint via GET /waypoint
  ✓ Server calculates direction via GET /calculate-direction
```

---

## Error Handling

### No Waypoint Set
```json
{
  "status": "no_waypoint",
  "message": "No waypoint has been set yet",
  "waypoint": null
}
```

### No GPS Data
```json
{
  "status": "error",
  "message": "No GPS data available"
}
```

### No Azimuth (Compass)
```json
{
  "status": "error",
  "message": "No azimuth (compass heading) available"
}
```

---

## API Summary

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/safe-coordinates` | POST | Set safe waypoint | Mobile App |
| `/waypoint` | GET | Fetch waypoint | ESP32 |
| `/calculate-direction` | GET | Get direction to waypoint | ESP32 |
| `/history` | GET | Get GPS history | ESP32 |
| `/coordinates` | POST | Send GPS data | Phone |

---

## Next Steps

1. **Integrate into mobile app** - Add UI to set safe waypoints
2. **Update ESP32 code** - Fetch waypoint and calculate direction
3. **Test with hardware** - Verify LED indicators work correctly
4. **Add arrival detection** - Notify when worker reaches waypoint
