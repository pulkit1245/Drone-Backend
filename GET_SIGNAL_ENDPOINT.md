# GET /get-signal Endpoint

## 📡 Overview

Retrieve the latest signal strength data from RSSI readings sent by ESP32 helmets.

## 🔧 Endpoint

**URL**: `GET /get-signal`

**Base URL**: `https://adahrs-ip-157-49-184-22.tunnelmole.net/get-signal`

## 📥 Request

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `helmet_id` | integer | ❌ No | Filter by specific helmet ID |

### Examples

**Get latest signal from any helmet:**
```bash
curl http://localhost:8001/get-signal
```

**Get latest signal from specific helmet:**
```bash
curl "http://localhost:8001/get-signal?helmet_id=9001"
```

## 📤 Response

### Success (200)

```json
{
  "status": "ok",
  "data": {
    "timestamp": "2025-11-27T13:16:13.194824",
    "helmet_id": 9001,
    "rssi": -46,
    "signal": 88,
    "client_ip": "127.0.0.1"
  }
}
```

**Fields:**
- `timestamp` (string): ISO 8601 timestamp when data was received
- `helmet_id` (integer): Unique helmet identifier
- `rssi` (integer): Signal strength in dBm (-90 to -40)
- `signal` (integer): Signal strength as percentage (0-100)
- `client_ip` (string): IP address of the helmet/ESP32

### Error (404)

**No data available:**
```json
{
  "status": "error",
  "message": "No RSSI data available"
}
```

**Helmet not found:**
```json
{
  "status": "error",
  "message": "No data found for helmet_id 9001"
}
```

## 🎯 Use Cases

### 1. Monitor Helmet Connection
```bash
# Check if helmet is still connected
curl "http://localhost:8001/get-signal?helmet_id=1234"
```

### 2. Get Signal Quality
```bash
# Get current signal strength
curl http://localhost:8001/get-signal | jq '.data.signal'
# Output: 88
```

### 3. Check Connection Status
```python
import requests

response = requests.get("http://localhost:8001/get-signal?helmet_id=1234")
data = response.json()

if data["status"] == "ok":
    signal = data["data"]["signal"]
    if signal > 70:
        print("Excellent connection")
    elif signal > 50:
        print("Good connection")
    else:
        print("Weak connection")
```

## 📱 ESP32/Arduino Example

```cpp
#include <HTTPClient.h>
#include <ArduinoJson.h>

void checkSignalStrength() {
    HTTPClient http;
    http.begin("https://adahrs-ip-157-49-184-22.tunnelmole.net/get-signal?helmet_id=1234");
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String payload = http.getString();
        
        StaticJsonDocument<512> doc;
        deserializeJson(doc, payload);
        
        if (strcmp(doc["status"], "ok") == 0) {
            int helmetId = doc["data"]["helmet_id"];
            int rssi = doc["data"]["rssi"];
            int signal = doc["data"]["signal"];
            
            Serial.printf("Helmet %d: Signal %d%% (%d dBm)\n", 
                          helmetId, signal, rssi);
            
            // Take action based on signal strength
            if (signal < 30) {
                Serial.println("WARNING: Weak signal!");
            }
        }
    }
    
    http.end();
}
```

## 🔄 Data Flow

```
ESP32 Helmet ──POST /rssi──> Server ──Stores──> rssi_log.csv
                                         ↓
                              Drone ──GET /get-signal──> Latest Data
```

## 📊 Signal Strength Guide

| Signal % | RSSI (dBm) | Quality | Description |
|----------|------------|---------|-------------|
| 90-100% | -40 to -45 | ⭐⭐⭐⭐⭐ | Excellent |
| 70-89% | -46 to -56 | ⭐⭐⭐⭐ | Very Good |
| 50-69% | -57 to -67 | ⭐⭐⭐ | Good |
| 30-49% | -68 to -78 | ⭐⭐ | Fair |
| 0-29% | -79 to -90 | ⭐ | Weak |

## 🧪 Testing

### Test 1: Send signal data
```bash
curl -X POST http://localhost:8001/rssi \
  -H "Content-Type: application/json" \
  -d '{"helmet_id": 1234, "signal": 75}'
```

### Test 2: Retrieve signal data
```bash
curl http://localhost:8001/get-signal
```

**Expected Output:**
```json
{
  "status": "ok",
  "data": {
    "helmet_id": 1234,
    "rssi": -52,
    "signal": 75,
    ...
  }
}
```

### Test 3: Filter by helmet
```bash
curl "http://localhost:8001/get-signal?helmet_id=1234"
```

## 💡 Tips

1. **Polling**: Poll this endpoint every few seconds to monitor signal strength
2. **Timeout Detection**: If timestamp is old (>10 seconds), helmet may be disconnected
3. **Multiple Helmets**: Use `helmet_id` parameter to track specific helmets
4. **Signal Threshold**: Set alerts when signal drops below threshold (e.g., 30%)

## 🔍 Monitoring Example

```python
import requests
import time
from datetime import datetime, timedelta

def monitor_helmet(helmet_id, interval=5):
    """Monitor helmet signal strength continuously."""
    url = f"http://localhost:8001/get-signal?helmet_id={helmet_id}"
    
    while True:
        try:
            response = requests.get(url)
            data = response.json()
            
            if data["status"] == "ok":
                signal = data["data"]["signal"]
                timestamp = datetime.fromisoformat(data["data"]["timestamp"])
                age = (datetime.utcnow() - timestamp).total_seconds()
                
                print(f"Helmet {helmet_id}: {signal}% (age: {age:.1f}s)")
                
                # Alert if signal is weak
                if signal < 30:
                    print("⚠️  WARNING: Weak signal!")
                
                # Alert if data is stale
                if age > 10:
                    print("⚠️  WARNING: Stale data!")
            else:
                print(f"❌ Error: {data['message']}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        time.sleep(interval)

# Monitor helmet 1234 every 5 seconds
monitor_helmet(1234, interval=5)
```

## ✅ Summary

- ✅ Get latest RSSI/signal data
- ✅ Filter by helmet ID
- ✅ Returns both dBm and percentage
- ✅ Includes timestamp and IP
- ✅ Perfect for monitoring connection quality

The endpoint is ready to use! 📡✨
