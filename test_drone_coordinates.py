#!/usr/bin/env python3
"""
Test script for the drone coordinates endpoint.
Demonstrates how to use /get-coordinates-drone endpoint.
"""

import requests
import time


def test_drone_endpoint(server_url="http://localhost:5000"):
    """Test the /get-coordinates-drone endpoint."""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "Drone Coordinates Endpoint Test")
    print("=" * 70)
    print(f"\nServer: {server_url}")
    print("-" * 70)
    
    # Test 1: Get fresh coordinates
    print("\n1. Getting fresh coordinates...")
    try:
        response = requests.get(f"{server_url}/get-coordinates-drone", timeout=10)
        
        if response.status_code == 200:
            coords = response.json()
            print(f"   ✓ Success!")
            print(f"   Response: {coords}")
            print(f"   Latitude:  {coords[0]}°")
            print(f"   Longitude: {coords[1]}°")
            print(f"   Reserved:  {coords[2]}")
            print(f"   Accuracy:  ±{coords[3]}m")
        else:
            print(f"   ✗ Error: HTTP {response.status_code}")
            print(f"   Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
        print("\n   Make sure the server is running:")
        print("   python3 server.py")
        return
    
    # Test 2: Get cached coordinates (should be faster)
    print("\n2. Getting cached coordinates (faster)...")
    try:
        start_time = time.time()
        response = requests.get(
            f"{server_url}/get-coordinates-drone?cached=true",
            timeout=10
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            coords = response.json()
            print(f"   ✓ Success! (took {elapsed:.3f}s)")
            print(f"   Response: {coords}")
        else:
            print(f"   ✗ Error: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
    
    # Test 3: Parse as array
    print("\n3. Parsing coordinates as array...")
    try:
        response = requests.get(f"{server_url}/get-coordinates-drone", timeout=10)
        
        if response.status_code == 200:
            coords = response.json()
            
            # Unpack the array
            latitude, longitude, reserved, accuracy = coords
            
            print(f"   ✓ Successfully unpacked array:")
            print(f"   coords[0] = latitude  = {latitude}")
            print(f"   coords[1] = longitude = {longitude}")
            print(f"   coords[2] = reserved  = {reserved}")
            print(f"   coords[3] = accuracy  = {accuracy}")
            
            # Example: Use in calculations
            print(f"\n   Example usage:")
            print(f"   Location: ({latitude:.6f}, {longitude:.6f})")
            print(f"   Precision: ±{accuracy:.1f} meters")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Request failed: {e}")
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70 + "\n")


def simulate_drone_polling(server_url="http://localhost:5000", duration=30, interval=2):
    """
    Simulate a drone polling for coordinates periodically.
    
    Args:
        server_url: Base URL of the server
        duration: How long to poll in seconds
        interval: Seconds between polls
    """
    print("\n" + "=" * 70)
    print(" " * 15 + "Simulating Drone Coordinate Polling")
    print("=" * 70)
    print(f"Server: {server_url}")
    print(f"Duration: {duration}s, Interval: {interval}s")
    print("-" * 70)
    print(f"{'Time':<10} {'Latitude':<12} {'Longitude':<12} {'Accuracy':<10}")
    print("-" * 70)
    
    start_time = time.time()
    count = 0
    
    while time.time() - start_time < duration:
        try:
            # Use cached for faster polling
            response = requests.get(
                f"{server_url}/get-coordinates-drone?cached=true",
                timeout=5
            )
            
            if response.status_code == 200:
                coords = response.json()
                lat, lon, _, acc = coords
                
                elapsed = int(time.time() - start_time)
                print(f"{elapsed}s{' ' * (10-len(str(elapsed)))} "
                      f"{lat:>11.6f}° {lon:>11.6f}° ±{acc:>6.1f}m")
                count += 1
            else:
                print(f"Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            break
        
        time.sleep(interval)
    
    print("-" * 70)
    print(f"Polling complete. Received {count} coordinate updates.")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print(" " * 15 + "Drone Coordinates Test Menu")
    print("=" * 70)
    
    server_url = input("\nEnter server URL (default: http://localhost:5000): ").strip()
    if not server_url:
        server_url = "http://localhost:5000"
    
    print("\nSelect test mode:")
    print("  1. Basic endpoint test")
    print("  2. Simulate drone polling (30 seconds)")
    print("  3. Simulate drone polling (custom duration)")
    print("  4. Exit")
    print("-" * 70)
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        test_drone_endpoint(server_url)
    
    elif choice == "2":
        simulate_drone_polling(server_url, duration=30, interval=2)
    
    elif choice == "3":
        duration = input("Duration in seconds (default: 60): ").strip()
        duration = int(duration) if duration else 60
        
        interval = input("Interval between polls in seconds (default: 2): ").strip()
        interval = int(interval) if interval else 2
        
        simulate_drone_polling(server_url, duration, interval)
    
    elif choice == "4":
        print("\nExiting...")
        return
    
    else:
        print("\nInvalid choice.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
