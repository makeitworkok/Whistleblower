# Whistleblower Tkinter UI - Build & Distribution Guide

This guide covers the Tkinter desktop UI version of Whistleblower, designed for easy distribution as a Windows executable.

## Overview

The Tkinter UI (`tkinter_ui.py`) provides a native desktop interface that:

- Eliminates the need for subprocess calls (direct function imports)
- Works better with PyInstaller for creating executables
- Supports browser selection (Chromium/Edge, Firefox, WebKit)
- Provides real-time logging output
- Runs entirely offline with no web server

## Running the Tkinter UI

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Launch the UI

```bash
python tkinter_ui.py
```

## Building Windows Executable

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Build the Executable

```bash
pyinstaller whistleblower.spec
```

This creates:

- `dist/Whistleblower/` folder with the executable and dependencies
- `dist/Whistleblower/Whistleblower.exe` - the main executable

### 3. Install Playwright Browsers in Distribution

After building, install Playwright browsers for the bundled distribution:

```bash
cd dist/Whistleblower
# Set PLAYWRIGHT_BROWSERS_PATH to current directory
set PLAYWRIGHT_BROWSERS_PATH=%CD%\playwright_browsers
playwright install chromium
playwright install firefox
```

Or for end users, provide a batch file (`install_browsers.bat`):

```batch
@echo off
echo Installing browsers for Whistleblower...
set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers
playwright install chromium
playwright install firefox
echo Done! You can now run Whistleblower.exe
pause
```

## Architecture Changes

### Before (Flask UI + Subprocess)

```text
Flask Web Server
  └─> HTTP Endpoint
       └─> subprocess.Popen (python bootstrap_recorder.py)
            └─> Selenium Browser Automation
```

**Problem**: PyInstaller bundles break subprocess calls to Python scripts.

### After (Tkinter UI + Direct Import)

```text
Tkinter Desktop UI
  └─> threading.Thread
       └─> Direct function call (bootstrap_recorder.run_bootstrap())
            └─> Playwright Browser Automation
```

**Solution**: Direct function imports work perfectly in PyInstaller bundles.

## Key Refactoring

### bootstrap_recorder.py

- Added `run_bootstrap()` function - accepts parameters directly
- Kept `main()` for CLI compatibility
- No subprocess needed

### whistleblower.py

- Added `run_capture()` function - accepts parameters directly  
- Kept `main()` for CLI compatibility
- No subprocess needed

### tkinter_ui.py

- New desktop UI using Tkinter
- Imports modules directly: `import bootstrap_recorder, whistleblower`
- Runs operations in threads to keep UI responsive
- Real-time log output via queue

## Browser Support

The UI supports selecting between:

- **Chromium** (default) - includes Edge on Windows (usually pre-installed)
- **Firefox** - requires Firefox installation
- **WebKit** - Safari engine (primarily for testing)

On Windows, Edge (Chromium) is selected automatically if available.

## Distribution Checklist

When distributing to Windows users:

1. ✅ Build with `pyinstaller whistleblower.spec`
2. ✅ Bundle `sites/` folder with example configs
3. ✅ Include Playwright browser binaries (or install script)
4. ✅ Test on clean Windows machine (no Python installed)
5. ✅ Provide user documentation for:
   - Running Whistleblower.exe
   - Installing browsers (if needed)
   - Creating site configs

## Troubleshooting

### "ModuleNotFoundError" when running executable

- Playwright or dependencies not bundled correctly
- Solution: Add missing modules to `hiddenimports` in `.spec` file

### "Browser not found" error

- Playwright browsers not installed for the distribution
- Solution: Run `playwright install chromium` in dist folder

### Executable opens console window

- `console=True` in `.spec` file
- Solution: Change to `console=False` for GUI-only app

### Slow startup time

- Large bundle size due to excluded packages not being excluded
- Solution: Review `excludes` list in `.spec` file

## File Size Optimization

The spec file excludes unnecessary packages:

- matplotlib
- numpy/pandas
- PyQt/PySide
- wx

This reduces the bundle size significantly while keeping all necessary functionality.

## Future Enhancements

- [ ] Add application icon (.ico file)
- [ ] Create MSI installer with WiX
- [ ] Auto-detect installed browsers
- [ ] Progress indicators during long operations
- [ ] Schedule tab for automated captures
- [ ] Built-in config editor

## License

Copyright (c) 2025-2026 Chris Favre - MIT License
