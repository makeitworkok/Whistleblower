# Windows Packaging Plan (Non-Dev End Users)

## Objective

Deliver a Windows-first app that non-technical users can run with:

1. Download
2. Double-click
3. Enter URL/credentials
4. Click `Start`
5. Review logs and artifacts

Core capture logic (`whistleblower.py`) remains the source of truth.

## Priority Rule

- Primary focus stays on capture reliability and artifact correctness.
- Packaging/UI work proceeds in small, isolated steps that do not destabilize core behavior.

## Phase 0: Prerequisites (Current Foundation)

Goal: Ensure CLI behavior is stable enough to wrap.

- Keep config schema stable (or version it when changed).
- Keep stdout/stderr messages actionable for GUI log display.
- Maintain deterministic output paths under `data/`.

Exit criteria:

- Repeatable successful runs on known demo/site configs.
- Clear error messaging for config/login/selector failures.

## Phase 1: Windows Packaging Smoke Test (CLI Only)

Goal: Package existing CLI on Windows with no logic changes.

Implementation:

- Build on Windows using PyInstaller `--onedir` first.
- Bundle Playwright dependencies with explicit collection flags.
- Set `PLAYWRIGHT_BROWSERS_PATH=0` during install/build flow.

Exit criteria:

- App runs on a clean Windows machine with no Python installed.
- `--config ...` execution works and writes artifacts correctly.

## Phase 2: Minimal GUI Wrapper

Goal: Hide terminal/config complexity for end users.

Implementation:

- Add `gui_runner.py` (Tkinter) with:
  - BAS URL input
  - Username/password input
  - Optional timeout/settle controls (simple defaults)
  - `Start` button
  - Live log text area
  - Link/button to open output folder
- GUI writes/uses a generated config file internally.
- GUI launches capture process and streams stdout/stderr.

Exit criteria:

- Non-technical user can complete a run without touching terminal.
- Common failure states are visible in GUI (bad creds, selector timeout, etc.).

## Phase 3: Installer and User Experience Hardening

Goal: Make distribution and first-run behavior predictable.

Implementation:

- Choose distribution format:
  - Simple zip (`--onedir`) first
  - Installer (Inno Setup/NSIS) second
- Add version metadata and app icon.
- Add first-run checks (writable output folder, required files present).

Exit criteria:

- Fresh machine install/unzip works without manual dependency steps.
- User can recover from expected setup issues with clear prompts.

## Phase 4: Trust and Operations Readiness

Goal: Reduce friction from Windows security/reputation systems.

Implementation:

- Document SmartScreen/AV expectations.
- Add code signing when budget/process allows.
- Publish checksums and release notes.

Exit criteria:

- Internal pilot users can install/run with minimal support.
- Release process is documented and repeatable.

## Known Gotchas to Track

- Playwright browser/runtime bundling in packaged app.
- Path handling (`cwd`, temp dirs, spaces in paths, permissions).
- Credential handling in GUI-generated config artifacts.
- Antivirus false positives on unsigned executables.
- Differences between dev environment and clean target machines.

## Suggested Execution Cadence

1. Keep core reliability work as default stream.
2. Time-box packaging/UI work in short branches.
3. Merge only when each phase exit criteria is met.
