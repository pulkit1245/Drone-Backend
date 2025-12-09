#!/bin/bash
# Script to find and kill all processes sending fake data to the server

echo "=========================================="
echo "Finding processes sending fake data..."
echo "=========================================="

# Find Python processes (excluding the server itself)
echo -e "\n1. Checking for Python processes..."
ps aux | grep python | grep -v "server.py" | grep -v grep

# Find processes making requests to port 8001
echo -e "\n2. Checking for processes connected to port 8001..."
lsof -i :8001 | grep -v "server.py"

# Find any test_client or simulation scripts
echo -e "\n3. Checking for test/simulation scripts..."
ps aux | grep -E "(test_client|simulate|example_location)" | grep -v grep

echo -e "\n=========================================="
echo "To kill a specific process, use: kill -9 <PID>"
echo "To kill all Python processes except server:"
echo "  ps aux | grep python | grep -v server.py | grep -v grep | awk '{print \$2}' | xargs kill -9"
echo "=========================================="
