#!/bin/bash
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
# Create DMG installer for macOS
# This script creates a distributable DMG file from the built application

set -e

echo "========================================"
echo "Creating Whistleblower DMG Installer"
echo "========================================"
echo ""

# Check if app exists
if [ ! -d "dist/Whistleblower.app" ]; then
    echo "Error: dist/Whistleblower.app not found"
    echo "Run ./build-macos.sh first"
    exit 1
fi

VERSION="1.0.0"
DMG_NAME="Whistleblower-macOS-v${VERSION}.dmg"
VOLUME_NAME="Whistleblower"
TEMP_DMG="temp-${DMG_NAME}"

echo "[1/4] Creating temporary DMG..."
mkdir -p dist/dmg
cp -r dist/Whistleblower.app dist/dmg/
ln -s /Applications dist/dmg/Applications

# Create DMG
hdiutil create -volname "${VOLUME_NAME}" \
    -srcfolder dist/dmg \
    -ov -format UDZO \
    "${TEMP_DMG}"

echo "[2/4] Optimizing DMG..."
mv "${TEMP_DMG}" "dist/${DMG_NAME}"

echo "[3/4] Cleaning up..."
rm -rf dist/dmg

echo "[4/4] Verifying DMG..."
hdiutil verify "dist/${DMG_NAME}"

echo ""
echo "========================================"
echo "DMG Created Successfully!"
echo "========================================"
echo ""
echo "Installer: dist/${DMG_NAME}"
DMG_SIZE=$(du -sh "dist/${DMG_NAME}" | cut -f1)
echo "Size: ${DMG_SIZE}"
echo ""
echo "To test:"
echo "  open dist/${DMG_NAME}"
echo ""
