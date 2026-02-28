#!/bin/bash
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
# Launch Whistleblower Application
# This script launches the built Whistleblower.app

clear
echo "╔════════════════════════════════════════╗"
echo "║   Launching Whistleblower...          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if app exists
if [ ! -d "dist/Whistleblower.app" ]; then
    echo "❌ Error: Whistleblower.app not found in dist/"
    echo ""
    echo "Please build the app first:"
    echo "  ./build-macos.sh"
    echo ""
    exit 1
fi

# Launch the app using macOS 'open' command
echo "Opening Whistleblower.app..."
open dist/Whistleblower.app

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Whistleblower launched successfully!"
    echo ""
    echo "If the app doesn't appear:"
    echo "  1. Check System Settings > Privacy & Security"
    echo "  2. Look for a message about blocking Whistleblower"
    echo "  3. Click 'Open Anyway'"
    echo ""
else
    echo ""
    echo "❌ Failed to launch Whistleblower"
    echo ""
    echo "Try running directly:"
    echo "  open dist/Whistleblower.app"
    echo ""
    echo "Or double-click: dist/Whistleblower.app"
    echo ""
    exit 1
fi
