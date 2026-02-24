# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Whistleblower Tkinter UI.

This builds a Windows executable with all dependencies bundled.

To build:
    pyinstaller whistleblower.spec

The executable will be in the dist/ folder.
"""

import sys
from pathlib import Path

block_cipher = None

# Collect data files (sites/*.json configs and docs)
datas = [
    ('sites', 'sites'),
    ('docs', 'docs'),
    ('README.md', '.'),
    ('LICENSE', '.'),
    ('requirements.txt', '.'),
]

# Test imports for site_config and other modules
hiddenimports = [
    'analyze_capture',
    'bootstrap_recorder',
    'whistleblower',
    'site_config',
    'playwright',
    'playwright.sync_api',
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'queue',
    'threading',
    'json',
    'pathlib',
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
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
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
    console=False,  # Set to False for GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon='icon.ico' if you have an icon file
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
