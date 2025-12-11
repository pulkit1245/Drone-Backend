# IoT Controller API Documentation

## Overview
The IoT Controller provides endpoints for managing IoT device interactions, including variable triggering from mobile apps and button count monitoring from IoT devices.

## Base URL
All IoT endpoints are prefixed with `/iot`

Example: `http://your-server:8001/iot/trigger`

---

## Endpoints

### 1. Trigger Variable (POST)
**Endpoint:** `/iot/trigger`

**Description:** Trigger a variable from the mobile app. This can be used to send commands or alerts to IoT devices.

**Request Body:**
```json
{
  "variable_name": "emergency_alert",
  "triggered": true,
  "triggered_by": "app_user_123"
}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "variable_name": "emergency_alert",
  "triggered": true,
  "timestamp": "2025-12-11T17:00:00"
}
```

**Example Usage:**
```bash
curl -X POST http://localhost:8001/iot/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "variable_name": "emergency_alert",
    "triggered": true,
    "triggered_by": "mobile_app"
  }'
```

---

### 2. Receive Button Count (POST)
**Endpoint:** `/iot/button-count`

**Description:** Receive button press counts from IoT devices (e.g., ESP32 with 3 buttons).

**Request Body:**
```json
{
  "device_id": "esp32_001",
  "button_1": 5,
  "button_2": 3,
  "button_3": 7
}
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "device_id": "esp32_001",
  "counts": {
    "button_1": 5,
    "button_2": 3,
    "button_3": 7
  },
  "timestamp": "2025-12-11T17:00:00"
}
```

**Example Usage:**
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

---

### 3. Get Status (GET)
**Endpoint:** `/iot/status`

**Description:** Check if variables are triggered and get button counts.

**Query Parameters:**
- `variable_name` (optional): Get status of specific variable
- `device_id` (optional): Get button counts for specific device

**Response - All Data (200 OK):**
```json
{
  "status": "ok",
  "variables": {
    "emergency_alert": {
      "triggered": true,
      "timestamp": "2025-12-11T17:00:00",
      "triggered_by": "app_user_123"
    }
  },
  "button_counts": {
    "esp32_001": {
      "button_1": 5,
      "button_2": 3,
      "button_3": 7,
      "last_update": "2025-12-11T17:00:00"
    }
  }
}
```

**Response - Specific Variable (200 OK):**
```json
{
  "status": "ok",
  "variable_name": "emergency_alert",
  "triggered": true,
  "timestamp": "2025-12-11T17:00:00",
  "triggered_by": "app_user_123"
}
```

**Response - Specific Device (200 OK):**
```json
{
  "status": "ok",
  "device_id": "esp32_001",
  "counts": {
    "button_1": 5,
    "button_2": 3,
    "button_3": 7
  },
  "last_update": "2025-12-11T17:00:00"
}
```

**Example Usage:**
```bash
# Get all status
curl http://localhost:8001/iot/status

# Get specific variable status
curl http://localhost:8001/iot/status?variable_name=emergency_alert

# Get specific device button counts
curl http://localhost:8001/iot/status?device_id=esp32_001
```

---

### 4. Reset Data (POST)
**Endpoint:** `/iot/reset`

**Description:** Reset all IoT data (variables and button counts).

**Query Parameters:**
- `confirm=yes` (required): Safety confirmation
- `type` (optional): `variables`, `buttons`, or `all` (default: `all`)

**Response (200 OK):**
```json
{
  "status": "ok",
  "message": "IoT data reset successfully (type: all)",
  "reset": {
    "variables": true,
    "button_counts": true
  }
}
```

**Example Usage:**
```bash
# Reset all data
curl -X POST http://localhost:8001/iot/reset?confirm=yes

# Reset only variables
curl -X POST http://localhost:8001/iot/reset?confirm=yes&type=variables

# Reset only button counts
curl -X POST http://localhost:8001/iot/reset?confirm=yes&type=buttons
```

---

### 5. Health Check (GET)
**Endpoint:** `/iot/health`

**Description:** Check IoT controller health and status.

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "IoT Controller",
  "variables_count": 1,
  "devices_count": 1,
  "timestamp": "2025-12-11T17:00:00"
}
```

**Example Usage:**
```bash
curl http://localhost:8001/iot/health
```

---

## Use Cases

### Use Case 1: Mobile App Triggers Emergency Alert
1. Mobile app sends POST to `/iot/trigger`:
   ```json
   {
     "variable_name": "emergency_alert",
     "triggered": true,
     "triggered_by": "user_mobile_app"
   }
   ```

2. ESP32 periodically checks `/iot/status?variable_name=emergency_alert`

3. When triggered, ESP32 activates buzzer/LED/relay

### Use Case 2: ESP32 Button Monitoring
1. ESP32 counts button presses locally

2. Every 5 seconds, sends counts to `/iot/button-count`:
   ```json
   {
     "device_id": "esp32_001",
     "button_1": 10,
     "button_2": 5,
     "button_3": 15
   }
   ```

3. Mobile app can query `/iot/status?device_id=esp32_001` to see button counts

### Use Case 3: Dashboard Monitoring
1. Web dashboard calls `/iot/status` to get all data

2. Displays:
   - All triggered variables
   - All device button counts
   - Last update timestamps

---

## Data Persistence

### Files Created:
- `iot_triggers.csv`: Log of all variable trigger events
- `iot_button_counts.csv`: Log of all button count updates
- `iot_state.json`: Current state (in-memory cache)

### CSV Format:

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

---

## Error Responses

### 400 Bad Request
```json
{
  "status": "error",
  "message": "Invalid JSON"
}
```

### 404 Not Found
```json
{
  "status": "error",
  "message": "Variable not found"
}
```

---

## Integration Example (Android/Kotlin)

```kotlin
// Trigger variable from app
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

// Check trigger status
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

---

## Testing

### Start the server:
```bash
python server.py
```

### Test with curl:
```bash
# Trigger a variable
curl -X POST http://localhost:8001/iot/trigger \
  -H "Content-Type: application/json" \
  -d '{"variable_name": "test_alert", "triggered": true, "triggered_by": "test"}'

# Check status
curl http://localhost:8001/iot/status?variable_name=test_alert

# Send button counts
curl -X POST http://localhost:8001/iot/button-count \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test_device", "button_1": 1, "button_2": 2, "button_3": 3}'

# Get all status
curl http://localhost:8001/iot/status
```
