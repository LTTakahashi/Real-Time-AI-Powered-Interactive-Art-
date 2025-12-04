#!/bin/bash
# GestureCanvas Run Script
# Quick launcher for the desktop app

set -e

echo "Starting GestureCanvas..."
echo ""

# Check if frontend is built
if [ ! -f "frontend/dist/index.html" ]; then
    echo "ERROR: Frontend not built!"
    echo "Please run: ./setup.sh"
    exit 1
fi

# Launch the app (using Python 3.11 for MediaPipe compatibility)
python3.11 launcher.py
