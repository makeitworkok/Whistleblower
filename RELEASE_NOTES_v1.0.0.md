# Whistleblower v1.0.0 - Windows Release

## 🎉 First Official Release!

This is the first distributable Windows release of Whistleblower—a read-only evidence capture tool for building automation systems and web-based control interfaces.

## 📦 What's New

### Windows Executable Distribution
- **Standalone Windows application** - No Python installation required!
- **Complete bundled dependencies** - Playwright, Tkinter, and all libraries included
- **Portable** - Extract and run from anywhere
- **Size**: 47 MB (complete package)

### Features
- ✅ **Automated login** to BAS/SCADA web interfaces
- ✅ **Screenshot capture** of dashboards and graphics
- ✅ **DOM text extraction** with configurable selectors
- ✅ **Vendor templates** included (Niagara, Trane Tracer, React/SPA)
- ✅ **Bootstrap recorder** for auto-discovering site configurations
- ✅ **Tkinter GUI** for easy configuration and operation
- ✅ **Optional AI analysis** with capture comparison

## 🚀 Quick Start

### For Windows Users (No Python)
1. Download `Whistleblower-Windows-Installer.zip` (below)
2. Extract the ZIP file
3. Navigate to the `Whistleblower` folder
4. Double-click `Whistleblower.exe`

### ⚠️ Important: Running Unsigned Executables
This is an **educational/open-source project** and the executable is **not code-signed**.

**When Windows shows "Windows protected your PC":**
1. Click **"More info"**
2. Click **"Run anyway"**

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

- **OS**: Windows 10 or Windows 11
- **Disk Space**: 100 MB
- **Internet**: Required for browser automation (Playwright downloads browsers on first run)
- **No Python required** for executable version

## 🔧 What's Included

### Application Files
- `Whistleblower.exe` - Main application (3.44 MB)
- `_internal/` - Bundled dependencies and runtime

### Vendor Templates
Pre-configured templates for:
- Tridium Niagara N4
- Trane Tracer Synchrony
- Generic React/SPA applications

### Documentation
- Complete README with setup guides
- Vendor-specific template documentation
- Bootstrap recorder guide

## 🐛 Known Issues

- First launch may take 15-30 seconds as Playwright initializes browsers
- Windows Defender/SmartScreen warnings expected (unsigned executable)
- Some antivirus software may flag the executable (false positive)

## 🆘 Troubleshooting

**Application won't start?**
- Check Windows Defender hasn't quarantined the file
- Right-click the .exe → Properties → "Unblock" if present
- Try running as Administrator

**Browsers won't launch?**
- Ensure internet connectivity
- Playwright downloads browsers on first run (~300 MB)
- Check firewall isn't blocking the application

## 📖 Documentation

- [Main README](https://github.com/makeitworkok/Whistleblower/blob/main/README.md)
- [Vendor Templates Guide](https://github.com/makeitworkok/Whistleblower/blob/main/sites/README.md)
- [CLI Documentation](https://github.com/makeitworkok/Whistleblower/blob/main/docs/CLI-GUIDE.md)

## 🙏 Acknowledgments

Built with:
- Python 3.11
- Playwright (browser automation)
- Tkinter (GUI)
- PyInstaller (Windows packaging)

## 📝 License

MIT License - See [LICENSE](https://github.com/makeitworkok/Whistleblower/blob/main/LICENSE) for details

---

**Download the Windows installer below and start capturing evidence from your BAS today!**
