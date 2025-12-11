#!/usr/bin/env python3
"""
Test script for Safe Coordinates and Waypoint endpoints
"""

import requests
import json
import time

SERVER_URL = "http://localhost:8001"

def test_safe_coordinates():
    """Test setting a safe waypoint from the app"""
    print("\n" + "="*70)
    print("  TEST 1: Setting Safe Waypoint from App")
    print("="*70)
    
    # Set a safe waypoint
    waypoint_data = {
        "latitude": 11.495504,
        "longitude": 77.278168,
        "timestamp": int(time.time() * 1000),
        "set_by": "mobile_app_test"
    }
    
    print("\n📍 Sending safe waypoint to server:")
    print(json.dumps(waypoint_data, indent=2))
    
    response = requests.post(f"{SERVER_URL}/safe-coordinates", json=waypoint_data)
    print(f"\nStatus: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200

def test_get_waypoint():
    """Test ESP32 fetching the waypoint"""
    print("\n" + "="*70)
    print("  TEST 2: ESP32 Fetching Waypoint")
    print("="*70)
    
    response = requests.get(f"{SERVER_URL}/waypoint")
    print(f"\nStatus: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    data = response.json()
    if data["status"] == "ok":
        waypoint = data["waypoint"]
        print(f"\n✅ ESP32 will navigate to:")
        print(f"   Latitude:  {waypoint['latitude']}")
        print(f"   Longitude: {waypoint['longitude']}")
        print(f"   Set by:    {waypoint['set_by']}")
        return True
    else:
        print(f"\n⚠️  {data['message']}")
        return False

def test_calculate_direction():
    """Test direction calculation"""
    print("\n" + "="*70)
    print("  TEST 3: Calculate Direction to Waypoint")
    print("="*70)
    
    response = requests.get(f"{SERVER_URL}/calculate-direction")
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2))
        
        if data["status"] == "ok":
            print(f"\n🧭 Navigation Info:")
            print(f"   Direction:     {data['direction']}")
            print(f"   Distance:      {data['navigation']['distance']:.1f} m")
            print(f"   Bearing:       {data['navigation']['bearing']:.1f}°")
            print(f"   Current Heading: {data['current_position']['heading']:.1f}°")
            print(f"   Heading Diff:  {data['navigation']['heading_diff']:.1f}°")
            return True
        else:
            print(f"\n⚠️  {data['message']}")
            return False
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False

def test_workflow():
    """Test the complete workflow"""
    print("\n" + "="*70)
    print("  COMPLETE WORKFLOW TEST")
    print("="*70)
    
    print("\n📱 Scenario: Mobile app sets safe waypoint, ESP32 navigates to it")
    
    # Step 1: App sets waypoint
    print("\n1️⃣ Mobile app sets safe waypoint...")
    if not test_safe_coordinates():
        print("❌ Failed to set waypoint")
        return False
    
    time.sleep(1)
    
    # Step 2: ESP32 fetches waypoint
    print("\n2️⃣ ESP32 fetches waypoint...")
    if not test_get_waypoint():
        print("❌ Failed to get waypoint")
        return False
    
    time.sleep(1)
    
    # Step 3: Calculate direction
    print("\n3️⃣ Calculate direction to waypoint...")
    if not test_calculate_direction():
        print("❌ Failed to calculate direction")
        return False
    
    return True

def main():
    print("\n" + "="*70)
    print("  Safe Coordinates & Waypoint API Test")
    print("="*70)
    
    try:
        if test_workflow():
            print("\n" + "="*70)
            print("  ✅ ALL TESTS PASSED")
            print("="*70)
            
            print("\n📋 Summary:")
            print("  ✓ App can set safe waypoint via POST /safe-coordinates")
            print("  ✓ ESP32 can fetch waypoint via GET /waypoint")
            print("  ✓ Server calculates direction via GET /calculate-direction")
            
            print("\n🎯 Integration Points:")
            print("  1. Mobile App → POST /safe-coordinates (set destination)")
            print("  2. ESP32 → GET /waypoint (fetch destination)")
            print("  3. ESP32 → GET /calculate-direction (get direction)")
            print("  4. ESP32 → GET /history (get current GPS for local calc)")
            
        else:
            print("\n❌ Some tests failed")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Make sure the server is running on http://localhost:8001")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
