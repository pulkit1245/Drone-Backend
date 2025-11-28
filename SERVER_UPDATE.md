# Server Update Summary

## ✅ Changes Made

### 1. **Port Changed to 8001**
- Server now runs on port **8001** instead of 5000
- Accessible at: `http://localhost:8001` or `http://10.254.229.234:8001`

### 2. **Enhanced /rssi Endpoint**
The `/rssi` endpoint now accepts **BOTH** formats:

#### Format 1: Signal Percentage (Your Arduino Code)
```json
{
  "helmet_id": 1234,
  "signal": 82
}
```

#### Format 2: RSSI in dBm (Traditional)
```json
{
  "helmet_id": 1234,
  "rssi": -67
}
```

### 3. **Automatic Conversion**
- If you send `signal` (0-100%), server converts to `rssi` (dBm)
- If you send `rssi` (dBm), server converts to `signal` (0-100%)
- Both values are logged and returned

### 4. **Enhanced Response**
```json
{
  "status": "ok",
  "rssi": -49,
  "signal": 82
}
```

### 5. **Updated CSV Log**
New columns: `timestamp_iso, helmet_id, rssi, signal_percent, client_ip`

Example:
```csv
timestamp_iso,helmet_id,rssi,signal_percent,client_ip
2025-11-27T12:08:02.094239,3001,-51,78,127.0.0.1
```

### 6. **Updated Viewer**
The `main.py` viewer now displays both RSSI and Signal % in all views.

## 🔧 Your Arduino Code Configuration

Update your Arduino code to point to the new port:

```cpp
// Change this line:
const char* SERVER_URL = "https://gew5xr-ip-103-77-186-53.tunnelmole.net/rssi";

// To (if testing locally):
const char* SERVER_URL = "http://YOUR_MACBOOK_IP:8001/rssi";

// Or keep your tunnel URL but update the tunnel to point to port 8001
```

## 📊 Conversion Formula

**Signal % to RSSI (dBm):**
- 0% = -90 dBm (very weak)
- 50% = -65 dBm (fair)
- 100% = -40 dBm (excellent)

**RSSI (dBm) to Signal %:**
- -90 dBm = 0%
- -65 dBm = 50%
- -40 dBm = 100%

## 🧪 Testing

### Test with your Arduino format:
```bash
curl -X POST http://localhost:8001/rssi \
  -H "Content-Type: application/json" \
  -d '{"helmet_id": 1234, "signal": 82}'
```

**Response:**
```json
{
  "rssi": -49,
  "signal": 82,
  "status": "ok"
}
```

### Test with traditional RSSI format:
```bash
curl -X POST http://localhost:8001/rssi \
  -H "Content-Type: application/json" \
  -d '{"helmet_id": 1234, "rssi": -67}'
```

**Response:**
```json
{
  "rssi": -67,
  "signal": 45,
  "status": "ok"
}
```

## 📡 Server Status

✅ **Running on port 8001**
- Local: http://127.0.0.1:8001
- Network: http://10.254.229.234:8001

## 🎯 Next Steps

1. **Update your tunnelmole** to forward to port 8001:
   ```bash
   tunnelmole 8001
   ```

2. **Your Arduino code is ready!** It will work as-is, just update the SERVER_URL if needed.

3. **View incoming data:**
   ```bash
   python3 main.py
   ```
   Choose option 2 for live view to see data as it arrives.

## 📝 Console Output

When your Arduino sends data, you'll see:
```
[2025-11-27T12:08:02.094239] helmet_id=3001, rssi=-51 dBm, signal=78%, from=127.0.0.1
```

Perfect for debugging! 🎉
