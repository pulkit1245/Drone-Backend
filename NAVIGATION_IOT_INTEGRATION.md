# ESP32 Navigation with IoT Trigger - Integration Guide

## 🎯 Overview

This system integrates the ESP32 navigation with the IoT trigger mechanism, allowing you to:
1. **Start navigation from mobile app** - Trigger via POST `/iot/trigger`
2. **Auto-start with button presses** - Press any button 3 times (or multiples of 3)
3. **Monitor trigger status** - ESP32 checks every second via GET `/iot/trigger`
4. **Navigate to destination** - Shows direction using 4 LEDs when active

## 🔧 Hardware Setup

### Components Required
- ESP32 Development Board
- 4 LEDs (for N/E/S/W directions)
- 3 Push Buttons
- Resistors (220Ω for LEDs, 10kΩ for buttons if not using internal pull-ups)

### Pin Connections

**LEDs:**
```
LED_N (North/Front)  → GPIO 25
LED_E (East/Right)   → GPIO 26
LED_S (South/Back)   → GPIO 27
LED_W (West/Left)    → GPIO 14
```

**Buttons:**
```
BUTTON_1 → GPIO 12 (with internal pull-up)
BUTTON_2 → GPIO 13 (with internal pull-up)
BUTTON_3 → GPIO 15 (with internal pull-up)
```

### Wiring Diagram
```
ESP32                Components
-----                ----------
GPIO 25 ----[220Ω]---- LED_N ---- GND
GPIO 26 ----[220Ω]---- LED_E ---- GND
GPIO 27 ----[220Ω]---- LED_S ---- GND
GPIO 14 ----[220Ω]---- LED_W ---- GND

GPIO 12 ---- BUTTON_1 ---- GND
GPIO 13 ---- BUTTON_2 ---- GND
GPIO 15 ---- BUTTON_3 ---- GND
```

## 📡 Backend Setup

### 1. Update Server Configuration

The IoT controller now supports both POST and GET methods on `/iot/trigger`:

**POST** - Trigger/reset a variable:
```bash
curl -X POST http://localhost:8001/iot/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "start_navigation",
    "triggered": true,
    "triggered_by": "mobile_app"
  }'
```

**GET** - Check trigger status:
```bash
curl "http://localhost:8001/iot/trigger?variable_name=start_navigation"
```

### 2. Restart Server

**Important:** You must restart the server for the new GET endpoint to work:

```bash
# Stop current server (Ctrl+C)
python3 server.py
```

### 3. Test the Endpoint

```bash
python3 test_navigation_trigger.py
```

## 🚀 ESP32 Setup

### 1. Install Required Libraries

In Arduino IDE, install:
- **WiFi** (built-in)
- **HTTPClient** (built-in)
- **ArduinoJson** (Library Manager → search "ArduinoJson" by Benoit Blanchon)

### 2. Configure the Sketch

Open `esp32_navigation_with_iot.ino` and update:

```cpp
// WiFi credentials
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Server IP (your laptop/phone running the server)
const char* SERVER_IP   = "192.168.1.100";  // Change to your server IP

// Destination coordinates
const float destLat = 28.7536382;  // Your target latitude
const float destLon = 77.4983311;  // Your target longitude
```

### 3. Upload to ESP32

1. Connect ESP32 via USB
2. Select board: **Tools → Board → ESP32 Dev Module**
3. Select port: **Tools → Port → /dev/cu.usbserial-XXXX**
4. Click **Upload**

## 🎮 How It Works

### System States

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM IDLE                          │
│  - LEDs OFF                                             │
│  - Monitoring buttons                                   │
│  - Checking trigger status every 1 second               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  TRIGGER CONDITIONS:            │
        │  1. Button count = 3, 6, 9...   │
        │  2. App triggers via POST       │
        └─────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              NAVIGATION ACTIVE                          │
│  - Fetching GPS data every 1 second                     │
│  - Calculating bearing to destination                   │
│  - Showing direction on LEDs                            │
│  - Checking for arrival (within 4m)                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  STOP CONDITIONS:               │
        │  1. App resets trigger          │
        │  2. Arrival at destination      │
        └─────────────────────────────────┘
```

### Trigger Flow

#### Method 1: Button Press Auto-Trigger

```
User presses button → Button count incremented
                    ↓
        Count = 3, 6, 9, 12... ?
                    ↓ YES
        POST /iot/trigger (triggered=true)
                    ↓
        systemInitialized = true
                    ↓
        Navigation starts
```

#### Method 2: Mobile App Trigger

```
Mobile App → POST /iot/trigger (triggered=true)
                    ↓
        Server updates state
                    ↓
ESP32 checks → GET /iot/trigger?variable_name=start_navigation
                    ↓
        Response: {"triggered": true}
                    ↓
        systemInitialized = true
                    ↓
        Navigation starts
```

### LED Behavior

**When System Idle:**
- All LEDs OFF

**When WiFi Connecting:**
- All LEDs blink 3 times rapidly

**When Triggered:**
- All LEDs flash 5 times rapidly

**During Navigation:**
- LEDs show direction to destination:
  - **N only** → Target straight ahead
  - **N + E** → Target ahead-right (NE)
  - **E only** → Target to the right
  - **S + E** → Target behind-right (SE)
  - **S only** → Target behind
  - **S + W** → Target behind-left (SW)
  - **W only** → Target to the left
  - **N + W** → Target ahead-left (NW)

**When Arrived (within 4m):**
- All LEDs ON continuously

## 📱 Mobile App Integration

### Trigger Navigation

```kotlin
suspend fun startNavigation() {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("variable_name", "start_navigation")
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

### Stop Navigation

```kotlin
suspend fun stopNavigation() {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("variable_name", "start_navigation")
        put("triggered", false)
        put("triggered_by", "android_app")
    }
    
    val request = Request.Builder()
        .url("http://your-server:8001/iot/trigger")
        .post(json.toString().toRequestBody("application/json".toMediaType()))
        .build()
    
    client.newCall(request).execute()
}
```

### Check Navigation Status

```kotlin
suspend fun isNavigationActive(): Boolean {
    val client = OkHttpClient()
    val request = Request.Builder()
        .url("http://your-server:8001/iot/trigger?variable_name=start_navigation")
        .get()
        .build()
    
    val response = client.newCall(request).execute()
    val json = JSONObject(response.body?.string() ?: "")
    return json.getBoolean("triggered")
}
```

## 🧪 Testing

### Test 1: Button Auto-Trigger

1. Upload sketch to ESP32
2. Open Serial Monitor (115200 baud)
3. Press any button 3 times
4. Watch Serial Monitor for "AUTO-TRIGGER" message
5. LEDs should flash 5 times
6. Navigation should start

### Test 2: App Trigger

1. Ensure ESP32 is running
2. From your computer, run:
   ```bash
   curl -X POST http://localhost:8001/iot/trigger \
     -H "Content-Type: application/json" \
     -d '{"variable_name": "start_navigation", "triggered": true, "triggered_by": "test"}'
   ```
3. Within 1 second, ESP32 should detect trigger
4. LEDs should flash 3 times
5. Navigation should start

### Test 3: Complete Workflow

```bash
python3 test_navigation_trigger.py
```

Expected output:
- ✓ GET endpoint returns trigger status
- ✓ POST endpoint sets trigger
- ✓ ESP32 can check status
- ✓ Navigation workflow works end-to-end

## 🐛 Troubleshooting

### ESP32 Not Connecting to WiFi
- Check SSID and password
- Ensure ESP32 and server are on same network
- Check Serial Monitor for connection errors

### Navigation Not Starting
- Verify server is running: `lsof -i :8001`
- Check trigger status: `curl "http://localhost:8001/iot/trigger?variable_name=start_navigation"`
- Ensure `systemInitialized` is true (check Serial Monitor)

### LEDs Not Showing Direction
- Verify GPS data is being received from `/history` endpoint
- Check Serial Monitor for GPS coordinates
- Ensure phone is sending GPS data

### Button Presses Not Counted
- Check button wiring (should connect to GND when pressed)
- Verify pull-up resistors are enabled
- Watch Serial Monitor for button press messages

## 📊 Serial Monitor Output

### Normal Operation
```
=== ESP32 Navigation with IoT Trigger ===
Press any button 3 times to start navigation
Or trigger via app: POST /iot/trigger

Connecting to WiFi: BIT-SIH
✓ WiFi Connected!
IP Address: 192.168.1.105
Server: http://172.16.7.78:8001

Button 1 pressed! Count: 1
Button 1 pressed! Count: 2
Button 1 pressed! Count: 3

*** AUTO-TRIGGER: Button count reached multiple of 3! ***
Total button presses: 3

--- Triggering Navigation System ---
URL: http://172.16.7.78:8001/iot/trigger
Payload: {"variable_name":"start_navigation","triggered":true,"triggered_by":"esp32_nav_001"}
✓ Navigation system triggered successfully!

---- Latest Phone Nav Data ----
Lat: 28.753638
Lon: 77.498331
Azim: 45.23
Speed: 1.20
--------------------------------

→ Bearing: 90.5° | Diff: 45.3° | Dist: 125.4 m
```

## 🎯 Next Steps

1. ✅ Restart server to enable GET endpoint
2. ✅ Upload ESP32 sketch
3. ✅ Test button auto-trigger
4. ✅ Test app trigger
5. ✅ Integrate into your mobile app
6. ✅ Test complete navigation workflow

## 📚 Related Files

- `iot_controller.py` - Backend IoT controller
- `esp32_navigation_with_iot.ino` - ESP32 sketch
- `test_navigation_trigger.py` - Test script
- `IOT_API_DOCUMENTATION.md` - Complete API reference
