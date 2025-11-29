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

app = Flask(__name__)

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
    Required: helmet_id, latitude, longitude
    Optional: rssi (dBm) or signal (0-100%)
    Automatically converts between dBm and percentage.
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    helmet_id = data.get("helmet_id")
    rssi = data.get("rssi")
    signal = data.get("signal")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    # Validate required fields
    if helmet_id is None:
        return jsonify({"status": "error", "message": "helmet_id required"}), 400
    
    if latitude is None or longitude is None:
        return jsonify({"status": "error", "message": "latitude and longitude required"}), 400
    
    if rssi is None and signal is None:
        return jsonify({"status": "error", "message": "Either rssi or signal required"}), 400

    # Convert between formats if needed
    if rssi is not None and signal is None:
        signal = rssi_to_percent(rssi)
    elif signal is not None and rssi is None:
        rssi = percent_to_rssi(signal)

    ts = datetime.utcnow().isoformat()
    timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    client_ip = request.remote_addr

    print(f"[{ts}] helmet_id={helmet_id}, rssi={rssi} dBm, signal={signal}%, lat={latitude:.6f}, lon={longitude:.6f}, from={client_ip}")

    # Log to RSSI CSV with coordinates
    init_log_file()
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
        "status": "ok", 
        "rssi": rssi, 
        "signal": signal,
        "latitude": latitude,
        "longitude": longitude
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
    Optional: accuracy, altitude, speed
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
                "accuracy", "altitude", "speed", "client_ip"
            ])
    
    # Append coordinates to CSV
    with open(coords_log, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            ts_iso, timestamp, latitude, longitude, 
            accuracy, altitude, speed, client_ip
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
            "speed": speed
        }
    }), 200

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
    Get latest GPS coordinates from Android app with signal strength as a simple array for drone.
    
    Returns the most recent coordinates from Android app (POST /coordinates) 
    combined with the latest signal strength from ESP32 (POST /rssi).
    
    Returns:
        Array of 4 doubles: [latitude, longitude, 1, signal]
        Example: [28.7522064, 77.4985367, 1.0, 88.0]
        
        - [0] = latitude (degrees)
        - [1] = longitude (degrees)
        - [2] = reserved (always 1.0)
        - [3] = signal strength (0-100%)
    """
    coords_log = "coordinates_log.csv"
    
    # Check if coordinates file exists
    if not os.path.exists(coords_log):
        # No coordinates received yet
        return jsonify([0.0, 0.0, 0.0, 0.0]), 200
    
    try:
        # Read the last line from coordinates CSV (most recent GPS)
        with open(coords_log, mode="r") as f:
            lines = f.readlines()
            
            # Need at least header + 1 data line
            if len(lines) < 2:
                return jsonify([0.0, 0.0, 0.0, 0.0]), 200
            
            # Get last line (most recent coordinates)
            last_line = lines[-1].strip()
            parts = last_line.split(',')
            
            # Parse: timestamp_iso, timestamp_ms, latitude, longitude, accuracy, altitude, speed, client_ip
            if len(parts) >= 5:
                latitude = float(parts[2])
                longitude = float(parts[3])
            else:
                return jsonify([0.0, 0.0, 0.0, 0.0]), 200
        
        # Get latest signal strength from RSSI log
        signal = 0.0
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode="r") as f:
                rssi_lines = f.readlines()
                if len(rssi_lines) >= 2:
                    # Get last RSSI line
                    last_rssi = rssi_lines[-1].strip()
                    rssi_parts = last_rssi.split(',')
                    # Parse: timestamp_iso, helmet_id, rssi, signal_percent, client_ip
                    if len(rssi_parts) >= 4:
                        signal = float(rssi_parts[3])  # signal_percent
        
        # Return array: [latitude, longitude, 1, signal]
        coordinates = [latitude, longitude, 1.0, signal]
        return jsonify(coordinates), 200
                
    except Exception as e:
        print(f"Error reading coordinates: {e}")
        return jsonify([0.0, 0.0, 0.0, 0.0]), 500




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


@app.route("/")
def index():
    return "ESP32 RSSI server is running.\n", 200


if __name__ == "__main__":
    init_log_file()
    # Listen on all interfaces so ESP32 in LAN can reach it
    app.run(host="0.0.0.0", port=8001, debug=True)
