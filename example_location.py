#!/usr/bin/env python3
"""
Example script showing how to use the location service with RSSI data.
This demonstrates logging RSSI readings with GPS coordinates.
"""

import time
from location_service import LocationService
from datetime import datetime


def main():
    """Demo: Get location and display it."""
    print("\n" + "=" * 70)
    print(" " * 15 + "Location Service Example")
    print("=" * 70)
    
    service = LocationService()
    
    # Get current location
    print("\n1. Getting current location...")
    location = service.get_coordinates()
    
    if location:
        print(f"   ✓ Latitude:  {location['latitude']:.6f}°")
        print(f"   ✓ Longitude: {location['longitude']:.6f}°")
        print(f"   ✓ Accuracy:  ±{location.get('accuracy', 0):.1f}m")
        print(f"   ✓ Formatted: {service.format_coordinates(location)}")
        print(f"   ✓ Maps URL:  {service.get_google_maps_url(location)}")
    else:
        print("   ✗ Unable to get location")
        print("\n   Make sure you've run: ./setup_location.sh")
        return
    
    # Demonstrate caching
    print("\n2. Testing cached location (should be instant)...")
    time.sleep(1)
    cached = service.get_cached_location(max_age_seconds=60)
    
    if cached:
        print(f"   ✓ Using cached location from {cached['timestamp']}")
        print(f"   ✓ {service.format_coordinates(cached)}")
    else:
        print("   ✗ No cached location available")
    
    # Simulate RSSI reading with location
    print("\n3. Simulating RSSI reading with location...")
    rssi_data = {
        'helmet_id': 1234,
        'rssi': -67,
        'location': location,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"   Helmet ID: {rssi_data['helmet_id']}")
    print(f"   RSSI: {rssi_data['rssi']} dBm")
    print(f"   Position: {service.format_coordinates(rssi_data['location'])}")
    print(f"   Timestamp: {rssi_data['timestamp']}")
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
