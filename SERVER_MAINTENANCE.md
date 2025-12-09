# Server Maintenance Guide

## Finding Where "Helmet 1" Data Comes From

### Step 1: Check Data Status on Server

First, check what data exists on your deployed server:

```bash
curl https://your-server-url.com/data-status
```

This will show you:
- All helmet IDs currently in the system
- How many entries each helmet has
- Latest timestamp and signal for each helmet
- Total entries in coordinates log

**Example Response:**
```json
{
  "rssi_log": {
    "exists": true,
    "helmets": {
      "1": {
        "count": 150,
        "latest_timestamp": "2025-11-28T15:30:50.059640",
        "latest_signal": 20
      },
      "1967": {
        "count": 1059,
        "latest_timestamp": "2025-11-28T15:09:16.756515",
        "latest_signal": 100
      }
    },
    "total_entries": 2372
  },
  "coordinates_log": {
    "exists": true,
    "total_entries": 5000,
    "latest": {
      "timestamp": "2025-11-28T15:35:22.082000",
      "latitude": 28.753045,
      "longitude": 77.498278
    }
  }
}
```

### Step 2: Clear Old Data (if needed)

If you see old/unwanted helmet data (like "helmet 1"), clear it:

```bash
curl -X POST "https://your-server-url.com/clear-data?confirm=yes"
```

**Response:**
```json
{
  "status": "ok",
  "message": "Data cleared successfully",
  "files_cleared": ["rssi_log.csv", "coordinates_log.csv"]
}
```

> ⚠️ **Warning**: This will delete ALL logged data. Make sure you want to do this!

### Step 3: Verify Data is Cleared

Check status again to confirm:

```bash
curl https://your-server-url.com/data-status
```

Should show empty helmets:
```json
{
  "rssi_log": {
    "exists": true,
    "helmets": {},
    "total_entries": 0
  },
  "coordinates_log": {
    "exists": true,
    "total_entries": 0
  }
}
```

## Understanding the Data Flow

### Where Helmet Data Comes From

1. **ESP32/Helmet Device** sends POST to `/rssi`:
   ```json
   {
     "latitude": 28.753045,
     "longitude": 77.498278,
     "signals": {
       "1": 85,
       "2": 92
     }
   }
   ```

2. **Server** logs to `rssi_log.csv`:
   ```
   timestamp_iso,helmet_id,rssi,signal_percent,latitude,longitude,client_ip
   2025-11-30T19:25:35,1,-67,85,28.753045,77.498278,127.0.0.1
   ```

3. **Android App** calls GET `/get-coordinates-drone`:
   - Reads ALL entries from `rssi_log.csv`
   - Returns latest signal for each helmet_id
   - **This is where old data persists!**

### Why "Helmet 1" Keeps Appearing

- CSV files persist between server restarts
- `/get-coordinates-drone` reads the ENTIRE CSV file
- Even old data from days/weeks ago will appear
- Solution: Clear data or filter by timestamp

## Deployment Checklist

When deploying to Render/server:

1. ✅ Push updated `server.py` with new endpoints
2. ✅ Deploy to server
3. ✅ Call `/data-status` to check what data exists
4. ✅ Call `/clear-data?confirm=yes` if needed to reset
5. ✅ Test with fresh data from ESP32/helmet

## Troubleshooting

### Problem: Helmet 1 still appears after clearing data

**Possible causes:**
1. Multiple server instances running
2. Android app caching old responses
3. Different server URL being used
4. Simulation mode in Android app

**Solutions:**
- Check Android app's server URL configuration
- Clear Android app cache/data
- Verify only one server instance is running
- Check if app has simulation/test mode enabled

### Problem: Data clears but immediately comes back

**Cause:** ESP32/helmet is continuously sending data with helmet_id=1

**Solution:** 
- Check ESP32 code - what helmet_id is it sending?
- Update ESP32 firmware to use correct helmet_id
- Or accept that helmet 1 is a real device

## API Reference

### GET `/data-status`
Returns current state of logged data.

### POST `/clear-data?confirm=yes`
Clears all logged data (requires confirmation).

### GET `/get-coordinates-drone`
Returns latest drone navigation data (reads from CSV files).

### POST `/rssi`
Receives helmet signal data (writes to CSV files).

### POST `/coordinates`
Receives GPS coordinates from Android app (writes to CSV files).
