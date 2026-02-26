# Whistleblower

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](#current-status)

> Read-only evidence capture for dashboards.

**Whistleblower** is a read-only watchdog for building automation systems (really any web-based control system).

It logs into whatever web interface you've got (any BAS vendor, PLC, SCADA, janky custom system—doesn't matter), navigates the graphics/dashboards, and grabs what the operator actually sees: screenshots, DOM text, element states.

The goal: catch when the pretty pictures lie about what's really happening in the building. No assumptions, no deep integrations—just evidence.

No write access.  
No drivers.  
No vendor SDKs.  
No cloud requirement for core capture.  
No subscriptions.  

Just local artifacts and receipts.

---

## ✅ What Whistleblower does (current MVP)

- Automates login to a BAS web UI using your provided credentials/selectors
- Navigates to your configured pages (dashboards, graphics, trends, etc.)
- Captures on each run:
  - Full-page screenshots
  - Visible DOM text + key element states (via CSS selectors you define)
- Stores timestamped artifacts locally for manual review or future comparison
- Includes optional post-capture analysis (`analyze_capture.py`) and a local desktop UI (`tkinter_ui_refactored.py`)

Intentionally **read-only** and **vendor-agnostic**. Works on whatever crap UI the system exposes via browser.

---

## 🚫 What it deliberately does NOT do

- ❌ Setpoint changes or control actions
- ❌ BACnet/Modbus/Lon protocol stacks
- ❌ Vendor SDKs, proprietary APIs, or deep integrations
- ❌ Automatic cloud telemetry or background phoning home
- ❌ Automatic alerting (yet—coming after reliable capture)

Optional analysis mode sends evidence to your chosen model provider only when you run it.

If the graphics are bullshitting you, Whistleblower just documents the bullshit. What you do next is on you.

---

## ⚠️ Read-only access disclaimer

Whistleblower is intended to be read-only. Configure the BAS account it uses with **read-only permissions** only. Do not grant write, override, or operator control rights. You are responsible for ensuring the credentials and access level are safe for a monitoring-only tool.

---

## 🧰 Requirements

### Windows Executable (Easiest)

**Don't want to install Python?** Download the Windows executable:

- No Python installation required
- Download, extract, and run
- Includes all dependencies bundled
- See the `windows-exe` branch for builds

### From Source

- Python 3.12+ (`whistleblower.py`, `tkinter_ui_refactored.py`, `bootstrap_recorder.py`, `analyze_capture.py`)
- Valid credentials for the BAS web interface you want to watch
- Internet for the initial dependency/browser install and only when using API-backed analysis providers

---

## 🏢 Supported BAS Vendors & Systems

Whistleblower includes **vendor-specific templates** to simplify setup. Each template includes:

- Pre-configured login selectors for that vendor
- Typical page paths and navigation patterns
- Documentation and examples

### Templates Registry

| Vendor | System | Template | Status | Notes |
| ------ | ------ | -------- | ------ | ----- |
| **Tridium** | Niagara (N4) | `niagara.template.json` | ✅ Tested | 2-step multi-page login, .px dashboards |
| **Trane** | Tracer Synchrony | `trane-tracer-synchrony.template.json` | ✅ Tested | /hui/* pages, hash routing |
| **Generic** | React/SPA (URL routing) | `react-url-based.template.json` | ✅ Tested | Hash-routed navigation |
| **Generic** | React/SPA (click nav) | `react-click-based.template.json` | ✅ Tested | Menu-based navigation |
| **Johnson Controls** | OpenBlue/Metasys | `johnson-controls.template.json` | 🔜 Planned | — |
| **Custom/Unknown** | Any | `example.json` or bootstrap_recorder | ✅ Tested | Use bootstrap_recorder to auto-discover |

**For detailed vendor info and setup instructions**, see [sites/README.md](sites/README.md) and [sites/templates-registry.json](sites/templates-registry.json).

---

## 🗂️ Repository layout

```text
Whistleblower/
├── requirements.txt
├── whistleblower.py          # Main capture runner (Playwright automation)
├── bootstrap_recorder.py     # Records operator flow, generates starter config + steps
├── analyze_capture.py        # Optional LLM analysis for captured runs
├── tkinter_ui_refactored.py  # Local desktop UI (bootstrap/capture/schedule/analysis)
├── ui_app.py                 # Legacy local web UI (Flask)
├── sites/
│   ├── README.md             # Template & config guide
│   ├── templates-registry.json # All vendor profiles
│   ├── niagara.template.json # Niagara/Tridium template
│   ├── trane-tracer-synchrony.template.json
│   ├── react-*.template.json # Generic SPA templates
│   └── example.json          # Starting point for custom systems
├── data/                     # Runtime output (screenshots, DOM, etc.)
│   └── .gitkeep
├── docs/
│   ├── ROADMAP.md
│   └── CHANGELOG.md
├── BUILD-GUIDE.md            # macOS + Windows build guide
├── README.md
└── LICENSE                   # MIT
```

- `sites/` -> per-site JSON configs (URLs, creds, login selectors, pages to hit)
- `data/` -> where the goods land (don't commit this)

---

## ⚡ Quick Start

### Option 1: Windows Executable (No Python Required)

1. Download the Whistleblower Windows package from the releases page
1. Extract the ZIP file to your desired location
1. Run `install-browsers.bat` (first time only - downloads Chromium)
1. Double-click `Whistleblower.exe`
1. Use the desktop UI to configure and run captures

See `dist/Whistleblower/README.txt` in the Windows build for full details.

### Option 2: From Source (Python Required)

1. Clone it

   ```bash
   git clone https://github.com/makeitworkok/Whistleblower.git
   cd Whistleblower
   ```

1. Make an output dir (if not already there)

   ```bash
   mkdir -p data
   ```

1. Install dependencies (first time only)

   ```bash
   python3 -m pip install -r requirements.txt
   python3 -m playwright install chromium
   ```

1. Set up your private config (never commit this!)

   **Option A: Use a vendor template** (if your system is in the registry)

   Check `sites/templates-registry.json` to find your BAS vendor:

   ```bash
   # For Niagara systems:
   cp sites/niagara.template.json sites/my-niagara-site.json

   # For Trane Tracer Synchrony:
   cp sites/trane-tracer-synchrony.template.json sites/my-trane-site.json

   # For custom/unknown systems:
   cp sites/example.json sites/my-site.json
   ```

   **Option B: Auto-discover selectors** (recommended for first-time setup)

   ```bash
   python3 bootstrap_recorder.py --url https://your-system.local --site-name my-site
   ```

   This launches an interactive browser where you log in manually. It discovers:

   - Login form selectors
   - Navigation paths
   - UI element states

   Output: `sites/my-site.bootstrap.json` (ready to test)

   Then edit `sites/my-site.json` with your real URL, username/password, login selectors, and pages/selectors.

   See [sites/README.md](sites/README.md) for detailed template documentation and examples.

1. Run it

   **Linux/macOS/Windows (PowerShell/CMD):**

   ```bash
   python3 whistleblower.py --config sites/my-site.json
   ```

   For macOS .app builds, see [BUILD-GUIDE.md](BUILD-GUIDE.md).

1. Optional (debug only): record the full interaction as video

   ```bash
   python3 whistleblower.py --config sites/my-site.json --record-video
   ```

   Video output is saved per run at:
   `data/<site_name>/<timestamp>/video/session.mp4`

   For normal scheduled/routine capture, leave `--record-video` off.

---

## 🧪 Testing Your Configuration

Before deploying, validate your configuration and test on your system:

```bash
# Quick validation of all site configs (no network required)
python3 test_configs.py

# Functional test on reachable systems (attempts actual login/capture)
python3 test_functional.py
```

Both scripts auto-discover all `sites/*.json` files and report results. Add new sites and re-run—tests update automatically.

👉 **[See docs/TESTING.md](docs/TESTING.md) for detailed testing guide and troubleshooting.**

---

## Multi-Step Login Support

Some BAS systems (like Niagara) require **login across multiple pages**:

```text
Step 1: /prelogin → Enter username → Submit
         ↓
Step 2: /login → Enter password → Submit
         ↓
Success → Dashboard
```

Whistleblower **automatically detects and handles** multi-step logins:

- Detects when only username field is visible
- Fills username, submits, waits for password page
- Detects when password field appears
- Fills password, submits, waits for authentication
- Works with both single-step and multi-step flows

**No special configuration needed** — the login function adapts based on what's visible.

If you have a system with unusual login flow (OAuth, MFA, etc.), use `bootstrap_recorder.py` to understand the flow, then adjust selectors in your config.

---

## Local Desktop UI (recommended for non-devs)

Run the local desktop UI to manage bootstrap recording, captures, schedules, and analysis.

Install local dependencies first:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

Then start the UI:

```bash
python3 tkinter_ui_refactored.py
```

What the UI provides:

- Bootstrap recorder (build a starter config and suggested steps)
- Main capture (run once)
- Scheduled capture (run every N minutes)
- Analysis (single combined analysis per run, or per-page)
- Time-range analysis (analyze runs between start/end UTC filters)

### Analysis API key

Analysis requires an API key. You can:

- Set `OPENAI_API_KEY` or `XAI_API_KEY` in your environment
- Paste it into the UI (saved to `~/.whistleblower_env`)
- Or place it in `.private/openai.env` (CLI-only)

---

## 📁 Output Example

After a successful run:

```text
data/
└── my-site/                  # From "site_name" in your config
    └── 20260210-161200/      # Timestamp of run
        ├── main_dashboard/
        │   ├── screenshot.png
        │   ├── dom.json       # Extracted text/elements
        │   └── meta.json      # Run info, selectors used, etc.
        └── ahu-graphics/
            ├── screenshot.png
            └── ...
```

Each run gets its own timestamped folder. Nothing gets overwritten.

---

## ⚙️ Configuration (sites/*.json)

Configs are per-site JSON files. Minimal example in `sites/example.json`.

Key fields you'll need:

- `name`: Friendly name for output folders
- `base_url`: Login/entry URL
- `login_attempts`: Retry count for login flows
- `viewport`: Browser viewport size (`width`/`height`)
- `login`: Credentials + selectors:
  - `username` / `password` (or env placeholders like `${MY_SITE_USERNAME}`)
  - `user_selector`, `pass_selector`, `submit_selector`, `success_selector`
- `watch`: Array of capture targets. Each target supports `name`, `url`, `root_selector`, `settle_ms`, `screenshot_full_page` or `screenshot_selector`, optional `pre_click_selector`, `pre_click_wait_ms`, `pre_click_steps`, and optional `prefer_url_on_pre_click_change` (default `true`).

**Working with ReactJS/SPAs:** Navigation selectors can be volatile in single-page applications.
See [docs/REACTJS-GUIDE.md](docs/REACTJS-GUIDE.md) for strategies on stable selectors, handling
loading states, and dealing with hash-based routing.

BAS UIs vary wildly—some need delays, some have iframes, some throw modals. Tweak selectors and add waits in code as needed for your target.

### Record steps with Playwright codegen

If the UI is JS-driven and hard to script from static URLs, record your click path and pull selectors:

```bash
npx playwright codegen https://your-bas-host.example.com/index.html --viewport-size 1920,1080
```

Useful variant (save script while recording):

```bash
npx playwright codegen https://your-bas-host.example.com/index.html --viewport-size 1920,1080 -o codegen-session.ts
```

Use the generated click selectors in your site config under `watch[].pre_click_steps`.

### Bootstrap a config by recording a real session

For first-time setup, use the standalone recorder to generate a starter config from your
actual login/navigation flow.

1. Run the recorder locally (headed browser):

   ```bash
   python3 bootstrap_recorder.py \
     --url "https://your-bas-host/login" \
     --site-name "my_site" \
     --ignore-https-errors \
     --record-video
   ```

2. In the opened browser, perform a normal read-only operator flow:
   - Login
   - Navigate to the graphics/pages you care about
   - Return to terminal and press Enter

3. Generated outputs:
   - `sites/my_site.bootstrap.json` (starter Whistleblower config)
   - `sites/my_site.steps.json` (suggested `pre_click_steps`)
   - `data/bootstrap/my_site/<timestamp>/` (raw events, screenshot, optional video)

4. Copy and finalize:
   - Copy `sites/my_site.bootstrap.json` to your real config (for example `sites/local.json`)
   - Export env vars for credentials and adjust selectors as needed
   - Move selected steps from `sites/my_site.steps.json` into `watch[].pre_click_steps`

   Generated bootstrap configs use environment placeholders by default:
   - `username`: `${MY_SITE_USERNAME}`
   - `password`: `${MY_SITE_PASSWORD}`

   Example run:

   ```bash
   export MY_SITE_USERNAME='your_user'
   export MY_SITE_PASSWORD='your_password'

   python3 whistleblower.py --config sites/my_site.local.json
   ```

---

## Current Status

Alpha, but beyond capture-only MVP.

Implemented and in active use:

- Read-only capture pipeline (`whistleblower.py`) with per-target artifacts
- Bootstrap flow recorder (`bootstrap_recorder.py`) for starter configs and click-step generation
- Local desktop UI (`tkinter_ui_refactored.py`) for bootstrap, one-off capture, scheduling, and analysis
- Post-capture LLM analysis (`analyze_capture.py`) with:
  - OpenAI or xAI/Grok providers
  - Combined run analysis or per-page analysis
  - Start/end UTC filtering for batch analysis

Current focus:

- Harden capture reliability across flaky/hash-routed BAS UIs
- Add deterministic diff artifacts between runs
- Layer deterministic rule checks on top of captures/diffs
- Continue Windows non-dev packaging track: `docs/windows-packaging-plan.md`

## 🚦 Alpha Exit Checklist

Mark this complete before cutting `v0.1.0-alpha`:

- [ ] Local setup succeeds on a clean machine (`pip install -r requirements.txt` and `playwright install chromium`).
- [ ] At least 2 representative site configs run successfully (default run, no video).
- [ ] Each run writes `screenshot.png`, `dom.json`, `meta.json` per target.
- [ ] `readiness_error` is `null` for baseline demo targets.
- [x] `bootstrap_recorder.py` generates `*.bootstrap.json` and `*.steps.json`.
- [x] `analyze_capture.py` emits `analysis.md`, `analysis.json`, and `analysis_summary.json`.
- [x] `tkinter_ui_refactored.py` supports bootstrap, one-off capture, scheduling, and analysis.
- [x] Private secrets are not committed (`sites/*.local.json`, `.private/*` ignored).
- [x] README quick start and config schema match real CLI behavior.

---

## 🧠 Analyze Captures with an Agent

After a Whistleblower run completes, you can ask an LLM to review each captured target
using both `screenshot.png` and `dom.json`.

Provider options:

- OpenAI (default): `--provider openai` (or omit `--provider`)
- xAI/Grok: `--provider xai` or `--provider grok`

1. Set API key:

   ```bash
   export OPENAI_API_KEY='your_api_key'
   ```

   For Grok/xAI instead:

   ```bash
   export XAI_API_KEY='your_xai_key'
   ```

   `GROK_API_KEY` is also accepted as a fallback.

   Optional (recommended): store once in a private file:

   ```bash
   cp .private/openai.env.example .private/openai.env
   # edit .private/openai.env and set OPENAI_API_KEY or XAI_API_KEY
   ```

   `analyze_capture.py` auto-loads `.private/openai.env`.

1. Analyze the latest run for a site (OpenAI default):

   ```bash
   python3 analyze_capture.py --site ignition_demo
   ```

1. Analyze the latest run for a site with Grok/xAI:

   ```bash
   python3 analyze_capture.py --provider grok --site ignition_demo
   ```

1. Analyze an explicit run directory:

   ```bash
   python3 analyze_capture.py --run-dir data/ignition_demo/20260212-174539
   ```

1. Analyze a UTC time window across runs (optionally scoped by `--site`):

   ```bash
   python3 analyze_capture.py \
     --site ignition_demo \
     --start-utc 2026-02-01T00:00:00Z \
     --end-utc 2026-02-19T23:59:59Z
   ```

1. Force per-page output instead of a combined run summary:

   ```bash
   python3 analyze_capture.py --site ignition_demo --per-page
   ```

Outputs are written next to each target:

- `analysis.md` (human-readable findings)
- `analysis.json` (structured metadata)

And one run-level file:

- `analysis_summary.json`

---

## Additional Documentation

### React/SPA Frontend Support

- **[docs/REACT-DOCS-MAP.md](docs/REACT-DOCS-MAP.md)** - START HERE - Navigation guide for React documentation
- **[docs/REACTJS-GUIDE.md](docs/REACTJS-GUIDE.md)** - Comprehensive guide for React, Vue, Angular, and SPA frontends
- **[docs/REACT-QUICK-REF.md](docs/REACT-QUICK-REF.md)** - Quick reference with copy-paste config patterns
- **[docs/REACT-TROUBLESHOOTING.md](docs/REACT-TROUBLESHOOTING.md)** - Step-by-step troubleshooting checklist
- **[sites/ignition_perspective_annotated.example.json](sites/ignition_perspective_annotated.example.json)** - Annotated real-world example

### Project Documentation

- **[docs/TESTING.md](docs/TESTING.md)** - Testing guide: how to run test_configs.py and test_functional.py, add tests for new sites
- **[docs/TEMPLATES.md](docs/TEMPLATES.md)** - Complete template system documentation and vendor support
- [sites/README.md](sites/README.md) - Site configuration quick-start and credential management
- [docs/ROADMAP.md](docs/ROADMAP.md) - Development roadmap and milestones
- [docs/CHANGELOG.md](docs/CHANGELOG.md) - Version history
- [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md) - Non-negotiable design constraints

---

## License

Whistleblower is released under the **MIT License**.

You are free to use, modify, and distribute this software for any purpose, including commercial use, without restriction. See [LICENSE](./LICENSE) for the full license text.

Contributions welcome.
