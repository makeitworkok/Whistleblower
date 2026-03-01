# Whistleblower v1.0.0 - Cross-Platform Release

## 🎉 First Official Release!

This is the first distributable release of Whistleblower—a read-only evidence capture tool for building automation systems and web-based control interfaces. Now available for **Windows** and **macOS**!

## 📦 What's New

### Cross-Platform Desktop Applications
- **Windows and macOS support** - No Python installation required!
- **Complete bundled dependencies** - Playwright, Tkinter, and all libraries included
- **Portable** - Extract and run from anywhere
- **Native applications** - .exe for Windows, .app for macOS

### Features
- ✅ **Automated login** to BAS/SCADA web interfaces
- ✅ **Screenshot capture** of dashboards and graphics
- ✅ **DOM text extraction** with configurable selectors
- ✅ **Vendor templates** included (Niagara, Meatball Tracers, React/SPA)
- ✅ **Bootstrap recorder** for auto-discovering site configurations
- ✅ **Tkinter GUI** for easy configuration and operation
- ✅ **Optional AI analysis** with capture comparison

## 🚀 Quick Start

### For Windows Users (No Python)
1. Download `Whistleblower-Windows-Installer.zip` (below)
2. Extract the ZIP file
3. Navigate to the `Whistleblower` folder
4. Double-click `Whistleblower.exe`

### For macOS Users (No Python)
1. Download `Whistleblower-macOS-v1.0.0.dmg` (below)
2. Open the DMG file
3. Drag `Whistleblower.app` to Applications
4. Launch from Applications

### ⚠️ Important: Running Unsigned Applications
This is an **educational/open-source project** and the applications are **not code-signed**.

**Windows** - When Windows shows "Windows protected your PC":
1. Click **"More info"**
2. Click **"Run anyway"**

**macOS** - When you see "cannot be opened because the developer cannot be verified":
1. Right-click (or Control-click) the app
2. Select **"Open"**
3. Click **"Open"** in the dialog

The application is safe and read-only. All source code is available in this repository for review.

### For Developers
Clone the repository and run from source:
```bash
git clone https://github.com/makeitworkok/Whistleblower.git
cd Whistleblower
pip install -r requirements.txt
python tkinter_ui_refactored.py
```

## 📋 System Requirements

### Windows
- **OS**: Windows 10 or Windows 11
- **Disk Space**: 100 MB
- **Internet**: Required for browser automation (Playwright downloads browsers on first run)

### macOS  
- **OS**: macOS 10.15 (Catalina) or later
- **Disk Space**: 150 MB
- **Internet**: Required for browser automation (Playwright downloads browsers on first run)

**No Python required** for either platform!

## 🔧 What's Included

### Windows Package (`Whistleblower-Windows-Installer.zip` - 47 MB)
- `Whistleblower.exe` - Main application (3.44 MB)
- `_internal/` - Bundled dependencies and runtime

### macOS Package (`Whistleblower-macOS-v1.0.0.dmg` - ~50 MB)
- `Whistleblower.app` - Native macOS application bundle
- All dependencies included in the app bundle

### Vendor Templates
Pre-configured templates for:
- Tridium Niagara N4
- Meatball Tracers
- Generic React/SPA applications

### Documentation
- Complete README with setup guides
- Vendor-specific template documentation
- Bootstrap recorder guide

## 🐛 Known Issues

- First launch may take 15-30 seconds as Playwright initializes browsers
- Security warnings expected on both platforms (unsigned applications)
- Some antivirus software may flag executables (false positive)
- macOS may show "damaged" error if downloaded via certain browsers (use the workaround below)

## 🆘 Troubleshooting

### Windows

**Application won't start?**
- Check Windows Defender hasn't quarantined the file
- Right-click the .exe → Properties → "Unblock" if present
- Try running as Administrator

**Browsers won't launch?**
- Ensure internet connectivity
- Playwright downloads browsers on first run (~300 MB)
- Check firewall isn't blocking the application

### macOS

**"Whistleblower.app is damaged and can't be opened"?**
Run this command in Terminal:
```bash
xattr -cr /Applications/Whistleblower.app
```

**Application won't open?**
- Right-click → Open (first time only)
- Check System Preferences → Security & Privacy → Allow anyway
- Make sure you're on macOS 10.15 or later

**Browsers won't launch?**
- Ensure internet connectivity
- Playwright downloads browsers on first run (~300 MB)
- Check if any security software is blocking browser downloads

## 📖 Documentation

- [Main README](https://github.com/makeitworkok/Whistleblower/blob/main/README.md)
- [Vendor Templates Guide](https://github.com/makeitworkok/Whistleblower/blob/main/sites/README.md)
- [CLI Documentation](https://github.com/makeitworkok/Whistleblower/blob/main/docs/CLI-GUIDE.md)

## 🙏 Acknowledgments

Built with:
- Python 3.12
- Playwright (browser automation)
- Tkinter (GUI)
- PyInstaller (Windows packaging)

## 📝 License

MIT License - See [LICENSE](https://github.com/makeitworkok/Whistleblower/blob/main/LICENSE) for details

---

**Download the Windows installer below and start capturing evidence from your BAS today!**

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->
