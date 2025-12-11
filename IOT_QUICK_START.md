# IoT Controller Setup - Quick Start Guide

## 📋 Overview
The IoT Controller has been successfully integrated into your SIH Backend. It provides endpoints for:
- ✅ Triggering variables from mobile apps
- ✅ Receiving button counts from IoT devices (ESP32)
- ✅ Checking trigger status via GET requests

## 🚀 Quick Start

### 1. Restart the Server
The IoT controller has been added to `server.py`. You need to restart the server to load the new endpoints:

```bash
# Stop the current server (Ctrl+C in the terminal where it's running)
# Then restart:
python3 server.py
```

### 2. Test the Endpoints
Once the server is restarted, run the test script:

```bash
python3 test_iot.py
```

Expected output: All 8 tests should pass ✓

### 3. Access IoT Endpoints
All IoT endpoints are available at: `http://localhost:8001/iot/`

## 📡 Available Endpoints

### 1. Trigger Variable (POST)
**Use Case:** Mobile app sends a command/alert to IoT devices

```bash
curl -X POST http://localhost:8001/iot/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "emergency_alert",
    "triggered": true,
    "triggered_by": "mobile_app"
  }'
```

### 2. Send Button Counts (POST)
**Use Case:** ESP32 with 3 buttons sends press counts

```bash
curl -X POST http://localhost:8001/iot/button-count \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32_001",
    "button_1": 10,
    "button_2": 5,
    "button_3": 15
  }'
```

### 3. Check Status (GET)
**Use Case:** Check if a variable is triggered

```bash
# Check specific variable
curl http://localhost:8001/iot/status?variable_name=emergency_alert

# Check specific device button counts
curl http://localhost:8001/iot/status?device_id=esp32_001

# Get all status
curl http://localhost:8001/iot/status
```

### 4. Health Check (GET)
```bash
curl http://localhost:8001/iot/health
```

## 🔧 ESP32 Setup

### Hardware Connections
```
ESP32 Pin    →    Component
GPIO 12      →    Button 1 (with pull-up resistor)
GPIO 14      →    Button 2 (with pull-up resistor)
GPIO 27      →    Button 3 (with pull-up resistor)
GPIO 2       →    Built-in LED (status indicator)
```

### Arduino Sketch
Upload `esp32_iot_buttons.ino` to your ESP32:

1. Open Arduino IDE
2. Install required libraries:
   - WiFi (built-in)
   - HTTPClient (built-in)
   - ArduinoJson (install from Library Manager)
3. Update WiFi credentials in the sketch:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
4. Update server URL:
   ```cpp
   const char* serverUrl = "http://YOUR_SERVER_IP:8001";
   ```
5. Upload to ESP32

### ESP32 Behavior
- **Button Press:** LED flashes briefly
- **Data Sent:** LED blinks for 100ms
- **Alert Triggered:** LED blinks rapidly 3 times
- **WiFi Connected:** LED blinks rapidly 5 times

## 📱 Mobile App Integration (Android/Kotlin)

### Trigger Emergency Alert
```kotlin
suspend fun triggerEmergencyAlert() {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("variable_name", "emergency_alert")
        put("triggered", true)
        put("triggered_by", "android_app")
    }
    
    val request = Request.Builder()
        .url("http://your-server:8001/iot/trigger")
        .post(json.toString().toRequestBody("application/json".toMediaType()))
        .build()
    
    client.newCall(request).execute()
}
```

### Check Trigger Status
```kotlin
suspend fun checkTriggerStatus(): Boolean {
    val client = OkHttpClient()
    val request = Request.Builder()
        .url("http://your-server:8001/iot/status?variable_name=emergency_alert")
        .get()
        .build()
    
    val response = client.newCall(request).execute()
    val json = JSONObject(response.body?.string() ?: "")
    return json.getBoolean("triggered")
}
```

### Get Button Counts
```kotlin
suspend fun getButtonCounts(deviceId: String): Map<String, Int> {
    val client = OkHttpClient()
    val request = Request.Builder()
        .url("http://your-server:8001/iot/status?device_id=$deviceId")
        .get()
        .build()
    
    val response = client.newCall(request).execute()
    val json = JSONObject(response.body?.string() ?: "")
    val counts = json.getJSONObject("counts")
    
    return mapOf(
        "button_1" to counts.getInt("button_1"),
        "button_2" to counts.getInt("button_2"),
        "button_3" to counts.getInt("button_3")
    )
}
```

## 🎯 Use Case Examples

### Example 1: Emergency Alert System
1. **Mobile App:** User presses emergency button
2. **App → Server:** POST `/iot/trigger` with `emergency_alert = true`
3. **ESP32 → Server:** Periodically checks `/iot/status?variable_name=emergency_alert`
4. **ESP32:** When triggered, activates buzzer/LED/relay

### Example 2: Button Monitoring Dashboard
1. **ESP32:** Counts button presses locally
2. **ESP32 → Server:** Sends counts every 5 seconds to `/iot/button-count`
3. **Dashboard:** Queries `/iot/status` to display all device button counts
4. **Dashboard:** Shows real-time button press statistics

### Example 3: Multi-Device Coordination
1. **Device 1:** Sends button counts
2. **Device 2:** Checks trigger status
3. **Device 3:** Monitors other devices via `/iot/status`
4. **Mobile App:** Controls all devices via trigger endpoints

## 📊 Data Storage

### Files Created
- `iot_triggers.csv` - Log of all variable trigger events
- `iot_button_counts.csv` - Log of all button count updates
- `iot_state.json` - Current state (in-memory cache)

### CSV Format Examples

**iot_triggers.csv:**
```csv
timestamp_iso,variable_name,action,triggered_by,client_ip
2025-12-11T17:00:00,emergency_alert,trigger,app_user_123,192.168.1.50
```

**iot_button_counts.csv:**
```csv
timestamp_iso,device_id,button_1,button_2,button_3,client_ip
2025-12-11T17:00:00,esp32_001,5,3,7,192.168.1.100
```

## 🔍 Troubleshooting

### Server Not Responding
```bash
# Check if server is running
lsof -i :8001

# Restart server
python3 server.py
```

### ESP32 Not Connecting
1. Check WiFi credentials
2. Verify server IP address
3. Check Serial Monitor for error messages
4. Ensure ESP32 and server are on same network

### 404 Errors
- Make sure server has been restarted after adding IoT controller
- Verify endpoint URLs include `/iot/` prefix
- Check server logs for errors

## 📚 Documentation Files

1. **IOT_API_DOCUMENTATION.md** - Complete API reference
2. **iot_controller.py** - Backend implementation
3. **esp32_iot_buttons.ino** - ESP32 Arduino sketch
4. **test_iot.py** - Test script for all endpoints

## ✅ Next Steps

1. ✅ Restart the server
2. ✅ Run test script to verify endpoints
3. ✅ Upload ESP32 sketch (if using hardware)
4. ✅ Integrate into your mobile app
5. ✅ Test end-to-end workflow

## 🎉 You're Ready!

The IoT controller is now fully integrated and ready to use. Start by restarting the server and running the tests!
