# Whistleblower Build Guide

This guide explains how to build standalone executables and installers for Whistleblower on macOS and Windows.

## Prerequisites

### All Platforms

- Python 3.12 or higher
- pip (Python package manager)

### macOS (Prerequisites)

- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (recommended): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

### Windows (Prerequisites)

- Windows 10 or later
- Microsoft Visual C++ Redistributable (usually pre-installed)

## Quick Start

### macOS (Quick Start)

1. **Build the application:**

   ```bash
   chmod +x build-macos.sh
   ./build-macos.sh
   ```

2. **Create DMG installer (optional):**

   ```bash
   chmod +x create-dmg.sh
   ./create-dmg.sh
   ```

3. **Find your build:**

   - Application: `dist/Whistleblower.app`
   - DMG Installer: `dist/Whistleblower-macOS-v1.0.0.dmg`

> Tip: If you have not installed dependencies yet, see the macOS setup steps below
> (create `.venv312`, install `requirements.txt`, then `pyinstaller` and `Pillow`).

### Windows (Quick Start)

1. **Build the application:**

   ```cmd
   build-windows-exe.bat
   ```

2. **Create ZIP installer (optional):**

   ```cmd
   create-installer.bat
   ```

3. **Find your build:**

   - Application: `dist\Whistleblower\Whistleblower.exe`
   - ZIP Installer: `dist\Whistleblower-Windows-v1.0.0.zip`

## Detailed Build Process

### Setting Up Environment

#### macOS (Environment)

```bash
# Create virtual environment
python3 -m venv .venv312

# Activate it
source .venv312/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller Pillow
```

#### Windows (Environment)

```cmd
REM Create virtual environment
py -m venv .venv312

REM Activate it
.venv312\Scripts\activate

REM Install dependencies
pip install -r requirements.txt
pip install pyinstaller Pillow
```

### Manual Build Steps

If you prefer to build manually or need to customize:

1. **Generate icons:**

   ```bash
   cd assets
   python create_icon.py
   cd ..
   ```

2. **Build with PyInstaller:**

   ```bash
   pyinstaller whistleblower.spec --clean
   ```

3. **Test the build:**
   - macOS: `open dist/Whistleblower.app`
   - Windows: `dist\Whistleblower\Whistleblower.exe`

## Build Configuration

The build is configured in `whistleblower.spec`:

- **Entry point:** `tkinter_ui_refactored.py`
- **Icons:**
  - macOS: `assets/icon.icns`
  - Windows: `assets/icon.ico`
- **Bundle identifier:** `com.makeitworkok.whistleblower`
- **Version:** 1.0.0

### Customizing the Build

Edit `whistleblower.spec` to customize:

```python
# Change app name
name='YourAppName'

# Change version
version='2.0.0'

# Add more data files
datas = [
    ('your_folder', 'your_folder'),
]

# Add more Python modules
hiddenimports = [
    'your_module',
]
```

## Build Output Structure

### macOS (.app bundle)

```text
Whistleblower.app/
├── Contents/
│   ├── Info.plist          # App metadata
│   ├── MacOS/
│   │   └── Whistleblower   # Executable
│   └── Resources/          # Icons, data files
```

### macOS App Data Location

When running the packaged app, all writable data goes to:

- `~/Library/Application Support/Whistleblower/` (contains `sites/` templates and `data/` captures)

The app writes a launch log to:

- `~/whistleblower_launch.log`

### Windows (folder)

```text
Whistleblower/
├── Whistleblower.exe       # Main executable
├── _internal/              # Dependencies and libraries
├── sites/                  # Site configurations
├── docs/                   # Documentation
└── README.md
```

## Size Optimization

Current build sizes (approximate):

- macOS .app: ~150-200 MB
- Windows folder: ~180-230 MB

To reduce size further:

1. **Remove unused modules** in `whistleblower.spec`:

   ```python
   excludes=['module_name']
   ```

2. **Use UPX compression** (already enabled):

   ```python
   upx=True
   ```

3. **Strip debug symbols** (configure in spec):

   ```python
   strip=True
   ```

## Troubleshooting

### Build Fails with "Module not found"

Add missing module to `hiddenimports` in `whistleblower.spec`:

```python
hiddenimports = [
    # ... existing imports ...
    'missing_module',
]
```

### Application won't start

1. Check build logs: `build/whistleblower/warn-whistleblower.txt`
2. Test with console enabled:

   ```python
   console=True  # in whistleblower.spec
   ```

3. Rebuild: `pyinstaller whistleblower.spec --clean`

If the app quits immediately when launched from Finder, check:

- Launch log: `~/whistleblower_launch.log`
- App data dir: `~/Library/Application Support/Whistleblower/`

### "Developer cannot be verified" (macOS)

This is normal for unsigned apps. Users can:

1. Right-click the app
2. Select "Open"
3. Click "Open" in the dialog

For distribution, consider code signing:

```bash
codesign --force --deep --sign "Developer ID" Whistleblower.app
```

### Icons not showing

1. Ensure icons exist: `ls -la assets/icon.*`
2. Regenerate icons: `cd assets && python create_icon.py`
3. Rebuild: `pyinstaller whistleblower.spec --clean`

## Distribution

### macOS (Distribution)

#### Option 1: DMG Installer (Recommended)

- Run `./create-dmg.sh`
- Distribute: `dist/Whistleblower-macOS-v1.0.0.dmg`
- Users drag app to Applications folder

#### Option 2: ZIP Archive

```bash
cd dist
zip -r Whistleblower-macOS.zip Whistleblower.app
```

### Windows (Distribution)

#### Option 1: ZIP Archive (Recommended)

- Run `create-installer.bat`
- Distribute: `dist/Whistleblower-Windows-v1.0.0.zip`
- Users extract and run

#### Option 2: Installer (Advanced)

- Use Inno Setup or NSIS
- Create proper Windows installer with Start Menu shortcuts

## Code Signing (Optional)

### macOS (Code Signing)

1. Get Developer ID certificate from Apple
2. Sign the app:

   ```bash
   codesign --force --deep --sign "Developer ID Application: Your Name" \
       --options runtime \
       --entitlements entitlements.plist \
       Whistleblower.app
   ```

3. Notarize for Gatekeeper:

   ```bash
   xcrun notarytool submit Whistleblower.dmg \
       --apple-id your@email.com \
       --password app-specific-password \
       --team-id TEAM_ID
   ```


### Windows (Code Signing)

1. Get code signing certificate
2. Sign the executable:

   
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com Whistleblower.exe
   ```
   


## Automated Builds

### GitHub Actions (CI/CD)

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: ./build-macos.sh
      - run: ./create-dmg.sh
      - uses: actions/upload-artifact@v3
        with:
          name: Whistleblower-macOS
          path: dist/*.dmg

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: build-windows-exe.bat
      - run: create-installer.bat
      - uses: actions/upload-artifact@v3
        with:
          name: Whistleblower-Windows
          path: dist/*.zip
```

## Version Management

Update version in these files:

1. `whistleblower.spec` - `version='X.X.X'`
2. `build-macos.sh` - `VERSION="X.X.X"`
3. `build-windows-exe.bat` - `set VERSION=X.X.X`
4. `create-dmg.sh` - `VERSION="X.X.X"`
5. `create-installer.bat` - `set VERSION=X.X.X`

## Support

For build issues:

- Check logs in `build/whistleblower/`
- Review PyInstaller docs: <https://pyinstaller.org>
- Open an issue on GitHub

## License

Built executables include all dependencies and are subject to their respective licenses.
See LICENSE file for Whistleblower license.
