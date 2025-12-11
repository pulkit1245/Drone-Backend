import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_navigation_flow():
    print("--- Testing Navigation Flow ---")
    
    # 1. Set Safe Waypoint (Destination)
    # Using the coordinates from user's request: 11.495456, 77.277199
    waypoint_payload = {
        "latitude": 11.495456,
        "longitude": 77.277199,
        "set_by": "test_script"
    }
    try:
        resp = requests.post(f"{BASE_URL}/safe-coordinates", json=waypoint_payload)
        print(f"Set Waypoint: {resp.status_code} - {resp.json().get('message')}")
    except Exception as e:
        print(f"Failed to set waypoint: {e}")
        return

    # 2. Simulate GPS Update (Current Location)
    # Slightly south-west of destination to expect "FRONT" or similar
    # Origin from user request: 11.495050, 77.276972
    # Heading (azimuth) is needed. Let's say we are facing North (0)
    gps_payload = {
        "latitude": 11.495050,
        "longitude": 77.276972,
        "timestamp": int(time.time() * 1000),
        "accuracy": 5.0,
        "speed": 1.2,
        "azimuth": 25.0 # Facing somewhat towards the target (bearing is likely ~25-30 deg)
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/coordinates", json=gps_payload)
        print(f"Sent GPS: {resp.status_code}")
    except Exception as e:
        print(f"Failed to send GPS: {e}")
        return

    # 3. Get Direction
    try:
        resp = requests.get(f"{BASE_URL}/calculate-direction")
        if resp.status_code == 200:
            data = resp.json()
            print("\n✅ Direction Calculated Successfully:")
            print(f"  Direction: {data.get('direction')}")
            print(f"  Bearing: {data['navigation']['bearing']}°")
            print(f"  Distance: {data['navigation']['distance']} m")
            print(f"  Heading Diff: {data['navigation']['heading_diff']}°")
        else:
            print(f"\n❌ Failed to get direction: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Failed to get direction: {e}")

if __name__ == "__main__":
    test_navigation_flow()
