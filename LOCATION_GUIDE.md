# Quick Start Guide - Location Service

## 🚀 Setup (One-time)

### 1. Install location tools
```bash
./setup_location.sh
```

### 2. Grant permissions
- Open **System Preferences**
- Go to **Security & Privacy → Privacy → Location Services**
- Enable for **Terminal**

## 📍 Usage

### From Python

```python
from location_service import LocationService

service = LocationService()

# Get current location
location = service.get_coordinates()
print(f"Lat: {location['latitude']}, Lon: {location['longitude']}")

# Get formatted string
formatted = service.format_coordinates(location)
print(formatted)  # "37.774900°N, 122.419400°W (±65.0m)"

# Get Google Maps URL
url = service.get_google_maps_url(location)
print(url)  # "https://www.google.com/maps?q=37.7749,-122.4194"

# Use cached location (faster, max 60s old)
cached = service.get_cached_location(max_age_seconds=60)
```

### From API (Server must be running)

```bash
# Get current location
curl http://localhost:5000/location

# Use cached location (faster)
curl "http://localhost:5000/location?cached=true"

# Specify method
curl "http://localhost:5000/location?method=corelocation"
```

### From Command Line

```bash
# Test the location service
python3 location_service.py

# Run the example
python3 example_location.py
```

## 🔧 Methods Available

1. **`corelocation`** - Uses CoreLocationCLI (most accurate, requires `brew install corelocationcli`)
2. **`whereami`** - Uses whereami tool (alternative, requires `brew install whereami`)
3. **`applescript`** - Uses AppleScript (fallback, no installation needed but less reliable)
4. **`auto`** - Tries all methods in order (default, recommended)

## 📊 Response Format

```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "accuracy": 65.0,
  "altitude": 52.3,
  "timestamp": "2025-11-27T11:37:23.123456"
}
```

## ⚠️ Troubleshooting

**"CoreLocationCLI not found"**
```bash
brew install corelocationcli
```

**"Location services disabled"**
- Enable in System Preferences → Security & Privacy → Privacy → Location Services
- Enable for Terminal or your Python IDE

**"Unable to get location"**
- Make sure you granted permissions
- Try running: `CoreLocationCLI -once` to test
- Check that Location Services are enabled system-wide

## 💡 Tips

- Use `cached=true` for faster responses when you don't need real-time accuracy
- The first location request may take 2-5 seconds
- Accuracy is typically 10-100 meters depending on available signals
- Indoor locations may have lower accuracy
