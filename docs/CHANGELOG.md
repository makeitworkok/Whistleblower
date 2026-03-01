# Changelog

## [1.0.2] - 2026-03-01

### Added
- Security-focused test coverage:
  - `test_core_security.py`
  - `test_ui_app_security.py`
  - `test_tkinter_ui.py`
- App version constant and display updates for `1.0.2` in Tkinter UI.

### Changed
- `bootstrap_recorder.py` now redacts password values in event logs and stores `${WHISTLEBLOWER_PASSWORD}` placeholder instead of clear-text passwords.
- `ui_app.py` now applies stricter input validation for URL, site name, viewport bounds, and path normalization.
- `tkinter_ui_refactored.py` now prompts for bootstrap password when needed and injects it via environment variable before capture.
- Windows/macOS build metadata updated to `1.0.2` in packaging files (`create-installer.bat`, `whistleblower.spec`).

## [Unreleased] - 2026-02-19

### Added
- Comprehensive ReactJS/SPA guide (`docs/REACTJS-GUIDE.md`) covering:
  - Stable selector strategies for dynamic React apps
  - Handling loading states and async rendering
  - Hash-based routing solutions
  - Multi-step navigation patterns
  - Framework-specific examples (MUI, Ant Design, Ignition Perspective)
- Quick reference card (`docs/REACT-QUICK-REF.md`) with copy-paste config snippets
- React/SPA troubleshooting guide (`docs/REACT-TROUBLESHOOTING.md`) with step-by-step diagnostics
- Documentation navigation map (`docs/REACT-DOCS-MAP.md`) linking all React resources
- **Practical templates** validated through testing on Ignition Perspective demos:
  - `sites/react-url-based.template.json` - For hash routing navigation (easiest, most reliable)
  - `sites/react-click-based.template.json` - For click-based navigation (includes XPath fallback strategies)
  - `sites/ignition_perspective_annotated.example.json` - Detailed Ignition-specific example
- Documentation section in README linking to all guides

## [UI] - 2026-02-18

### Added
- Local UI run instructions and API key guidance.
- Combined analysis support for multi-page runs.
- Time range selection for analysis runs.
- UI application entry point.

### Changed
- Site config ignore rules to allow example files only.

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->

