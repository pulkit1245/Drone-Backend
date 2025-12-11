"""
ESP32 RSSI & GPS Data Server
============================
Receives RSSI signal strength from ESP32 helmets and GPS coordinates from Android app.
Provides combined data for drone navigation.

Author: Pulkit Verma
Date: 2025-11-27
"""

from flask import Flask, request, jsonify
from datetime import datetime
import csv
import os
from location_service import LocationService
from iot_controller import iot_bp

app = Flask(__name__)

# Register IoT controller blueprint
app.register_blueprint(iot_bp, url_prefix='/iot')

LOG_FILE = "rssi_log.csv"
location_service = LocationService()


def init_log_file():
    """Create RSSI log CSV file with headers if it doesn't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_iso", "helmet_id", "rssi", "signal_percent", "latitude", "longitude", "client_ip"])


@app.route("/rssi", methods=["POST"])
def receive_rssi():
    """
    Receive RSSI data from ESP32 helmets with GPS coordinates.
    Accepts bulk format with multiple helmets.
    
    Required format:
    {
        "latitude": float,
        "longitude": float,
        "signals": {
            "helmet_id": signal_strength,
            ...
        }
    }
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    signals = data.get("signals")

    # Validate required fields
    if latitude is None or longitude is None:
        return jsonify({"status": "error", "message": "latitude and longitude required"}), 400
    
    if signals is None or not isinstance(signals, dict) or len(signals) == 0:
        return jsonify({"status": "error", "message": "signals dictionary required with at least one helmet"}), 400

    ts = datetime.utcnow().isoformat()
    timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    client_ip = request.remote_addr

    # Process each helmet in the signals dictionary
    init_log_file()
    for helmet_id, signal in signals.items():
        # Convert signal to int if needed
        signal = int(signal)
        
        # Calculate RSSI from signal percentage
        rssi = percent_to_rssi(signal)

        print(f"[{ts}] helmet_id={helmet_id}, rssi={rssi} dBm, signal={signal}%, lat={latitude:.6f}, lon={longitude:.6f}, from={client_ip}")

        # Log to RSSI CSV with coordinates
        with open(LOG_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, helmet_id, rssi, signal, latitude, longitude, client_ip])

    # Also update coordinates log (for drone navigation)
    coords_log = "coordinates_log.csv"
    if not os.path.exists(coords_log):
        with open(coords_log, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_iso", "timestamp_ms", "latitude", "longitude", 
                "accuracy", "altitude", "speed", "client_ip"
            ])
    
    # Append coordinates to CSV (accuracy, altitude, speed will be None for helmet data)
    with open(coords_log, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts, timestamp_ms, latitude, longitude, 
            None, None, None, client_ip
        ])

    return jsonify({
        "latitude": latitude,
        "longitude": longitude,
        "signals": signals
    }), 200


def rssi_to_percent(rssi):
    """Convert RSSI (dBm) to signal percentage (0-100)."""
    RSSI_MIN, RSSI_MAX = -90, -40
    if rssi <= RSSI_MIN:
        return 0
    if rssi >= RSSI_MAX:
        return 100
    return int((rssi - RSSI_MIN) * 100 / (RSSI_MAX - RSSI_MIN))


def percent_to_rssi(percent):
    """Convert signal percentage (0-100) to RSSI (dBm)."""
    RSSI_MIN, RSSI_MAX = -90, -40
    if percent <= 0:
        return RSSI_MIN
    if percent >= 100:
        return RSSI_MAX
    return int(RSSI_MIN + (percent * (RSSI_MAX - RSSI_MIN) / 100))


@app.route("/coordinates", methods=["POST"])
def receive_coordinates():
    """
    Receive GPS coordinates from Android app.
    Required: latitude, longitude, timestamp
    Optional: accuracy, altitude, speed, azimuth, pitch, roll
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = data.get("timestamp")
    accuracy = data.get("accuracy")
    altitude = data.get("altitude")
    speed = data.get("speed")
    azimuth = data.get("azimuth")
    pitch = data.get("pitch")
    roll = data.get("roll")

    # Validate required fields
    if latitude is None or longitude is None or timestamp is None:
        return jsonify({
            "status": "error", 
            "message": "latitude, longitude, and timestamp are required"
        }), 400

    # Get client IP
    client_ip = request.remote_addr
    
    # Convert timestamp from milliseconds to ISO format
    from datetime import datetime as dt
    ts_iso = dt.utcfromtimestamp(timestamp / 1000.0).isoformat()

    # Log to console with all available data
    log_msg = f"[{ts_iso}] GPS: lat={latitude:.6f}, lon={longitude:.6f}"
    if accuracy is not None:
        log_msg += f", accuracy=±{accuracy:.1f}m"
    if altitude is not None:
        log_msg += f", altitude={altitude:.1f}m"
    if speed is not None:
        log_msg += f", speed={speed:.2f}m/s"
    if azimuth is not None:
        log_msg += f", azimuth={azimuth:.1f}°"
    log_msg += f", from={client_ip}"
    
    print(log_msg)

    # Store in a separate CSV file for coordinates
    coords_log = "coordinates_log.csv"
    
    # Create file with header if it doesn't exist
    if not os.path.exists(coords_log):
        with open(coords_log, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_iso", "timestamp_ms", "latitude", "longitude", 
                "accuracy", "altitude", "speed", "azimuth", "pitch", "roll", "client_ip"
            ])
    
    # Append coordinates to CSV
    with open(coords_log, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts_iso, timestamp, latitude, longitude, 
            accuracy, altitude, speed, azimuth, pitch, roll, client_ip
        ])

    # Return success with the received data
    return jsonify({
        "status": "ok",
        "received": {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp,
            "timestamp_iso": ts_iso,
            "accuracy": accuracy,
            "altitude": altitude,
            "speed": speed,
            "azimuth": azimuth,
            "pitch": pitch,
            "roll": roll
        }
    }), 200

@app.route("/history", methods=["GET"])
def get_history():
    """
    Get GPS and compass data history (last 10 entries).
    
    Returns:
        {
            "count": int,
            "data": [
                {
                    "latitude": float,
                    "longitude": float,
                    "timestamp": int,
                    "accuracy": float,
                    "altitude": float,
                    "speed": float,
                    "azimuth": float,
                    "pitch": float,
                    "roll": float
                },
                ...
            ]
        }
    """
    coords_log = "coordinates_log.csv"
    
    if not os.path.exists(coords_log):
        return jsonify({"count": 0, "data": []}), 200
    
    try:
        history_data = []
        with open(coords_log, mode="r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Get last 10 entries
            last_10 = rows[-10:] if len(rows) > 10 else rows
            
            for row in last_10:
                entry = {
                    "latitude": float(row["latitude"]) if row["latitude"] else None,
                    "longitude": float(row["longitude"]) if row["longitude"] else None,
                    "timestamp": int(row["timestamp_ms"]) if row["timestamp_ms"] else None,
                    "accuracy": float(row["accuracy"]) if row.get("accuracy") and row["accuracy"] != '' else None,
                    "altitude": float(row["altitude"]) if row.get("altitude") and row["altitude"] != '' else None,
                    "speed": float(row["speed"]) if row.get("speed") and row["speed"] != '' else None,
                    "azimuth": float(row["azimuth"]) if row.get("azimuth") and row["azimuth"] != '' else None,
                    "pitch": float(row["pitch"]) if row.get("pitch") and row["pitch"] != '' else None,
                    "roll": float(row["roll"]) if row.get("roll") and row["roll"] != '' else None
                }
                history_data.append(entry)
        
        return jsonify({
            "count": len(history_data),
            "data": history_data
        }), 200
        
    except Exception as e:
        print(f"Error reading history: {e}")
        return jsonify({"count": 0, "data": [], "error": str(e)}), 500

# Global variable to store the current safe waypoint
current_waypoint = {
    "latitude": None,
    "longitude": None,
    "timestamp": None,
    "set_by": None
}

@app.route("/safe-coordinates", methods=["POST"])
def receive_safe_coordinates():
    """
    Receive safe waypoint coordinates from the mobile app.
    This is the destination that ESP32 should navigate to.
    
    Required: latitude, longitude
    Optional: timestamp, set_by
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = data.get("timestamp")
    set_by = data.get("set_by", "mobile_app")

    # Validate required fields
    if latitude is None or longitude is None:
        return jsonify({
            "status": "error", 
            "message": "latitude and longitude are required"
        }), 400

    # Update global waypoint
    current_waypoint["latitude"] = latitude
    current_waypoint["longitude"] = longitude
    current_waypoint["timestamp"] = timestamp
    current_waypoint["set_by"] = set_by

    # Get client IP
    client_ip = request.remote_addr
    
    # Convert timestamp if provided
    from datetime import datetime as dt
    if timestamp:
        ts_iso = dt.utcfromtimestamp(timestamp / 1000.0).isoformat()
    else:
        ts_iso = dt.utcnow().isoformat()
        current_waypoint["timestamp"] = int(dt.utcnow().timestamp() * 1000)

    # Log to console
    print(f"[{ts_iso}] SAFE WAYPOINT SET: lat={latitude:.6f}, lon={longitude:.6f}, by={set_by}, from={client_ip}")

    # Store in CSV for history
    waypoint_log = "safe_waypoints_log.csv"
    
    # Create file with header if it doesn't exist
    if not os.path.exists(waypoint_log):
        with open(waypoint_log, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp_iso", "timestamp_ms", "latitude", "longitude", 
                "set_by", "client_ip"
            ])
    
    # Append waypoint to CSV
    with open(waypoint_log, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts_iso, current_waypoint["timestamp"], latitude, longitude, 
            set_by, client_ip
        ])

    return jsonify({
        "status": "ok",
        "message": "Safe waypoint updated",
        "waypoint": {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": current_waypoint["timestamp"],
            "timestamp_iso": ts_iso,
            "set_by": set_by
        }
    }), 200

@app.route("/waypoint", methods=["GET"])
def get_waypoint():
    """
    Get the current safe waypoint for ESP32 navigation.
    
    Returns:
        {
            "status": "ok",
            "waypoint": {
                "latitude": float,
                "longitude": float,
                "timestamp": int,
                "set_by": str
            }
        }
    """
    if current_waypoint["latitude"] is None or current_waypoint["longitude"] is None:
        return jsonify({
            "status": "no_waypoint",
            "message": "No waypoint has been set yet",
            "waypoint": None
        }), 200
    
    return jsonify({
        "status": "ok",
        "waypoint": {
            "latitude": current_waypoint["latitude"],
            "longitude": current_waypoint["longitude"],
            "timestamp": current_waypoint["timestamp"],
            "set_by": current_waypoint["set_by"]
        }
    }), 200

# Helper functions for direction calculation
def normalize_angle(angle):
    """Keep angle in [0, 360) range."""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle

def normalize_diff(diff):
    """Convert angle difference to [-180, 180] range."""
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    return diff

def haversine(lat1, lon1, lat2, lon2):
    """Compute great-circle distance in meters."""
    import math
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing_to_target(lat1, lon1, lat2, lon2):
    """Calculate bearing (0–360°) from current → target."""
    import math
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlon)
    brng = math.degrees(math.atan2(y, x))
    return normalize_angle(brng)

def decide_direction(heading, target_bearing):
    """Decide LEFT, RIGHT, FRONT, BACK based on heading difference."""
    diff = normalize_diff(target_bearing - heading)
    if abs(diff) <= 15:
        return "FRONT"
    elif diff > 15 and diff <= 90:
        return "RIGHT"
    elif diff < -15 and diff >= -90:
        return "LEFT"
    else:
        return "BACK"

@app.route("/calculate-direction", methods=["GET"])
def calculate_direction():
    """
    Calculate direction to waypoint based on current GPS position.
    Uses the latest GPS data from /history and current waypoint from /safe-coordinates.
    
    Returns direction (FRONT/BACK/LEFT/RIGHT), bearing, distance, etc.
    """
    # Get current waypoint
    if current_waypoint["latitude"] is None or current_waypoint["longitude"] is None:
        return jsonify({
            "status": "error",
            "message": "No waypoint set. Use POST /safe-coordinates first."
        }), 400
    
    # Get latest GPS position
    coords_log = "coordinates_log.csv"
    if not os.path.exists(coords_log):
        return jsonify({
            "status": "error",
            "message": "No GPS data available"
        }), 400
    
    try:
        with open(coords_log, mode="r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if len(rows) == 0:
                return jsonify({
                    "status": "error",
                    "message": "No GPS data available"
                }), 400
            
            latest = rows[-1]
            
            # Extract current position
            lat = float(latest["latitude"])
            lon = float(latest["longitude"])
            heading = float(latest["azimuth"]) if latest.get("azimuth") and latest["azimuth"] != '' else None
            
            if heading is None:
                return jsonify({
                    "status": "error",
                    "message": "No azimuth (compass heading) available"
                }), 400
            
            # Calculate bearing and distance to waypoint
            target_lat = current_waypoint["latitude"]
            target_lon = current_waypoint["longitude"]
            
            bearing = bearing_to_target(lat, lon, target_lat, target_lon)
            distance = haversine(lat, lon, target_lat, target_lon)
            direction = decide_direction(heading, bearing)
            
            return jsonify({
                "status": "ok",
                "direction": direction,
                "current_position": {
                    "latitude": lat,
                    "longitude": lon,
                    "heading": heading
                },
                "waypoint": {
                    "latitude": target_lat,
                    "longitude": target_lon
                },
                "navigation": {
                    "bearing": round(bearing, 2),
                    "distance": round(distance, 2),
                    "heading_diff": round(normalize_diff(bearing - heading), 2)
                }
            }), 200
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/location", methods=["GET"])
def get_location():
    """
    Get current MacBook GPS coordinates.
    
    Query params:
        - method: 'auto' (default), 'corelocation', 'whereami', or 'applescript'
        - cached: if 'true', return cached location if available (max 60s old)
    
    Returns:
        {
            "status": "ok",
            "location": {
                "latitude": float,
                "longitude": float,
                "accuracy": float,
                "timestamp": str
            }
        }
    """
    method = request.args.get('method', 'auto')
    use_cached = request.args.get('cached', 'false').lower() == 'true'
    
    location = None
    
    # Try cached location first if requested
    if use_cached:
        location = location_service.get_cached_location(max_age_seconds=60)
    
    # Get fresh location if no cached or not requested
    if not location:
        location = location_service.get_coordinates(method=method)
    
    if location:
        return jsonify({
            "status": "ok",
            "location": location,
            "formatted": location_service.format_coordinates(location),
            "maps_url": location_service.get_google_maps_url(location)
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Unable to get location. Ensure location services are enabled and you have the required tools installed."
        }), 500


@app.route("/get-coordinates-drone", methods=["GET"])
def get_coordinates_drone():
    """
    Get latest GPS coordinates from Android app with signal strength data for drone.
    
    Returns the most recent coordinates from Android app (POST /coordinates) 
    combined with all helmet signal strengths from ESP32 (POST /rssi).
    
    Returns:
        {
            "latitude": float,
            "longitude": float,
            "signals": {
                helmet_id: signal_strength,
                ...
            }
        }
        
        Example: 
        {
            "latitude": 28.7522064,
            "longitude": 77.4985367,
            "signals": {
                "1": 88,
                "2": 75,
                "3": 92
            }
        }
    """
    coords_log = "coordinates_log.csv"
    
    # Check if coordinates file exists
    if not os.path.exists(coords_log):
        # No coordinates received yet
        return jsonify({
            "initialized": False,
            "latitude": 0.0,
            "longitude": 0.0,
            "signals": {}
        }), 200
    
    try:
        # Read the last line from coordinates CSV (most recent GPS)
        with open(coords_log, mode="r") as f:
            lines = f.readlines()
            
            # Need at least header + 1 data line
            if len(lines) < 2:
                return jsonify({
                    "initialized": False,
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "signals": {}
                }), 200
            
            # Get last line (most recent coordinates)
            last_line = lines[-1].strip()
            parts = last_line.split(',')
            
            # Parse: timestamp_iso, timestamp_ms, latitude, longitude, accuracy, altitude, speed, client_ip
            if len(parts) >= 5:
                latitude = float(parts[2])
                longitude = float(parts[3])
            else:
                return jsonify({
                    "initialized": False,
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "signals": {}
                }), 200
        
        # Get all helmet signal strengths from RSSI log
        signals = {}
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode="r") as f:
                rssi_lines = f.readlines()
                if len(rssi_lines) >= 2:
                    # Parse all RSSI entries and keep the latest for each helmet
                    for line in rssi_lines[1:]:  # Skip header
                        rssi_parts = line.strip().split(',')
                        # Parse: timestamp_iso, helmet_id, rssi, signal_percent, latitude, longitude, client_ip
                        if len(rssi_parts) >= 4:
                            helmet_id = rssi_parts[1]  # Keep as string
                            signal = int(float(rssi_parts[3]))  # signal_percent
                            signals[helmet_id] = signal  # Later entries will overwrite earlier ones
        
        # Data is initialized if we have valid coordinates
        initialized = latitude != 0.0 or longitude != 0.0
        
        # Return new format: {initialized, latitude, longitude, signals}
        return jsonify({
            "initialized": initialized,
            "latitude": latitude,
            "longitude": longitude,
            "signals": signals
        }), 200
                
    except Exception as e:
        print(f"Error reading coordinates: {e}")
        return jsonify({
            "initialized": False,
            "latitude": 0.0,
            "longitude": 0.0,
            "signals": {}
        }), 500




@app.route("/get-signal", methods=["GET"])
def get_signal():
    """
    Get latest signal strength from RSSI data.
    
    Returns the most recent RSSI/signal data received from ESP32/helmet.
    
    Query params:
        - helmet_id: Optional, filter by specific helmet ID
    
    Returns:
        {
            "helmet_id": int,
            "rssi": int (dBm),
            "signal": int (0-100%),
            "timestamp": str,
            "client_ip": str
        }
    """
    helmet_id_filter = request.args.get('helmet_id')
    
    # Check if RSSI log file exists
    if not os.path.exists(LOG_FILE):
        return jsonify({
            "status": "error",
            "message": "No RSSI data available"
        }), 404
    
    try:
        # Read all lines from CSV
        with open(LOG_FILE, mode="r") as f:
            lines = f.readlines()
            
            # Need at least header + 1 data line
            if len(lines) < 2:
                return jsonify({
                    "status": "error",
                    "message": "No RSSI data available"
                }), 404
            
            # If filtering by helmet_id, find the last entry for that helmet
            if helmet_id_filter:
                matching_lines = []
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split(',')
                    if len(parts) >= 5 and parts[1] == helmet_id_filter:
                        matching_lines.append(line)
                
                if not matching_lines:
                    return jsonify({
                        "status": "error",
                        "message": f"No data found for helmet_id {helmet_id_filter}"
                    }), 404
                
                last_line = matching_lines[-1].strip()
            else:
                # Get last line (most recent overall)
                last_line = lines[-1].strip()
            
            parts = last_line.split(',')
            
            # Parse: timestamp_iso, helmet_id, rssi, signal_percent, client_ip
            if len(parts) >= 5:
                return jsonify({
                    "status": "ok",
                    "data": {
                        "timestamp": parts[0],
                        "helmet_id": int(parts[1]),
                        "rssi": int(parts[2]),
                        "signal": int(parts[3]),
                        "client_ip": parts[4]
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid data format"
                }), 500
                
    except Exception as e:
        print(f"Error reading RSSI data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/clear-drone-data", methods=["POST"])
def clear_drone_data():
    """
    Clear all drone-related data (coordinates and helmet signals).
    This is a convenience endpoint specifically for drone data.
    
    Optional query params:
        - confirm=yes (required for safety)
    
    Returns:
        {
            "status": "ok",
            "message": "Drone data cleared successfully",
            "cleared": {
                "coordinates": bool,
                "helmet_signals": bool
            }
        }
    """
    confirm = request.args.get('confirm', '')
    
    if confirm != 'yes':
        return jsonify({
            "status": "error",
            "message": "Please add ?confirm=yes to confirm data deletion"
        }), 400
    
    try:
        cleared = {
            "coordinates": False,
            "helmet_signals": False
        }
        
        # Clear RSSI log (helmet signals)
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            init_log_file()  # Recreate with headers
            cleared["helmet_signals"] = True
        
        # Clear coordinates log
        coords_log = "coordinates_log.csv"
        if os.path.exists(coords_log):
            os.remove(coords_log)
            # Recreate with headers
            with open(coords_log, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp_iso", "timestamp_ms", "latitude", "longitude", 
                    "accuracy", "altitude", "speed", "client_ip"
                ])
            cleared["coordinates"] = True
        
        return jsonify({
            "status": "ok",
            "message": "Drone data cleared successfully",
            "cleared": cleared
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing drone data: {str(e)}"
        }), 500


@app.route("/")
def index():
    return "ESP32 RSSI server is running.\n", 200


if __name__ == "__main__":
    init_log_file()
    # Listen on all interfaces so ESP32 in LAN can reach it
    app.run(host="0.0.0.0", port=8001, debug=True)
