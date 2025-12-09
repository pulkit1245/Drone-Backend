#!/bin/bash
# Quick script to stop all fake data sources

echo "🛑 Stopping all fake data sources..."
echo "======================================"

# 1. Kill any test/simulation Python scripts
echo -e "\n1. Killing simulation scripts..."
pkill -f "test_client.py" 2>/dev/null && echo "   ✓ Killed test_client.py" || echo "   ℹ No test_client.py running"
pkill -f "example_location.py" 2>/dev/null && echo "   ✓ Killed example_location.py" || echo "   ℹ No example_location.py running"
pkill -f "simulate" 2>/dev/null && echo "   ✓ Killed simulation scripts" || echo "   ℹ No simulation scripts running"

# 2. Kill Android emulators
echo -e "\n2. Checking for Android emulators..."
if command -v adb &> /dev/null; then
    adb devices 2>/dev/null | grep emulator | cut -f1 | while read device; do
        adb -s "$device" emu kill 2>/dev/null && echo "   ✓ Killed emulator: $device"
    done
else
    echo "   ℹ adb not installed, skipping emulator check"
fi

# 3. Clear all drone data
echo -e "\n3. Clearing all drone data..."
curl -s -X POST "http://localhost:8001/clear-drone-data?confirm=yes" > /dev/null 2>&1 && \
    echo "   ✓ Cleared drone data" || \
    echo "   ⚠ Could not clear data (server might not be running)"

echo -e "\n======================================"
echo "✅ Done! Your server should now be clean."
echo "======================================"
