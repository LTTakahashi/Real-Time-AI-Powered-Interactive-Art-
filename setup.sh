#!/bin/bash
# GestureCanvas Setup Script
# Installs desktop app dependencies and builds the frontend

set -e  # Exit on error

echo "================================"
echo "GestureCanvas Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"
echo ""

# Install only NEW dependencies for desktop app
# (ML libraries like mediapipe, torch, etc. are already installed)
echo "Installing desktop app dependencies..."
echo "  - fastapi"
echo "  - uvicorn"
echo "  - websockets"
echo "  - requests"
pip3 install --user fastapi 'uvicorn[standard]' websockets requests
echo "✓ Desktop app dependencies installed"
echo ""

# Note about existing dependencies
echo "Note: Using existing ML dependencies (MediaPipe, PyTorch, etc.)"
echo "      These are already installed and working on your system."
echo ""

# Check Node.js
echo "Checking Node.js..."
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm not found. Please install Node.js first:"
    echo "  https://nodejs.org/"
    exit 1
fi
node_version=$(node --version)
echo "Found Node.js $node_version"
echo ""

# Install frontend dependencies (if needed)
echo "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    echo "✓ Frontend dependencies installed"
else
    echo "✓ Frontend dependencies already installed"
fi
echo ""

# Build frontend
echo "Building frontend..."
npx vite build
echo "✓ Frontend built successfully"
cd ..
echo ""

echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To run the app:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  python launcher.py"
echo ""
