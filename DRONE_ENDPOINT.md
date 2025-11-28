# Drone Coordinates Endpoint

## 🎯 Overview

Simple endpoint that returns GPS coordinates as a double array, optimized for drone/ESP32 integration.

## 📡 Endpoint

**GET** `/get-coordinates-drone`

## 🔧 Usage

### cURL
```bash
# Get fresh coordinates
curl http://localhost:5000/get-coordinates-drone

# Get cached coordinates (faster, max 60s old)
curl "http://localhost:5000/get-coordinates-drone?cached=true"
```

### Python
```python
import requests

response = requests.get("http://localhost:5000/get-coordinates-drone")
coords = response.json()

latitude, longitude, reserved, accuracy = coords

print(f"Lat: {latitude}, Lon: {longitude}, Accuracy: ±{accuracy}m")
```

### ESP32/Arduino
```cpp
#include <HTTPClient.h>
#include <ArduinoJson.h>

HTTPClient http;
http.begin("http://SERVER_IP:5000/get-coordinates-drone?cached=true");
int httpCode = http.GET();

if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<200> doc;
    deserializeJson(doc, payload);
    
    double latitude = doc[0];
    double longitude = doc[1];
    double reserved = doc[2];
    double accuracy = doc[3];
    
    // Use coordinates...
}
http.end();
```

## 📊 Response Format

### Success (HTTP 200)
```json
[37.7749, -122.4194, 1.0, 65.0]
```

**Array Structure:**
- `[0]` - **Latitude** (degrees, -90 to 90)
- `[1]` - **Longitude** (degrees, -180 to 180)
- `[2]` - **Reserved** (always 1.0, for future use)
- `[3]` - **Accuracy** (meters, horizontal accuracy)

### Error (HTTP 500)
```json
[0.0, 0.0, 0.0, 0.0]
```

## ⚙️ Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cached` | boolean | `false` | Use cached location (max 60s old) for faster response |

## 🚀 Examples

### Example 1: Basic Request
```bash
curl http://localhost:5000/get-coordinates-drone
# Response: [37.7749, -122.4194, 1.0, 65.0]
```

### Example 2: Fast Polling (Cached)
```bash
# Use cached for frequent polling (recommended for drones)
curl "http://localhost:5000/get-coordinates-drone?cached=true"
# Response: [37.7749, -122.4194, 1.0, 65.0]
```

### Example 3: Python Parsing
```python
import requests

def get_drone_coordinates(use_cache=True):
    url = "http://localhost:5000/get-coordinates-drone"
    params = {"cached": "true"} if use_cache else {}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        coords = response.json()
        return {
            'latitude': coords[0],
            'longitude': coords[1],
            'reserved': coords[2],
            'accuracy': coords[3]
        }
    return None

# Usage
coords = get_drone_coordinates(use_cache=True)
if coords:
    print(f"Position: ({coords['latitude']}, {coords['longitude']})")
    print(f"Accuracy: ±{coords['accuracy']}m")
```

## 🧪 Testing

### Test with Python Script
```bash
python3 test_drone_coordinates.py
```

Options:
1. Basic endpoint test
2. Simulate drone polling (30 seconds)
3. Custom duration polling

### Manual Testing
```bash
# Start server
python3 server.py

# In another terminal, test endpoint
curl http://localhost:5000/get-coordinates-drone
```

## 📝 Notes

- **Caching**: Use `cached=true` for frequent polling (e.g., every 1-2 seconds) to reduce latency
- **Fresh Data**: Omit `cached` parameter when you need the most up-to-date location
- **First Request**: May take 2-5 seconds to acquire GPS lock
- **Accuracy**: Typically 10-100 meters depending on available signals
- **Error Handling**: Check for `[0.0, 0.0, 0.0, 0.0]` response to detect errors

## 🔗 Related Files

- **Server**: `server.py` - Flask server with endpoint implementation
- **Test Script**: `test_drone_coordinates.py` - Python test utilities
- **ESP32 Example**: `esp32_get_coordinates.ino` - Arduino/ESP32 example code
- **Location Service**: `location_service.py` - Core location functionality

## 💡 Use Cases

1. **Drone Navigation**: Get home base coordinates for return-to-home functionality
2. **Geofencing**: Define boundaries based on server location
3. **Tracking**: Log drone position relative to server location
4. **Waypoint Navigation**: Use server location as a waypoint
5. **Distance Calculation**: Calculate distance from drone to server

## ⚠️ Requirements

Before using this endpoint, ensure:
1. Location service tools are installed (`./setup_location.sh`)
2. Location permissions are granted to Terminal
3. Server is running (`python3 server.py`)
4. Both devices are on the same network

## 🎯 Performance

| Scenario | Response Time | Recommended For |
|----------|---------------|-----------------|
| Fresh location | 2-5 seconds | Initial request, critical accuracy |
| Cached location | <100ms | Frequent polling, real-time updates |

## 🔄 Comparison with /location Endpoint

| Feature | `/get-coordinates-drone` | `/location` |
|---------|-------------------------|-------------|
| Response Format | Simple array | JSON object |
| Data Included | Coordinates only | Coordinates + metadata |
| Use Case | Embedded systems | Web/mobile apps |
| Parsing Complexity | Low | Medium |
| Response Size | Minimal | Larger |
