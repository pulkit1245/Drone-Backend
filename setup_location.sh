#!/bin/bash

echo "=================================="
echo "macOS Location Service Setup"
echo "=================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed."
    echo "Install Homebrew first: https://brew.sh"
    echo ""
    echo "Run this command:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

echo "✓ Homebrew is installed"
echo ""

# Install CoreLocationCLI
echo "Installing CoreLocationCLI..."
if brew install corelocationcli; then
    echo "✓ CoreLocationCLI installed successfully"
else
    echo "⚠ CoreLocationCLI installation failed, trying whereami as alternative..."
    
    # Try whereami as alternative
    if brew install whereami; then
        echo "✓ whereami installed successfully"
    else
        echo "❌ Both installations failed"
        exit 1
    fi
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Grant location permissions:"
echo "   System Preferences → Security & Privacy → Privacy → Location Services"
echo "   Enable for Terminal (or your Python IDE)"
echo ""
echo "2. Test the location service:"
echo "   python location_service.py"
echo ""
echo "3. Start the server with location support:"
echo "   python server.py"
echo ""
echo "4. Get your location via API:"
echo "   curl http://localhost:5000/location"
echo ""
