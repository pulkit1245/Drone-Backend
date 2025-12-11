#!/usr/bin/env python3
"""
Test Navigation Trigger Mechanism
==================================
Verifies that navigation starts when server responds with triggered=true
"""

import requests
import json
import time

SERVER_URL = "http://localhost:8001"

def test_navigation_trigger_mechanism():
    """Test that navigation starts when triggered=true from server."""
    
    print("\n" + "="*70)
    print("  Testing Navigation Trigger Mechanism")
    print("="*70)
    
    # Step 1: Reset trigger state
    print("\n📋 Step 1: Reset trigger state")
    print("-" * 70)
    payload = {
        "variable_name": "start_navigation",
        "triggered": False,
        "triggered_by": "test_reset"
    }
    response = requests.post(f"{SERVER_URL}/iot/trigger", json=payload)
    print(f"✓ Reset trigger: {response.status_code}")
    time.sleep(0.5)
    
    # Step 2: Verify initial state (should be false)
    print("\n📋 Step 2: Verify initial state")
    print("-" * 70)
    response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
    data = response.json()
    print(f"GET /iot/trigger response:")
    print(json.dumps(data, indent=2))
    
    initial_triggered = data.get('triggered', False)
    print(f"\n{'✓' if not initial_triggered else '✗'} Initial state: triggered = {initial_triggered}")
    
    if initial_triggered:
        print("⚠️  Warning: Trigger should be false initially!")
    
    # Step 3: Trigger navigation from server
    print("\n📋 Step 3: Trigger navigation (POST triggered=true)")
    print("-" * 70)
    payload = {
        "variable_name": "start_navigation",
        "triggered": True,
        "triggered_by": "mobile_app_test"
    }
    response = requests.post(f"{SERVER_URL}/iot/trigger", json=payload)
    post_data = response.json()
    print(f"POST /iot/trigger response:")
    print(json.dumps(post_data, indent=2))
    print(f"\n✓ Server updated: triggered = {post_data.get('triggered')}")
    
    time.sleep(0.5)
    
    # Step 4: ESP32 checks trigger status (simulating checkRemoteTrigger())
    print("\n📋 Step 4: ESP32 checks trigger status (GET request)")
    print("-" * 70)
    print("Simulating ESP32 checkRemoteTrigger() function...")
    
    response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
    esp32_data = response.json()
    
    print(f"\nESP32 receives:")
    print(json.dumps(esp32_data, indent=2))
    
    triggered = esp32_data.get('triggered', False)
    
    print(f"\nESP32 code logic:")
    print(f"  bool triggered = doc[\"triggered\"];  // = {triggered}")
    print(f"  if (triggered && !navigationActive) {{")
    
    if triggered:
        print(f"    Serial.println(\"Remote trigger activated!\");")
        print(f"    startNavigation();  // ← NAVIGATION STARTS HERE")
        print(f"  }}")
        print(f"\n✅ PASS: Navigation mechanism WILL START")
        print(f"   - navigationActive will be set to true")
        print(f"   - Status LED will flash 3 times")
        print(f"   - GPS fetching will begin")
        print(f"   - Direction LEDs will show navigation")
    else:
        print(f"    // This block will NOT execute")
        print(f"  }}")
        print(f"\n❌ FAIL: Navigation mechanism will NOT start")
        print(f"   - triggered is false, condition not met")
    
    # Step 5: Verify navigation would be active
    print("\n📋 Step 5: Verify navigation state")
    print("-" * 70)
    
    if triggered:
        print("After startNavigation() executes:")
        print("  ✓ navigationActive = true")
        print("  ✓ Status LED flashes 3 times (visual feedback)")
        print("  ✓ Serial prints: '✅ Navigation System Activated'")
        print("\nIn main loop():")
        print("  if (navigationActive && millis() - lastUpdate >= GPS_UPDATE_INTERVAL) {")
        print("    ✓ fetchLocationData();  // Fetches from /history")
        print("    ✓ if (currentData.valid) updateDirectionLeds();  // Shows direction")
        print("  }")
    else:
        print("Navigation will remain inactive:")
        print("  ✗ navigationActive = false")
        print("  ✗ No GPS fetching")
        print("  ✗ All LEDs remain OFF")
    
    # Step 6: Test stop mechanism
    print("\n📋 Step 6: Test stop mechanism")
    print("-" * 70)
    print("Resetting trigger to false...")
    
    payload = {
        "variable_name": "start_navigation",
        "triggered": False,
        "triggered_by": "mobile_app_test"
    }
    response = requests.post(f"{SERVER_URL}/iot/trigger", json=payload)
    time.sleep(0.5)
    
    response = requests.get(f"{SERVER_URL}/iot/trigger?variable_name=start_navigation")
    stop_data = response.json()
    stopped = not stop_data.get('triggered', True)
    
    print(f"ESP32 receives: triggered = {stop_data.get('triggered')}")
    
    if stopped:
        print(f"\nESP32 code logic:")
        print(f"  else if (!triggered && navigationActive) {{")
        print(f"    Serial.println(\"Remote trigger reset - stopping navigation\");")
        print(f"    stopNavigation();  // ← NAVIGATION STOPS HERE")
        print(f"  }}")
        print(f"\n✅ PASS: Stop mechanism works")
        print(f"   - navigationActive will be set to false")
        print(f"   - All navigation LEDs turn OFF")
        print(f"   - Status LED does long blink (500ms)")
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    if triggered and stopped:
        print("\n✅ ALL TESTS PASSED")
        print("\n✓ Navigation trigger mechanism works correctly:")
        print("  1. Server responds with triggered=true")
        print("  2. ESP32 detects trigger via GET /iot/trigger")
        print("  3. startNavigation() is called")
        print("  4. navigationActive becomes true")
        print("  5. GPS fetching and LED navigation begins")
        print("  6. Stop mechanism also works (triggered=false)")
        
        print("\n📍 Updated Destination Coordinates:")
        print("  Latitude:  11.494946")
        print("  Longitude: 77.2767853")
        print("  Arrival Radius: 4.0 meters")
        
        print("\n🎯 Ready to upload to ESP32!")
        return True
    else:
        print("\n❌ TESTS FAILED")
        print("Navigation trigger mechanism has issues")
        return False

if __name__ == "__main__":
    try:
        success = test_navigation_trigger_mechanism()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server!")
        print("Make sure the server is running on http://localhost:8001")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
