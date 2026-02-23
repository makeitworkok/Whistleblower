# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Whistleblower Windows executable."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

block_cipher = None

# Collect all Python scripts
a = Analysis(
    ['ui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include all site configuration files
        ('sites/*.json', 'sites'),
        ('sites/*.md', 'sites'),
        # Include documentation
        ('docs/*.md', 'docs'),
        # Include scripts
        ('scripts/*', 'scripts'),
        # Include README and other root docs
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('requirements.txt', '.'),
        # Include Python modules that are called as subprocesses
        ('whistleblower.py', '.'),
        ('bootstrap_recorder.py', '.'),
        ('analyze_capture.py', '.'),
        ('codegen-session.py', '.'),
    ],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=True,  # Keep console window for logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

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
