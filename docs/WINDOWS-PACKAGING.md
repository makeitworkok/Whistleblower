# Windows Executable Packaging Guide

This document describes how to build and package Whistleblower as a Windows executable for distribution.

## Prerequisites

- Python 3.12+
- PyInstaller
- Playwright and its dependencies
- Git

## Build Process

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Build the Executable

From the project root directory:

```bash
py -m PyInstaller whistleblower.spec
```

This will:
- Analyze all dependencies
- Package the application and its dependencies
- Create the executable in `dist/Whistleblower/`
- Include all necessary data files (sites/, docs/, scripts/)

Build time: ~2-5 minutes depending on your system.

### 3. Verify the Build

Check that these files exist:
- `dist/Whistleblower/Whistleblower.exe` - Main executable
- `dist/Whistleblower/_internal/` - Application data and libraries
- `dist/Whistleblower/README.txt` - User documentation
- `dist/Whistleblower/install-browsers.bat` - Browser installer
- `dist/Whistleblower/start-whistleblower.bat` - Launcher script

### 4. Test the Executable

Before distributing:

```batch
# Go to the dist folder
cd dist\Whistleblower

# Install browsers
install-browsers.bat

# Start the application  
start-whistleblower.bat
```

Verify:
- Application starts without errors
- Web UI opens at http://127.0.0.1:8787
- Bootstrap feature works
- Capture functionality works with a test site
- All UI features are accessible

## Creating the Distribution ZIP

### Option 1: Using PowerShell (Recommended)

```powershell
# From the project root
Compress-Archive -Path dist\Whistleblower\* -DestinationPath Whistleblower-Windows-v1.0.zip
```

### Option 2: Using 7-Zip

```batch
7z a -tzip Whistleblower-Windows-v1.0.zip .\dist\Whistleblower\*
```

### Option 3: Manual

Right-click `dist\Whistleblower` folder → Send to → Compressed (zipped) folder

## Distribution Checklist

Before releasing, verify the ZIP contains:

- [ ] `Whistleblower.exe`
- [ ] `README.txt` with installation instructions
- [ ] `install-browsers.bat` for first-time setup
- [ ] `start-whistleblower.bat` for easy launching
- [ ] `LICENSE` file
- [ ] `_internal/` folder with all dependencies
- [ ] `_internal/sites/` with all template files
- [ ] `_internal/docs/` with all documentation

## What Gets Included

### Python Scripts (as modules in _internal)
- `ui_app.py` - Main entry point
- `whistleblower.py` - Capture engine
- `bootstrap_recorder.py` - Bootstrap tool
- `analyze_capture.py` - Analysis tool

### Data Files (in _internal)
- `sites/*.json` - All configuration templates and examples
- `sites/README.md` - Site configuration guide
- `docs/*.md` - All documentation
- `scripts/*` - Utility scripts
- `README.md`, `LICENSE` - Project documentation

### Python Dependencies (automatically bundled)
- Playwright and its hooks
- Python standard library
- All runtime dependencies

### What's NOT Included
- Source `.py` files in root (they're compiled to .pyc)
- `data/` folder (created at runtime)
- `.git/` version control
- `build/` intermediate files
- `venv/` virtual environment
- `__pycache__/` cache files

## User Installation

Users simply:
1. Download the ZIP file
2. Extract to desired location (e.g., `C:\Whistleblower\`)
3. Run `install-browsers.bat` (first time only)
4. Run `start-whistleblower.bat` or double-click `Whistleblower.exe`

## Updating the PyInstaller Spec

The `whistleblower.spec` file controls what gets bundled. Edit it to:

### Add New Data Files

```python
datas=[
    ('new_folder/*.json', 'new_folder'),
],
```

### Add Hidden Imports

```python
hiddenimports=[
    'new_module',
],
```

### Change Executable Properties

```python
exe = EXE(
    name='Whistleblower',  # Executable name
    console=True,          # Show console window
    icon='icon.ico',       # Application icon
)
```

After editing, rebuild with:
```bash
py -m PyInstaller whistleblower.spec --clean
```

## Troubleshooting Build Issues

### Missing Modules
- Add to `hiddenimports` in the spec file
- Check PyInstaller warnings in build output

### Missing Data Files
- Add to `datas` list in the spec file
- Verify paths are correct (relative to project root)

### Large Executable Size
- Normal: 50-100 MB for Python + Playwright + dependencies
- To reduce: exclude unused modules in spec file
- Don't worry too much - convenience > size for this use case

### Playwright Not Working
- Ensure playwright hooks are included (check build log)
- Verify playwright browsers are installable after build
- Test `install-browsers.bat` functionality

## Version Management

When releasing a new version:

1. Update version number in relevant files
2. Rebuild: `py -m PyInstaller whistleblower.spec --clean`
3. Test thoroughly
4. Create ZIP with version in filename: `Whistleblower-Windows-v1.1.zip`
5. Tag in git: `git tag v1.1` and `git push origin v1.1`
6. Create GitHub release with the ZIP

## CI/CD Considerations (Future)

For automated builds:
- Use GitHub Actions with Windows runner
- Install Python 3.12+ and dependencies
- Run PyInstaller build
- Upload artifacts or create release
- Consider code signing certificate for the executable

Sample workflow pseudocode:
```yaml
- name: Build executable
  run: |
    pip install pyinstaller playwright
    py -m PyInstaller whistleblower.spec --clean
    
- name: Package for distribution
  run: |
    Compress-Archive -Path dist\Whistleblower\* -DestinationPath release.zip
```

## Security Notes

- The executable is **not code-signed** by default
  - Users may see Windows SmartScreen warnings
  - Consider purchasing code signing certificate for official releases
  
- Credentials in site configs are stored as **plain text**
  - Document this clearly for users
  - Recommend using read-only BAS accounts
  - Users should protect their config files appropriately

- No telemetry or phone-home in the executable
  - Completely offline capable except for:
    - Initial browser download
    - Accessing target BAS systems
    - Optional LLM analysis features

## Support

For build issues or questions:
- Check PyInstaller documentation: https://pyinstaller.org/
- Review Playwright packaging: https://playwright.dev/python/docs/library
- Open an issue on GitHub

---

Last updated: 2026-02-23
