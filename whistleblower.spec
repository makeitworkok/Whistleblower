# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Whistleblower Tkinter UI.

This builds executables for macOS (.app) and Windows (.exe) with all dependencies bundled.

To build:
    pyinstaller whistleblower.spec

The executable will be in the dist/ folder.
"""

import sys
from pathlib import Path

block_cipher = None

# Collect data files (only safe site templates/examples + docs)
sites_dir = Path('sites')
site_files = []
for pattern in ('*.template.json', '*.example.json'):
    site_files.extend(sites_dir.glob(pattern))
example_site = sites_dir / 'example.json'
if example_site.exists():
    site_files.append(example_site)

datas = [
    *[(str(p), 'sites') for p in sorted(site_files)],
    ('sites/README.md', 'sites'),
    ('docs', 'docs'),
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('requirements.txt', '.'),
]

# Platform-specific icon
if sys.platform == 'darwin':
    icon_file = 'assets/icon.icns'
elif sys.platform == 'win32':
    icon_file = 'assets/icon.ico'
else:
    icon_file = None

# Hidden imports for modules that PyInstaller might miss
hiddenimports = [
    # Core application modules
    'analyze_capture',
    'bootstrap_recorder',
    'whistleblower',
    'site_config',
    
    # Playwright and browser automation
    'playwright',
    'playwright.sync_api',
    'playwright._impl._api_types',
    'playwright._impl._connection',
    
    # Tkinter GUI
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'tkinter.filedialog',
    'tkinter.messagebox',
    
    # API and HTTP
    'requests',
    'urllib3',
    'certifi',
    
    # Standard library essentials
    'queue',
    'threading',
    'json',
    'pathlib',
    'subprocess',
]

# Analysis - find all Python modules and dependencies
a = Analysis(
    ['tkinter_ui_refactored.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI frameworks we don't use
        'matplotlib',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        
        # Data science libraries (not needed)
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        
        # Image processing (except Pillow for icons)
        'PIL.ImageQt',
        'PIL.ImageTk',
        
        # Development/testing tools
        'pytest',
        'doctest',
        'pdb',
        'pydoc',
        
        # Other unused modules
        'ftplib',
        'telnetlib',
        'xmlrpc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ archive of pure Python modules
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# EXE executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Whistleblower',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if icon_file and Path(icon_file).exists() else None,
)

# COLLECT - gather all files for distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Whistleblower',
)

# macOS Bundle configuration
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Whistleblower.app',
        icon=icon_file,
        bundle_identifier='com.makeitworkok.whistleblower',
        version='1.0.0',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': 'Whistleblower',
            'CFBundleDisplayName': 'Whistleblower',
            'CFBundleGetInfoString': 'Whistleblower - BAS Documentation System',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2026 MakeItWorkOK',
            'NSHighResolutionCapable': 'True',
        },
    )
