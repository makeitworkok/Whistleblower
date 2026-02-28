#!/bin/bash
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
# Build script for Whistleblower macOS Application
# This script builds and packages the application for macOS distribution

set -e  # Exit on error

echo "========================================"
echo "Whistleblower macOS Build Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is for macOS only"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv312" ]; then
    echo "${YELLOW}[1/6]${NC} Activating virtual environment..."
    source .venv312/bin/activate
    echo "      ${GREEN}✓${NC} Done."
    echo ""
else
    echo "${YELLOW}Warning:${NC} Virtual environment .venv312 not found"
    echo "      Using system Python"
    echo ""
fi

# Check Python version
echo "${YELLOW}[2/6]${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version)
echo "      Python: $PYTHON_VERSION"
echo ""

# Install/check dependencies
echo "${YELLOW}[3/6]${NC} Checking build dependencies..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "      Installing PyInstaller..."
    pip install pyinstaller
fi
if ! python3 -c "import PIL" 2>/dev/null; then
    echo "      Installing Pillow..."
    pip install Pillow
fi
echo "      ${GREEN}✓${NC} Dependencies ready."
echo ""

# Create/update icons
echo "${YELLOW}[4/6]${NC} Generating application icons..."
cd assets
python3 create_icon.py
cd ..
echo "      ${GREEN}✓${NC} Icons created."
echo ""

# Clean previous build
echo "${YELLOW}[5/6]${NC} Cleaning previous build..."
if [ -d "build" ]; then
    rm -rf build
fi
if [ -d "dist" ]; then
    rm -rf dist
fi
echo "      ${GREEN}✓${NC} Clean complete."
echo ""

# Build application
echo "${YELLOW}[6/6]${NC} Building Whistleblower.app..."
echo "      This may take a few minutes..."
pyinstaller whistleblower.spec --clean --noconfirm

if [ $? -eq 0 ]; then
    echo "      ${GREEN}✓${NC} Build complete!"
    echo ""
    
    # Show results
    echo "========================================"
    echo "${GREEN}Build Successful!${NC}"
    echo "========================================"
    echo ""
    
    if [ -d "dist/Whistleblower.app" ]; then
        APP_SIZE=$(du -sh dist/Whistleblower.app | cut -f1)
        echo "Application: dist/Whistleblower.app"
        echo "Size: $APP_SIZE"
        echo ""
        echo "To run:"
        echo "  open dist/Whistleblower.app"
        echo ""
        echo "To create DMG installer:"
        echo "  ./create-dmg.sh"
    else
        echo "Bundle: dist/Whistleblower/"
        BUNDLE_SIZE=$(du -sh dist/Whistleblower | cut -f1)
        echo "Size: $BUNDLE_SIZE"
        echo ""
        echo "To run:"
        echo "  ./dist/Whistleblower/Whistleblower"
    fi
    
    echo ""
    echo "Build logs: build/whistleblower/"
else
    echo ""
    echo "========================================"
    echo "${YELLOW}Build Failed${NC}"
    echo "========================================"
    echo ""
    echo "Check build/whistleblower/warn-whistleblower.txt for details"
    exit 1
fi
