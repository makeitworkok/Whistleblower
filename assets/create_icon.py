#!/usr/bin/env python3
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
"""
Create application icon from text or image.
This script generates icons for macOS (.icns) and Windows (.ico).
"""

import importlib
from typing import Any

try:
    Image: Any = importlib.import_module("PIL.Image")
    ImageDraw: Any = importlib.import_module("PIL.ImageDraw")
    ImageFont: Any = importlib.import_module("PIL.ImageFont")
    HAS_PIL = True
except ModuleNotFoundError:
    HAS_PIL = False
    Image = None
    ImageDraw = None
    ImageFont = None
    print("Note: Install Pillow for icon generation: pip install Pillow")

def create_simple_icon(output_path="icon.png", size=512):
    """Create a simple icon with 'W' letter."""
    if not HAS_PIL:
        print("Pillow not installed. Cannot create icon.")
        return False
    
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#1e3a5f')
    draw = ImageDraw.Draw(img)
    
    # Draw circle background
    margin = size // 10
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#2c5aa0')
    
    # Draw 'W' text
    try:
        # Try to use a nice font
        font_size = size // 2
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()
    
    text = "W"
    # Calculate text position to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2 - size//10)
    
    draw.text(position, text, fill='#ffffff', font=font)
    
    # Save PNG
    img.save(output_path)
    print(f"✓ Created {output_path}")
    return True

def create_icns_from_png(png_path, icns_path):
    """Convert PNG to ICNS for macOS (requires iconutil on macOS)."""
    import subprocess
    import os
    import tempfile
    
    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found")
        return False
    
    # Create iconset directory
    with tempfile.TemporaryDirectory() as tmpdir:
        iconset_dir = os.path.join(tmpdir, "icon.iconset")
        os.makedirs(iconset_dir)
        
        # Generate required sizes for macOS
        sizes = [16, 32, 64, 128, 256, 512]
        
        if not HAS_PIL:
            print("Pillow required to resize icons")
            return False
        
        img = Image.open(png_path)
        
        for size in sizes:
            # Regular resolution
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(os.path.join(iconset_dir, f"icon_{size}x{size}.png"))
            
            # Retina resolution
            if size <= 256:
                resized_2x = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
                resized_2x.save(os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png"))
        
        # Convert to icns using iconutil (macOS only)
        try:
            subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], 
                          check=True, capture_output=True)
            print(f"✓ Created {icns_path}")
            return True
        except subprocess.CalledProcessError:
            print("Error: iconutil failed (macOS only)")
            return False
        except FileNotFoundError:
            print("Error: iconutil not found (macOS only)")
            return False

def create_ico_from_png(png_path, ico_path):
    """Convert PNG to ICO for Windows."""
    if not HAS_PIL:
        print("Pillow required to create ICO")
        return False
    
    img = Image.open(png_path)
    
    # Create multiple sizes for Windows
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    img.save(ico_path, format='ICO', sizes=sizes)
    print(f"✓ Created {ico_path}")
    return True

if __name__ == "__main__":
    import sys
    import os
    
    # Change to assets directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("Creating Whistleblower application icons...")
    
    # Create base PNG icon
    if create_simple_icon("icon.png", 1024):
        # Create macOS .icns
        if sys.platform == "darwin":
            create_icns_from_png("icon.png", "icon.icns")
        
        # Create Windows .ico
        create_ico_from_png("icon.png", "icon.ico")
        
        print("\n✓ Icon creation complete!")
        print("  - icon.png (1024x1024 source)")
        if sys.platform == "darwin":
            print("  - icon.icns (macOS)")
        print("  - icon.ico (Windows)")
    else:
        print("\n✗ Icon creation failed. Install Pillow: pip install Pillow")
        sys.exit(1)
