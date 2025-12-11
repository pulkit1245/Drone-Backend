#!/usr/bin/env python3
"""
IoT Controller Test Script
===========================
Tests all IoT endpoints to verify functionality.

Usage: python test_iot.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001/iot"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test the health check endpoint."""
    print_section("Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_trigger_variable():
    """Test triggering a variable."""
    print_section("Testing Variable Trigger")
    
    # Trigger emergency alert
    payload = {
        "variable_name": "emergency_alert",
        "triggered": True,
        "triggered_by": "test_script"
    }
    
    print(f"Sending: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_button_count():
    """Test sending button counts."""
    print_section("Testing Button Count")
    
    payload = {
        "device_id": "esp32_test_001",
        "button_1": 10,
        "button_2": 5,
        "button_3": 15
    }
    
    print(f"Sending: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{BASE_URL}/button-count", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_get_all_status():
    """Test getting all status."""
    print_section("Testing Get All Status")
    
    response = requests.get(f"{BASE_URL}/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_get_variable_status():
    """Test getting specific variable status."""
    print_section("Testing Get Variable Status")
    
    response = requests.get(f"{BASE_URL}/status?variable_name=emergency_alert")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    data = response.json()
    if data.get("triggered"):
        print("\n✓ Variable is TRIGGERED!")
    else:
        print("\n✗ Variable is NOT triggered")
    
    return response.status_code == 200

def test_get_device_status():
    """Test getting specific device button counts."""
    print_section("Testing Get Device Status")
    
    response = requests.get(f"{BASE_URL}/status?device_id=esp32_test_001")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_reset_trigger():
    """Test resetting a trigger."""
    print_section("Testing Reset Trigger")
    
    payload = {
        "variable_name": "emergency_alert",
        "triggered": False,
        "triggered_by": "test_script"
    }
    
    print(f"Sending: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{BASE_URL}/trigger", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify it's reset
    time.sleep(0.5)
    response = requests.get(f"{BASE_URL}/status?variable_name=emergency_alert")
    data = response.json()
    
    if not data.get("triggered"):
        print("\n✓ Variable successfully reset!")
    else:
        print("\n✗ Variable still triggered")
    
    return response.status_code == 200

def test_multiple_devices():
    """Test multiple devices sending data."""
    print_section("Testing Multiple Devices")
    
    devices = [
        {"device_id": "esp32_001", "button_1": 5, "button_2": 3, "button_3": 7},
        {"device_id": "esp32_002", "button_1": 2, "button_2": 8, "button_3": 4},
        {"device_id": "esp32_003", "button_1": 9, "button_2": 1, "button_3": 6}
    ]
    
    for device in devices:
        print(f"\nSending from {device['device_id']}...")
        response = requests.post(f"{BASE_URL}/button-count", json=device)
        if response.status_code == 200:
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Failed: {response.status_code}")
        time.sleep(0.2)
    
    # Get all status
    print("\nFetching all device status...")
    response = requests.get(f"{BASE_URL}/status")
    data = response.json()
    
    print(f"\nTotal devices: {len(data.get('button_counts', {}))}")
    for device_id, counts in data.get('button_counts', {}).items():
        print(f"  {device_id}: B1={counts['button_1']}, B2={counts['button_2']}, B3={counts['button_3']}")
    
    return True

def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("  IoT Controller Test Suite")
    print("="*60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Trigger Variable", test_trigger_variable),
        ("Button Count", test_button_count),
        ("Get All Status", test_get_all_status),
        ("Get Variable Status", test_get_variable_status),
        ("Get Device Status", test_get_device_status),
        ("Reset Trigger", test_reset_trigger),
        ("Multiple Devices", test_multiple_devices)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"\n✗ Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Make sure the server is running on http://localhost:8001")
        print("\nStart the server with: python server.py")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
