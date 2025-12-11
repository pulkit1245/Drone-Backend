#!/usr/bin/env python3
"""
ESP32 Hybrid Navigation Simulator
==================================
Simulates the ESP32 hybrid navigation system to test server integration.
"""

import requests
import json
import time

SERVER_URL = "http://localhost:8001"

def test_trigger_endpoint():
    """Test the /iot/trigger GET endpoint that ESP32 will use."""
    print("\n" + "="*60)
    print("  Testing GET /iot/trigger Endpoint")
    print("="*60)
    
    # Test 1: Check trigger status (should be false initially)
    print("\n1. Checking initial trigger status...")
    response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    print(f"   Triggered: {data.get('triggered')}")
    
    return response.status_code == 200

def test_remote_trigger():
    """Simulate remote trigger from mobile app."""
    print("\n" + "="*60)
    print("  Simulating Remote Trigger from App")
    print("="*60)
    
    # Trigger navigation
    print("\n1. Sending POST to trigger navigation...")
    payload = {
        "variable_name": "start_navigation",
        "triggered": True,
        "triggered_by": "mobile_app_simulator"
    }
    response = requests.post(f"{SERVER_URL}/iot/trigger", json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Wait a bit
    time.sleep(1)
    
    # ESP32 checks status
    print("\n2. ESP32 checks trigger status (GET request)...")
    response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
    data = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Triggered: {data.get('triggered')}")
    
    if data.get('triggered'):
        print("\n   ✅ ESP32 would START NAVIGATION now!")
    else:
        print("\n   ❌ Trigger not detected!")
    
    return data.get('triggered')

def test_gps_endpoint():
    """Test if /history endpoint is available."""
    print("\n" + "="*60)
    print("  Testing GPS /history Endpoint")
    print("="*60)
    
    print("\n1. Fetching GPS data from /history...")
    try:
        response = requests.get(f"{SERVER_URL}/history", timeout=3)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"   GPS records available: {count}")
            
            if count > 0:
                latest = data['data'][-1]
                print(f"   Latest GPS:")
                print(f"     Lat: {latest.get('latitude')}")
                print(f"     Lon: {latest.get('longitude')}")
                print(f"     Azimuth: {latest.get('azimuth')}")
                return True
            else:
                print("   ⚠️  No GPS data available yet")
                print("   (Phone needs to send GPS data to /coordinates)")
                return False
        else:
            print(f"   ❌ Error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_stop_navigation():
    """Simulate stopping navigation."""
    print("\n" + "="*60)
    print("  Simulating Stop Navigation")
    print("="*60)
    
    # Reset trigger
    print("\n1. Sending POST to stop navigation...")
    payload = {
        "variable_name": "start_navigation",
        "triggered": False,
        "triggered_by": "mobile_app_simulator"
    }
    response = requests.post(f"{SERVER_URL}/iot/trigger", json=payload)
    print(f"   Status: {response.status_code}")
    
    # Wait a bit
    time.sleep(1)
    
    # ESP32 checks status
    print("\n2. ESP32 checks trigger status...")
    response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
    data = response.json()
    print(f"   Triggered: {data.get('triggered')}")
    
    if not data.get('triggered'):
        print("\n   ✅ ESP32 would STOP NAVIGATION now!")
    else:
        print("\n   ❌ Trigger still active!")
    
    return not data.get('triggered')

def simulate_esp32_loop():
    """Simulate the ESP32 main loop behavior."""
    print("\n" + "="*60)
    print("  Simulating ESP32 Main Loop (5 iterations)")
    print("="*60)
    
    for i in range(5):
        print(f"\n--- Loop iteration {i+1} ---")
        
        # Check remote trigger (every 1 second in real ESP32)
        response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
        data = response.json()
        triggered = data.get('triggered', False)
        
        print(f"Trigger check: {'ACTIVE' if triggered else 'INACTIVE'}")
        
        if triggered:
            # Fetch GPS data
            try:
                gps_response = requests.get(f"{SERVER_URL}/history", timeout=2)
                if gps_response.status_code == 200:
                    gps_data = gps_response.json()
                    if gps_data.get('count', 0) > 0:
                        latest = gps_data['data'][-1]
                        print(f"GPS: Lat={latest.get('latitude'):.6f}, Lon={latest.get('longitude'):.6f}, Azimuth={latest.get('azimuth'):.1f}°")
                        print("→ Calculating direction and updating LEDs...")
                    else:
                        print("⚠️  No GPS data available")
                else:
                    print(f"⚠️  GPS fetch failed: {gps_response.status_code}")
            except:
                print("⚠️  GPS endpoint error")
        else:
            print("LEDs: All OFF (navigation inactive)")
        
        time.sleep(1)

def main():
    print("\n" + "="*60)
    print("  ESP32 Hybrid Navigation System - Integration Test")
    print("="*60)
    
    try:
        # Test 1: Trigger endpoint
        print("\n📡 Test 1: Trigger Endpoint")
        if not test_trigger_endpoint():
            print("❌ Trigger endpoint test failed!")
            return
        
        time.sleep(1)
        
        # Test 2: GPS endpoint
        print("\n📍 Test 2: GPS Endpoint")
        gps_available = test_gps_endpoint()
        if not gps_available:
            print("⚠️  GPS data not available (this is OK if phone isn't sending data)")
        
        time.sleep(1)
        
        # Test 3: Remote trigger
        print("\n🚀 Test 3: Remote Trigger")
        if not test_remote_trigger():
            print("❌ Remote trigger test failed!")
            return
        
        time.sleep(2)
        
        # Test 4: Simulate ESP32 loop
        print("\n🔄 Test 4: ESP32 Loop Simulation")
        simulate_esp32_loop()
        
        time.sleep(1)
        
        # Test 5: Stop navigation
        print("\n🛑 Test 5: Stop Navigation")
        if not test_stop_navigation():
            print("❌ Stop navigation test failed!")
            return
        
        print("\n" + "="*60)
        print("  ✅ All Integration Tests Passed!")
        print("="*60)
        print("\n📋 Summary:")
        print("  ✓ GET /iot/trigger endpoint works")
        print("  ✓ POST /iot/trigger endpoint works")
        print("  ✓ Remote trigger detection works")
        print("  ✓ Stop navigation works")
        if gps_available:
            print("  ✓ GPS data available")
        else:
            print("  ⚠️  GPS data not available (phone needs to send data)")
        
        print("\n🎯 Next Steps:")
        print("  1. Upload esp32_hybrid_navigation_fixed.ino to ESP32")
        print("  2. Start sending GPS data from phone to /coordinates")
        print("  3. Press button 3 times OR trigger from app")
        print("  4. ESP32 will show navigation direction on LEDs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Make sure the server is running on http://localhost:8001")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")

if __name__ == "__main__":
    main()
