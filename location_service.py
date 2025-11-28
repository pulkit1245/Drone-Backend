#!/usr/bin/env python3
"""
Location Service for macOS
Gets current GPS coordinates from the MacBook using Core Location.
"""

import subprocess
import json
import time
from datetime import datetime


class LocationService:
    """Service to get GPS coordinates from macOS."""
    
    def __init__(self):
        self.last_location = None
        self.last_update = None
    
    def get_coordinates_via_corelocation(self):
        """
        Get coordinates using CoreLocationCLI (requires installation).
        Install with: brew install corelocationcli
        
        Returns:
            dict: {'latitude': float, 'longitude': float, 'accuracy': float, 'timestamp': str}
            None: if unable to get location
        """
        try:
            # Run CoreLocationCLI to get location
            result = subprocess.run(
                ['CoreLocationCLI', '-json', '-once'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                location = {
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'accuracy': data.get('horizontalAccuracy'),
                    'altitude': data.get('altitude'),
                    'timestamp': datetime.now().isoformat()
                }
                self.last_location = location
                self.last_update = time.time()
                return location
            else:
                print(f"Error getting location: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("CoreLocationCLI not found. Install with: brew install corelocationcli")
            return None
        except subprocess.TimeoutExpired:
            print("Location request timed out")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_coordinates_via_whereami(self):
        """
        Get coordinates using whereami (alternative tool).
        Install with: brew install whereami
        
        Returns:
            dict: {'latitude': float, 'longitude': float, 'timestamp': str}
            None: if unable to get location
        """
        try:
            result = subprocess.run(
                ['whereami', '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                location = {
                    'latitude': data.get('Latitude'),
                    'longitude': data.get('Longitude'),
                    'accuracy': data.get('HorizontalAccuracy'),
                    'timestamp': datetime.now().isoformat()
                }
                self.last_location = location
                self.last_update = time.time()
                return location
            else:
                print(f"Error getting location: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("whereami not found. Install with: brew install whereami")
            return None
        except subprocess.TimeoutExpired:
            print("Location request timed out")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_coordinates_via_applescript(self):
        """
        Get coordinates using AppleScript to access Location Services.
        This is a fallback method that doesn't require additional tools.
        
        Returns:
            dict: {'latitude': float, 'longitude': float, 'timestamp': str}
            None: if unable to get location
        """
        applescript = '''
        use framework "CoreLocation"
        use scripting additions

        set locationManager to current application's CLLocationManager's alloc()'s init()
        
        -- Check if location services are enabled
        if current application's CLLocationManager's locationServicesEnabled() is false then
            return "Location services disabled"
        end if
        
        -- Request location authorization
        locationManager's requestWhenInUseAuthorization()
        
        -- Get location
        locationManager's startUpdatingLocation()
        delay 2
        
        set currentLocation to locationManager's location()
        locationManager's stopUpdatingLocation()
        
        if currentLocation is missing value then
            return "Unable to get location"
        end if
        
        set lat to currentLocation's coordinate()'s latitude as text
        set lon to currentLocation's coordinate()'s longitude as text
        set acc to currentLocation's horizontalAccuracy() as text
        
        return "{\\"latitude\\":" & lat & ",\\"longitude\\":" & lon & ",\\"accuracy\\":" & acc & "}"
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-l', 'JavaScript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip().startswith('{'):
                data = json.loads(result.stdout.strip())
                location = {
                    'latitude': float(data.get('latitude')),
                    'longitude': float(data.get('longitude')),
                    'accuracy': float(data.get('accuracy')),
                    'timestamp': datetime.now().isoformat()
                }
                self.last_location = location
                self.last_update = time.time()
                return location
            else:
                print(f"AppleScript error: {result.stdout}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_coordinates(self, method='auto'):
        """
        Get current GPS coordinates using the best available method.
        
        Args:
            method: 'auto', 'corelocation', 'whereami', or 'applescript'
        
        Returns:
            dict: Location data with latitude, longitude, accuracy, timestamp
            None: if unable to get location
        """
        if method == 'auto':
            # Try methods in order of preference
            location = self.get_coordinates_via_corelocation()
            if location:
                return location
            
            location = self.get_coordinates_via_whereami()
            if location:
                return location
            
            location = self.get_coordinates_via_applescript()
            return location
        
        elif method == 'corelocation':
            return self.get_coordinates_via_corelocation()
        
        elif method == 'whereami':
            return self.get_coordinates_via_whereami()
        
        elif method == 'applescript':
            return self.get_coordinates_via_applescript()
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def get_cached_location(self, max_age_seconds=60):
        """
        Get cached location if it's recent enough.
        
        Args:
            max_age_seconds: Maximum age of cached location in seconds
        
        Returns:
            dict: Cached location or None if too old or not available
        """
        if self.last_location and self.last_update:
            age = time.time() - self.last_update
            if age <= max_age_seconds:
                return self.last_location
        return None
    
    def format_coordinates(self, location):
        """
        Format coordinates for display.
        
        Args:
            location: Location dict from get_coordinates()
        
        Returns:
            str: Formatted string
        """
        if not location:
            return "Location unavailable"
        
        lat = location.get('latitude', 0)
        lon = location.get('longitude', 0)
        acc = location.get('accuracy', 0)
        
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'
        
        return (f"{abs(lat):.6f}°{lat_dir}, {abs(lon):.6f}°{lon_dir} "
                f"(±{acc:.1f}m)")
    
    def get_google_maps_url(self, location):
        """
        Generate Google Maps URL for the location.
        
        Args:
            location: Location dict from get_coordinates()
        
        Returns:
            str: Google Maps URL
        """
        if not location:
            return None
        
        lat = location.get('latitude')
        lon = location.get('longitude')
        
        return f"https://www.google.com/maps?q={lat},{lon}"


def main():
    """Demo/test the location service."""
    print("\n" + "=" * 70)
    print(" " * 20 + "macOS Location Service")
    print("=" * 70)
    
    service = LocationService()
    
    print("\nAttempting to get current location...")
    print("(This may take a few seconds and requires location permissions)\n")
    
    location = service.get_coordinates()
    
    if location:
        print("✓ Location acquired successfully!\n")
        print("-" * 70)
        print(f"Latitude:  {location['latitude']:.6f}°")
        print(f"Longitude: {location['longitude']:.6f}°")
        print(f"Accuracy:  ±{location.get('accuracy', 0):.1f} meters")
        if 'altitude' in location and location['altitude']:
            print(f"Altitude:  {location['altitude']:.1f} meters")
        print(f"Timestamp: {location['timestamp']}")
        print("-" * 70)
        print(f"\nFormatted: {service.format_coordinates(location)}")
        print(f"\nGoogle Maps: {service.get_google_maps_url(location)}")
        print()
    else:
        print("✗ Unable to get location\n")
        print("Troubleshooting:")
        print("1. Install CoreLocationCLI: brew install corelocationcli")
        print("   OR")
        print("2. Install whereami: brew install whereami")
        print("\n3. Grant location permissions:")
        print("   System Preferences → Security & Privacy → Privacy → Location Services")
        print("   Enable for Terminal or your Python application")
        print()


if __name__ == "__main__":
    main()
