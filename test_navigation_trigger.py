#!/usr/bin/env python3
"""
Test IoT Trigger Integration
=============================
Tests the new GET /iot/trigger endpoint and navigation system integration.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001/iot"

def test_trigger_get_endpoint():
    """Test GET /iot/trigger endpoint."""
    print("\n" + "="*60)
    print("  Testing GET /iot/trigger Endpoint")
    print("="*60 + "\n")
    
    # Test 1: Check non-existent variable
    print("Test 1: Check non-existent variable")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 2: Trigger the variable via POST
    print("\nTest 2: Trigger variable via POST")
    payload = {
        "variable_name": "start_navigation",
        "triggered": True,
        "triggered_by": "test_script"
    }
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Check triggered variable via GET
    print("\nTest 3: Check triggered variable via GET")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get("triggered"):
        print("\n✓ Variable is TRIGGERED! ESP32 navigation should start.")
    else:
        print("\n✗ Variable is NOT triggered")
    
    # Test 4: Reset the variable
    print("\nTest 4: Reset variable via POST")
    payload = {
        "variable_name": "start_navigation",
        "triggered": False,
        "triggered_by": "test_script"
    }
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 5: Verify reset via GET
    print("\nTest 5: Verify reset via GET")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if not data.get("triggered"):
        print("\n✓ Variable successfully reset!")
    else:
        print("\n✗ Variable still triggered")

def test_button_count_trigger():
    """Test button count auto-trigger scenario."""
    print("\n" + "="*60)
    print("  Testing Button Count Auto-Trigger")
    print("="*60 + "\n")
    
    # Simulate button presses
    print("Simulating 3 button presses...")
    
    for i in range(1, 4):
        payload = {
            "device_id": "esp32_nav_001",
            "button_1": i,
            "button_2": 0,
            "button_3": 0
        }
        response = requests.post(f"{BASE_URL}/button-count", json=payload)
        print(f"Button press {i}: {response.status_code}")
        time.sleep(0.5)
    
    # Check if navigation was triggered
    print("\nChecking trigger status...")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    data = response.json()
    
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get("triggered"):
        print("\n✓ Navigation auto-triggered after 3 button presses!")
    else:
        print("\n⚠️  Auto-trigger not activated (ESP32 would handle this)")

def test_navigation_workflow():
    """Test complete navigation workflow."""
    print("\n" + "="*60)
    print("  Testing Complete Navigation Workflow")
    print("="*60 + "\n")
    
    # Step 1: Reset system
    print("Step 1: Reset navigation system")
    payload = {
        "variable_name": "start_navigation",
        "triggered": False,
        "triggered_by": "test_workflow"
    }
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"✓ System reset: {response.status_code}")
    
    time.sleep(1)
    
    # Step 2: Check status (should be false)
    print("\nStep 2: Check initial status")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    data = response.json()
    print(f"Triggered: {data.get('triggered')}")
    
    time.sleep(1)
    
    # Step 3: Trigger from app
    print("\nStep 3: Trigger from mobile app")
    payload = {
        "variable_name": "start_navigation",
        "triggered": True,
        "triggered_by": "mobile_app"
    }
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"✓ Triggered: {response.status_code}")
    
    time.sleep(1)
    
    # Step 4: ESP32 checks status (should be true)
    print("\nStep 4: ESP32 checks status (simulated)")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get("triggered"):
        print("\n🚀 ESP32 would start navigation now!")
        print("   - Fetching GPS data from /history")
        print("   - Calculating bearing to destination")
        print("   - Showing direction on LEDs")
    
    time.sleep(1)
    
    # Step 5: Stop navigation
    print("\nStep 5: Stop navigation from app")
    payload = {
        "variable_name": "start_navigation",
        "triggered": False,
        "triggered_by": "mobile_app"
    }
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"✓ Stopped: {response.status_code}")
    
    time.sleep(1)
    
    # Step 6: ESP32 checks status (should be false)
    print("\nStep 6: ESP32 checks status again")
    response = requests.get(f"{BASE_URL}/trigger?variable_name=start_navigation")
    data = response.json()
    print(f"Triggered: {data.get('triggered')}")
    
    if not data.get("triggered"):
        print("\n🛑 ESP32 would stop navigation now!")
        print("   - LEDs turned off")
        print("   - Waiting for next trigger")

if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("  IoT Trigger Integration Test Suite")
        print("="*60)
        
        test_trigger_get_endpoint()
        time.sleep(2)
        
        test_button_count_trigger()
        time.sleep(2)
        
        test_navigation_workflow()
        
        print("\n" + "="*60)
        print("  All Tests Complete!")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Make sure the server is running on http://localhost:8001")
        print("\nStart the server with: python3 server.py")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
