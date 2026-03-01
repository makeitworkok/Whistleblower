# Whistleblower v1.0.2 - Security Hardening Release

## 🔐 Release Focus

v1.0.2 is a security-focused update that improves credential handling, input validation, and packaging/version consistency across Windows and macOS builds.

## ✨ Highlights

### Security Improvements
- **Bootstrap password protection** in `bootstrap_recorder.py`
  - Redacts passwords in captured event logs
  - Stores `${WHISTLEBLOWER_PASSWORD}` placeholder instead of clear-text credentials
- **UI input validation hardening** in `ui_app.py`
  - URL validation
  - Site name validation
  - Viewport bounds validation
  - Relative path normalization for safer file handling
- **Tkinter credential flow update** in `tkinter_ui_refactored.py`
  - Prompts for password after bootstrap when needed
  - Injects password through environment variable before capture runs

### Versioning and Build Metadata
- Added `__version__ = "1.0.2"` in `tkinter_ui_refactored.py`
- Updated UI title/label to display version information
- Updated build/package version references:
  - `whistleblower.spec` (bundle version)
  - `create-installer.bat` (Windows ZIP version)

### Testing Additions
- Added `test_core_security.py`
  - Covers password redaction, placeholder usage, env var resolution
- Added `test_ui_app_security.py`
  - Covers input validation behavior in UI app
- Added `test_tkinter_ui.py`
  - Covers module import and env variable handling paths

## 📦 Windows Distribution

The Windows package for this release includes:
- `Whistleblower.exe`
- `install-browsers.bat`
- `Start-Whistleblower.bat`
- `README.md`
- `LICENSE`
- `_internal/` runtime dependencies

## ⬆️ Upgrade Notes

- Existing site configs that still contain clear-text passwords should be updated to use `${WHISTLEBLOWER_PASSWORD}` where applicable.
- Browser installation remains a first-run requirement for packaged Windows use (`install-browsers.bat`).

## 🙏 Thanks

Thanks to everyone testing packaged builds and validating security edge cases.

---

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->
