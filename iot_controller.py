"""
IoT Controller for Variable Triggering and Button Monitoring
=============================================================
Manages IoT device interactions including:
- Triggering variables from mobile app
- Receiving button counts from IoT devices (e.g., 3 buttons)
- Checking trigger status via GET requests

Author: Pulkit Verma
Date: 2025-12-11
"""

from flask import Flask, request, jsonify, Blueprint
from datetime import datetime
import csv
import os
import json
from threading import Lock

# Create Blueprint for IoT routes
iot_bp = Blueprint('iot', __name__)

# File paths
IOT_TRIGGERS_FILE = "iot_triggers.csv"
IOT_BUTTON_COUNTS_FILE = "iot_button_counts.csv"
IOT_STATE_FILE = "iot_state.json"

# Thread-safe state management
state_lock = Lock()

# In-memory state for quick access
iot_state = {
    "variables": {},  # variable_name: {"triggered": bool, "timestamp": str, "triggered_by": str}
    "button_counts": {},  # device_id: {"button_1": int, "button_2": int, "button_3": int, "last_update": str}
}


def init_iot_files():
    """Initialize CSV files and load state from JSON."""
    global iot_state
    
    # Create triggers CSV if it doesn't exist
    if not os.path.exists(IOT_TRIGGERS_FILE):
        with open(IOT_TRIGGERS_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_iso", "variable_name", "action", "triggered_by", "client_ip"])
    
    # Create button counts CSV if it doesn't exist
    if not os.path.exists(IOT_BUTTON_COUNTS_FILE):
        with open(IOT_BUTTON_COUNTS_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_iso", "device_id", "button_1", "button_2", "button_3", "client_ip"])
    
    # Load or create state file
    if os.path.exists(IOT_STATE_FILE):
        try:
            with open(IOT_STATE_FILE, 'r') as f:
                iot_state = json.load(f)
        except Exception as e:
            print(f"Error loading IoT state: {e}")
            save_state()
    else:
        save_state()


def save_state():
    """Save current state to JSON file."""
    try:
        with open(IOT_STATE_FILE, 'w') as f:
            json.dump(iot_state, f, indent=2)
    except Exception as e:
        print(f"Error saving IoT state: {e}")


@iot_bp.route("/trigger", methods=["POST", "GET"])
def trigger_variable():
    """
    POST: Trigger a variable from the mobile app.
    GET: Check if a variable is triggered.
    
    POST Request body:
    {
        "variable_name": "emergency_alert",
        "triggered": true,
        "triggered_by": "app_user_123"
    }
    
    GET Query params:
    ?variable_name=emergency_alert
    
    Returns:
    {
        "status": "ok",
        "variable_name": "emergency_alert",
        "triggered": true,
        "timestamp": "2025-12-11T17:00:00"
    }
    """
    # Handle GET request - check trigger status
    if request.method == "GET":
        variable_name = request.args.get('variable_name')
        
        if not variable_name:
            return jsonify({"status": "error", "message": "variable_name is required"}), 400
        
        with state_lock:
            if variable_name in iot_state["variables"]:
                var_data = iot_state["variables"][variable_name]
                return jsonify({
                    "status": "ok",
                    "variable_name": variable_name,
                    "triggered": var_data["triggered"],
                    "timestamp": var_data["timestamp"],
                    "triggered_by": var_data["triggered_by"]
                }), 200
            else:
                return jsonify({
                    "status": "ok",
                    "variable_name": variable_name,
                    "triggered": False,
                    "timestamp": None,
                    "triggered_by": None
                }), 200
    
    # Handle POST request - set trigger
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    variable_name = data.get("variable_name")
    triggered = data.get("triggered", True)
    triggered_by = data.get("triggered_by", "unknown")
    
    if not variable_name:
        return jsonify({"status": "error", "message": "variable_name is required"}), 400
    
    ts = datetime.utcnow().isoformat()
    client_ip = request.remote_addr
    
    with state_lock:
        # Update in-memory state
        iot_state["variables"][variable_name] = {
            "triggered": triggered,
            "timestamp": ts,
            "triggered_by": triggered_by
        }
        
        # Save state to file
        save_state()
        
        # Log to CSV
        with open(IOT_TRIGGERS_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            action = "trigger" if triggered else "reset"
            writer.writerow([ts, variable_name, action, triggered_by, client_ip])
    
    print(f"[{ts}] Variable '{variable_name}' {action}ed by {triggered_by} from {client_ip}")
    
    return jsonify({
        "status": "ok",
        "variable_name": variable_name,
        "triggered": triggered,
        "timestamp": ts
    }), 200


@iot_bp.route("/button-count", methods=["POST"])
def receive_button_count():
    """
    Receive button count from IoT device (e.g., ESP32 with 3 buttons).
    
    Request body:
    {
        "device_id": "esp32_001",
        "button_1": 5,
        "button_2": 3,
        "button_3": 7
    }
    
    Returns:
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
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    device_id = data.get("device_id")
    button_1 = data.get("button_1", 0)
    button_2 = data.get("button_2", 0)
    button_3 = data.get("button_3", 0)
    
    if not device_id:
        return jsonify({"status": "error", "message": "device_id is required"}), 400
    
    ts = datetime.utcnow().isoformat()
    client_ip = request.remote_addr
    
    with state_lock:
        # Update in-memory state
        iot_state["button_counts"][device_id] = {
            "button_1": button_1,
            "button_2": button_2,
            "button_3": button_3,
            "last_update": ts
        }
        
        # Save state to file
        save_state()
        
        # Log to CSV
        with open(IOT_BUTTON_COUNTS_FILE, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, device_id, button_1, button_2, button_3, client_ip])
    
    print(f"[{ts}] Button counts from {device_id}: B1={button_1}, B2={button_2}, B3={button_3}, from {client_ip}")
    
    return jsonify({
        "status": "ok",
        "device_id": device_id,
        "counts": {
            "button_1": button_1,
            "button_2": button_2,
            "button_3": button_3
        },
        "timestamp": ts
    }), 200


@iot_bp.route("/status", methods=["GET"])
def get_trigger_status():
    """
    Get the current trigger status of variables.
    
    Query params:
        - variable_name: Optional, get status of specific variable
        - device_id: Optional, get button counts for specific device
    
    Returns (all variables):
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
    
    Returns (specific variable):
    {
        "status": "ok",
        "variable_name": "emergency_alert",
        "triggered": true,
        "timestamp": "2025-12-11T17:00:00",
        "triggered_by": "app_user_123"
    }
    """
    variable_name = request.args.get('variable_name')
    device_id = request.args.get('device_id')
    
    with state_lock:
        # Specific variable requested
        if variable_name:
            if variable_name in iot_state["variables"]:
                var_data = iot_state["variables"][variable_name]
                return jsonify({
                    "status": "ok",
                    "variable_name": variable_name,
                    "triggered": var_data["triggered"],
                    "timestamp": var_data["timestamp"],
                    "triggered_by": var_data["triggered_by"]
                }), 200
            else:
                return jsonify({
                    "status": "ok",
                    "variable_name": variable_name,
                    "triggered": False,
                    "timestamp": None,
                    "triggered_by": None
                }), 200
        
        # Specific device requested
        if device_id:
            if device_id in iot_state["button_counts"]:
                device_data = iot_state["button_counts"][device_id]
                return jsonify({
                    "status": "ok",
                    "device_id": device_id,
                    "counts": {
                        "button_1": device_data["button_1"],
                        "button_2": device_data["button_2"],
                        "button_3": device_data["button_3"]
                    },
                    "last_update": device_data["last_update"]
                }), 200
            else:
                return jsonify({
                    "status": "ok",
                    "device_id": device_id,
                    "counts": {
                        "button_1": 0,
                        "button_2": 0,
                        "button_3": 0
                    },
                    "last_update": None
                }), 200
        
        # Return all data
        return jsonify({
            "status": "ok",
            "variables": iot_state["variables"],
            "button_counts": iot_state["button_counts"]
        }), 200


@iot_bp.route("/reset", methods=["POST"])
def reset_iot_data():
    """
    Reset all IoT data (variables and button counts).
    
    Optional query params:
        - confirm=yes (required for safety)
        - type=variables|buttons|all (default: all)
    
    Returns:
    {
        "status": "ok",
        "message": "IoT data reset successfully",
        "reset": {
            "variables": bool,
            "button_counts": bool
        }
    }
    """
    confirm = request.args.get('confirm', '')
    reset_type = request.args.get('type', 'all')
    
    if confirm != 'yes':
        return jsonify({
            "status": "error",
            "message": "Please add ?confirm=yes to confirm data reset"
        }), 400
    
    reset_result = {
        "variables": False,
        "button_counts": False
    }
    
    with state_lock:
        if reset_type in ['variables', 'all']:
            iot_state["variables"] = {}
            reset_result["variables"] = True
        
        if reset_type in ['buttons', 'all']:
            iot_state["button_counts"] = {}
            reset_result["button_counts"] = True
        
        save_state()
    
    return jsonify({
        "status": "ok",
        "message": f"IoT data reset successfully (type: {reset_type})",
        "reset": reset_result
    }), 200


@iot_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for IoT controller."""
    with state_lock:
        return jsonify({
            "status": "ok",
            "service": "IoT Controller",
            "variables_count": len(iot_state["variables"]),
            "devices_count": len(iot_state["button_counts"]),
            "timestamp": datetime.utcnow().isoformat()
        }), 200


# Initialize files when module is loaded
init_iot_files()
