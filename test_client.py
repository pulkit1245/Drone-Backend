#!/usr/bin/env python3
"""
Test client to simulate ESP32 helmet sending RSSI data.
Useful for testing the server without actual hardware.
"""

import requests
import time
import random
from datetime import datetime


def send_rssi(server_url, helmet_id, rssi):
    """Send RSSI data to the server."""
    try:
        response = requests.post(
            f"{server_url}/rssi",
            json={"helmet_id": helmet_id, "rssi": rssi},
            timeout=5
        )
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return None, str(e)


def simulate_helmet(server_url, helmet_id, duration=60, interval=2):
    """
    Simulate a helmet sending RSSI data.
    
    Args:
        server_url: Base URL of the server (e.g., http://localhost:5000)
        helmet_id: ID of the helmet to simulate
        duration: How long to run simulation in seconds
        interval: Seconds between each reading
    """
    print(f"Simulating helmet {helmet_id} for {duration} seconds...")
    print(f"Sending data every {interval} seconds to {server_url}")
    print("-" * 60)
    
    start_time = time.time()
    count = 0
    
    # Simulate realistic RSSI values that fluctuate
    base_rssi = random.randint(-75, -55)
    
    while time.time() - start_time < duration:
        # Add some random fluctuation to RSSI
        rssi = base_rssi + random.randint(-5, 5)
        
        status_code, response = send_rssi(server_url, helmet_id, rssi)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if status_code == 200:
            count += 1
            print(f"[{timestamp}] ✓ Sent: helmet_id={helmet_id}, rssi={rssi} dBm")
        else:
            print(f"[{timestamp}] ✗ Error: {response}")
        
        time.sleep(interval)
    
    print("-" * 60)
    print(f"Simulation complete. Sent {count} readings.")


def simulate_multiple_helmets(server_url, num_helmets=3, duration=60):
    """
    Simulate multiple helmets sending data simultaneously.
    
    Args:
        server_url: Base URL of the server
        num_helmets: Number of helmets to simulate
        duration: How long to run simulation in seconds
    """
    print(f"Simulating {num_helmets} helmets for {duration} seconds...")
    print(f"Server: {server_url}")
    print("-" * 60)
    
    start_time = time.time()
    helmet_ids = [1000 + i for i in range(num_helmets)]
    base_rssi_values = {hid: random.randint(-75, -55) for hid in helmet_ids}
    count = 0
    
    while time.time() - start_time < duration:
        # Each helmet sends data with slight random timing
        for helmet_id in helmet_ids:
            rssi = base_rssi_values[helmet_id] + random.randint(-5, 5)
            status_code, response = send_rssi(server_url, helmet_id, rssi)
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if status_code == 200:
                count += 1
                print(f"[{timestamp}] ✓ Helmet {helmet_id}: {rssi} dBm")
            else:
                print(f"[{timestamp}] ✗ Helmet {helmet_id}: Error - {response}")
            
            # Small delay between helmets
            time.sleep(0.1)
        
        # Wait before next round
        time.sleep(2)
    
    print("-" * 60)
    print(f"Simulation complete. Sent {count} total readings from {num_helmets} helmets.")


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print(" " * 15 + "ESP32 RSSI Test Client")
    print("=" * 60)
    
    server_url = input("\nEnter server URL (default: http://localhost:5000): ").strip()
    if not server_url:
        server_url = "http://localhost:5000"
    
    print("\nSelect test mode:")
    print("  1. Single helmet simulation")
    print("  2. Multiple helmets simulation")
    print("  3. Send single test reading")
    print("  4. Exit")
    print("-" * 60)
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        helmet_id = input("Enter helmet ID (default: 1234): ").strip()
        helmet_id = int(helmet_id) if helmet_id else 1234
        
        duration = input("Duration in seconds (default: 60): ").strip()
        duration = int(duration) if duration else 60
        
        interval = input("Interval between readings in seconds (default: 2): ").strip()
        interval = int(interval) if interval else 2
        
        simulate_helmet(server_url, helmet_id, duration, interval)
    
    elif choice == "2":
        num_helmets = input("Number of helmets (default: 3): ").strip()
        num_helmets = int(num_helmets) if num_helmets else 3
        
        duration = input("Duration in seconds (default: 60): ").strip()
        duration = int(duration) if duration else 60
        
        simulate_multiple_helmets(server_url, num_helmets, duration)
    
    elif choice == "3":
        helmet_id = input("Enter helmet ID (default: 1234): ").strip()
        helmet_id = int(helmet_id) if helmet_id else 1234
        
        rssi = input("Enter RSSI value (default: -67): ").strip()
        rssi = int(rssi) if rssi else -67
        
        print(f"\nSending test reading...")
        status_code, response = send_rssi(server_url, helmet_id, rssi)
        
        if status_code == 200:
            print(f"✓ Success: {response}")
        else:
            print(f"✗ Error: {response}")
    
    elif choice == "4":
        print("\nExiting...")
        return
    
    else:
        print("\nInvalid choice.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
