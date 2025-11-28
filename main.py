#!/usr/bin/env python3
"""
RSSI Data Viewer
================
Interactive terminal application to view and monitor RSSI signal strength data from ESP32 helmets.

Features: Summary View, Live View, Recent Readings

Author: Pulkit Verma
Date: 2025-11-27
"""

import csv
import os
import time
from datetime import datetime
from collections import defaultdict


class RSSIViewer:
    """Interactive viewer for RSSI signal strength data."""
    
    def __init__(self, log_file="rssi_log.csv"):
        """
        Initialize the RSSI viewer.
        
        Args:
            log_file (str): Path to CSV file (default: rssi_log.csv)
        """
        self.log_file = log_file
        self.last_position = 0  # For tracking new data in live view
        
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def read_all_data(self):
        """Read all data from the CSV file."""
        if not os.path.exists(self.log_file):
            return []
        
        data = []
        with open(self.log_file, mode="r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def read_new_data(self):
        """Read only new data since last read."""
        if not os.path.exists(self.log_file):
            return []
        
        new_data = []
        with open(self.log_file, mode="r") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= self.last_position:
                    new_data.append(row)
            self.last_position = i + 1 if reader.line_num > 1 else 0
        
        return new_data
    
    def get_signal_strength(self, rssi):
        """Convert RSSI to signal strength description."""
        rssi = int(rssi)
        if rssi >= -50:
            return "Excellent"
        elif rssi >= -60:
            return "Good"
        elif rssi >= -70:
            return "Fair"
        elif rssi >= -80:
            return "Weak"
        else:
            return "Very Weak"
    
    def get_signal_bars(self, rssi):
        """Convert RSSI to visual signal bars."""
        rssi = int(rssi)
        if rssi >= -50:
            return "█████"
        elif rssi >= -60:
            return "████░"
        elif rssi >= -70:
            return "███░░"
        elif rssi >= -80:
            return "██░░░"
        else:
            return "█░░░░"
    
    def display_summary(self):
        """Display summary statistics of all RSSI data."""
        data = self.read_all_data()
        
        if not data:
            print("No data available yet. Waiting for RSSI readings...")
            return
        
        # Group by helmet_id
        helmet_data = defaultdict(list)
        for row in data:
            helmet_id = row['helmet_id']
            rssi = int(row['rssi'])
            helmet_data[helmet_id].append(rssi)
        
        self.clear_screen()
        print("=" * 80)
        print(" " * 25 + "RSSI DATA SUMMARY")
        print("=" * 80)
        print(f"\nTotal readings: {len(data)}")
        print(f"Active helmets: {len(helmet_data)}")
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("-" * 80)
        print(f"{'Helmet ID':<12} {'Readings':<10} {'Avg RSSI':<12} {'Min':<8} {'Max':<8} {'Status':<15}")
        print("-" * 80)
        
        for helmet_id, rssi_values in sorted(helmet_data.items()):
            avg_rssi = sum(rssi_values) / len(rssi_values)
            min_rssi = min(rssi_values)
            max_rssi = max(rssi_values)
            status = self.get_signal_strength(avg_rssi)
            bars = self.get_signal_bars(avg_rssi)
            
            print(f"{helmet_id:<12} {len(rssi_values):<10} {avg_rssi:>6.1f} dBm   "
                  f"{min_rssi:>4} dBm {max_rssi:>4} dBm {bars} {status}")
        
        print("-" * 80)
    
    def display_live(self):
        """Display live RSSI readings as they come in."""
        print("\n" + "=" * 80)
        print(" " * 25 + "LIVE RSSI READINGS")
        print("=" * 80)
        print(f"{'Timestamp':<22} {'Helmet ID':<12} {'RSSI':<12} {'Signal %':<10} {'Bars':<10} {'IP':<15}")
        print("-" * 80)
        
        while True:
            new_data = self.read_new_data()
            
            for row in new_data:
                timestamp = datetime.fromisoformat(row['timestamp_iso']).strftime('%Y-%m-%d %H:%M:%S')
                helmet_id = row['helmet_id']
                rssi = int(row['rssi'])
                signal = int(row.get('signal_percent', 0))
                client_ip = row['client_ip']
                bars = self.get_signal_bars(rssi)
                
                print(f"{timestamp:<22} {helmet_id:<12} {rssi:>4} dBm    {signal:>3}%      {bars:<10} {client_ip:<15}")
            
            time.sleep(1)  # Check for new data every second
    
    def display_recent(self, n=10):
        """Display the most recent n readings."""
        data = self.read_all_data()
        
        if not data:
            print("No data available yet.")
            return
        
        recent = data[-n:] if len(data) >= n else data
        
        self.clear_screen()
        print("=" * 80)
        print(f" " * 25 + f"LAST {len(recent)} RSSI READINGS")
        print("=" * 80)
        print(f"{'Timestamp':<22} {'Helmet ID':<12} {'RSSI':<12} {'Signal %':<10} {'Bars':<10} {'IP':<15}")
        print("-" * 80)
        
        for row in recent:
            timestamp = datetime.fromisoformat(row['timestamp_iso']).strftime('%Y-%m-%d %H:%M:%S')
            helmet_id = row['helmet_id']
            rssi = int(row['rssi'])
            signal = int(row.get('signal_percent', 0))
            client_ip = row['client_ip']
            bars = self.get_signal_bars(rssi)
            
            print(f"{timestamp:<22} {helmet_id:<12} {rssi:>4} dBm    {signal:>3}%      {bars:<10} {client_ip:<15}")
        
        print("-" * 80)


def main():
    """Main entry point."""
    viewer = RSSIViewer()
    
    print("\n" + "=" * 80)
    print(" " * 20 + "ESP32 RSSI Data Viewer")
    print("=" * 80)
    print("\nSelect viewing mode:")
    print("  1. Summary view (statistics by helmet)")
    print("  2. Live view (real-time updates)")
    print("  3. Recent readings (last 10)")
    print("  4. Recent readings (last 50)")
    print("  5. Exit")
    print("-" * 80)
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        while True:
            viewer.display_summary()
            print("\nPress Ctrl+C to return to menu...")
            try:
                time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                print("\n")
                main()
                break
    
    elif choice == "2":
        try:
            viewer.display_live()
        except KeyboardInterrupt:
            print("\n")
            main()
    
    elif choice == "3":
        viewer.display_recent(10)
        input("\nPress Enter to return to menu...")
        main()
    
    elif choice == "4":
        viewer.display_recent(50)
        input("\nPress Enter to return to menu...")
        main()
    
    elif choice == "5":
        print("\nExiting...")
        return
    
    else:
        print("\nInvalid choice. Please try again.")
        time.sleep(1)
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
