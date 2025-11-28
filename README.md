# ESP32 RSSI Data Logger

A Flask-based server for receiving and logging RSSI (Received Signal Strength Indicator) data from ESP32 helmet devices, with a comprehensive viewer application.

## Files

- **server.py** - Flask server that receives RSSI data via HTTP POST
- **main.py** - Interactive viewer for displaying RSSI data
- **rssi_log.csv** - Auto-generated CSV log file (created on first run)

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Location Service Tools (Optional)

To enable GPS coordinate tracking from your MacBook:

```bash
# Run the automated setup script
./setup_location.sh
```

Or install manually:

```bash
# Option 1: CoreLocationCLI (recommended)
brew install corelocationcli

# Option 2: whereami (alternative)
brew install whereami
```

**Grant Location Permissions:**
1. Go to **System Preferences → Security & Privacy → Privacy → Location Services**
2. Enable Location Services
3. Enable for **Terminal** (or your Python IDE/application)

### Running the Server

Start the Flask server to begin receiving RSSI data:

```bash
python server.py
```

The server will:
- Listen on `0.0.0.0:5000` (accessible from your local network)
- Create `rssi_log.csv` if it doesn't exist
- Log all incoming RSSI readings to the CSV file
- Print readings to console

### Running the Viewer

In a separate terminal, run the main viewer:

```bash
python main.py
```

The viewer offers multiple display modes:

1. **Summary View** - Statistics grouped by helmet ID (auto-refreshes every 5 seconds)
2. **Live View** - Real-time stream of incoming readings
3. **Recent Readings** - View last 10 or 50 readings

## API Endpoint

### POST /rssi

Send RSSI data from your ESP32 device:

**Request:**
```json
{
  "helmet_id": 1234,
  "rssi": -67
}
```

**Response (Success):**
```json
{
  "status": "ok"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "helmet_id and rssi required"
}
```

### GET /location

Get current GPS coordinates from the MacBook:

**Request:**
```bash
curl http://localhost:5000/location

# With query parameters
curl "http://localhost:5000/location?method=auto&cached=true"
```

**Query Parameters:**
- `method` (optional): `auto` (default), `corelocation`, `whereami`, or `applescript`
- `cached` (optional): `true` to use cached location (max 60s old), `false` (default) for fresh location

**Response (Success):**
```json
{
  "status": "ok",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy": 65.0,
    "timestamp": "2025-11-27T11:37:23.123456"
  },
  "formatted": "37.774900°N, 122.419400°W (±65.0m)",
  "maps_url": "https://www.google.com/maps?q=37.7749,-122.4194"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Unable to get location. Ensure location services are enabled and you have the required tools installed."
}
```


### GET /get-coordinates-drone

Get current GPS coordinates as a simple array (optimized for drone integration):

**Request:**
```bash
curl http://localhost:5000/get-coordinates-drone

# With cached location (faster)
curl "http://localhost:5000/get-coordinates-drone?cached=true"
```

**Query Parameters:**
- `cached` (optional): `true` to use cached location (max 60s old), `false` (default) for fresh location

**Response (Success):**
```json
[37.7749, -122.4194, 1.0, 65.0]
```

Array format: `[latitude, longitude, 1, accuracy]`
- Index 0: Latitude (degrees)
- Index 1: Longitude (degrees)
- Index 2: Always 1.0 (reserved)
- Index 3: Accuracy (meters)

**Response (Error):**
```json
[0.0, 0.0, 0.0, 0.0]
```



### ESP32 Example Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/rssi";
const int helmetId = 1234;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    
    int rssi = WiFi.RSSI();
    String payload = "{\"helmet_id\":" + String(helmetId) + 
                     ",\"rssi\":" + String(rssi) + "}";
    
    int httpCode = http.POST(payload);
    
    if (httpCode > 0) {
      Serial.printf("RSSI: %d dBm, Response: %d\n", rssi, httpCode);
    } else {
      Serial.printf("Error: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
  }
  
  delay(5000); // Send every 5 seconds
}
```

## Signal Strength Guide

The viewer displays signal strength using visual bars and descriptions:

| RSSI Range | Bars | Description |
|------------|------|-------------|
| ≥ -50 dBm  | █████ | Excellent   |
| -50 to -60 | ████░ | Good        |
| -60 to -70 | ███░░ | Fair        |
| -70 to -80 | ██░░░ | Weak        |
| < -80 dBm  | █░░░░ | Very Weak   |

## Data Format

The CSV log file contains the following columns:

- **timestamp_iso** - ISO 8601 timestamp (UTC)
- **helmet_id** - Unique identifier for the helmet
- **rssi** - Signal strength in dBm
- **client_ip** - IP address of the ESP32 device

## Testing

You can test the server using curl:

```bash
curl -X POST http://localhost:5000/rssi \
  -H "Content-Type: application/json" \
  -d '{"helmet_id": 1234, "rssi": -67}'
```

Or using Python:

```python
import requests

response = requests.post(
    "http://localhost:5000/rssi",
    json={"helmet_id": 1234, "rssi": -67}
)
print(response.json())
```

## Features

### Server Features
- ✅ RESTful API endpoint for RSSI data
- ✅ GPS location tracking from MacBook
- ✅ CSV logging with timestamps
- ✅ Client IP tracking
- ✅ Input validation
- ✅ Network-accessible (LAN)

### Viewer Features
- ✅ Multiple display modes (summary, live, recent)
- ✅ Visual signal strength indicators
- ✅ Statistics by helmet (avg, min, max)
- ✅ Auto-refreshing displays
- ✅ Color-coded signal bars
- ✅ Interactive menu system

## Troubleshooting

**Server not accessible from ESP32:**
- Ensure your computer's firewall allows incoming connections on port 5000
- Verify both devices are on the same network
- Use your computer's local IP address (not localhost) in the ESP32 code

**No data showing in viewer:**
- Ensure the server is running
- Check that `rssi_log.csv` exists and contains data
- Verify ESP32 is successfully sending data (check server console output)

## License

MIT License
