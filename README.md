# Whistleblower

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](#-current-status)

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
- Includes optional post-capture analysis (`analyze_capture.py`) and a local control UI (`ui_app.py`)

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

- Python 3.11+ (`whistleblower.py`, `ui_app.py`, `bootstrap_recorder.py`, `analyze_capture.py`)
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
├── ui_app.py                 # Local web UI (bootstrap/capture/schedule/analysis)
├── sites/
│   ├── README.md             # 📖 Template & config guide
│   ├── templates-registry.json # 📋 All vendor profiles
│   ├── niagara.template.json # Niagara/Tridium template
│   ├── trane-tracer-synchrony.template.json
│   ├── react-*.template.json # Generic SPA templates
│   └── example.json          # Starting point for custom systems
├── data/                     # Runtime output (screenshots, DOM, etc.)
│   └── .gitkeep
├── docs/
│   ├── ROADMAP.md
│   └── CHANGELOG.md
├── README.md
└── LICENSE                   # MIT
```

- `sites/` → per-site JSON configs (URLs, creds, login selectors, pages to hit)
- `data/` → where the goods land (don't commit this)

---

## ⚡ Quick Start

### UI-Based Setup (Recommended)

1. **Clone and install**

   ```bash
   git clone https://github.com/makeitworkok/Whistleblower.git
   cd Whistleblower
   python3 -m pip install -r requirements.txt
   python3 -m playwright install chromium
   ```

2. **Start the local web UI**

   ```bash
   python3 ui_app.py
   ```

   Open in browser: `http://127.0.0.1:8787`

3. **Bootstrap your first site**

   - Navigate to the **Bootstrap** tab
   - Enter your BAS system URL and a site name
   - Click "Start Bootstrap Recording"
   - Log in and navigate through your system
   - Click "Stop Recording" when done

   The recorder will generate a starter config with discovered selectors automatically.

4. **Run your first capture**

   - Navigate to the **Capture** tab
   - Select your site config
   - Click "Run Capture"
   - View screenshots and data in the output directory

5. **Optional: Set up scheduled captures**

   - Navigate to the **Schedule** tab
   - Configure capture interval (e.g., every 15 minutes)
   - Enable scheduling

6. **Optional: Run analysis**

   - Navigate to the **Analysis** tab
   - Add your API key (OpenAI or xAI/Grok)
   - Select a run and click "Analyze"

### CLI-Based Setup (Advanced)

For automation, scripting, and headless deployments, use the command-line tools:

```bash
# Bootstrap a config
python3 bootstrap_recorder.py --url https://your-system.local --site-name my-site

# Run a capture
python3 whistleblower.py --config sites/my-site.json

# Analyze results
python3 analyze_capture.py --site my-site
```

📖 **[See docs/CLI-GUIDE.md](docs/CLI-GUIDE.md) for complete CLI reference and advanced usage.**

---

## 🧪 Testing Your Configuration

Before deploying, validate your configuration:

**Using the UI:**

- Navigate to the **Test** tab
- Select config and click "Validate"

**Using CLI:**

```bash
# Quick validation (no network required)
python3 test_configs.py

# Functional test (attempts actual login/capture)
python3 test_functional.py
```

👉 **[See docs/TESTING.md](docs/TESTING.md) for detailed testing guide and troubleshooting.**

---

## 🔐 Multi-Step Login Support

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

## 🖥️ Local Web UI

The web UI provides a complete interface for all Whistleblower operations:

```bash
python3 ui_app.py
# Open http://127.0.0.1:8787
```

### Features

- **Bootstrap Tab**: Record operator flows to auto-generate configs
- **Capture Tab**: Run one-off captures with live progress
- **Schedule Tab**: Configure recurring captures (e.g., every 15 minutes)
- **Analysis Tab**: Run LLM analysis on captured data
  - Single run or time-range analysis
  - OpenAI or xAI/Grok providers
  - Combined or per-page output
- **Test Tab**: Validate configs before deployment

### API Keys for Analysis

You can provide API keys in three ways:

1. **In the UI**: Paste directly into the Analysis tab
2. **Environment variable**: `OPENAI_API_KEY` or `XAI_API_KEY`
3. **Private file**: `.private/openai.env` (recommended)

   ```bash
   cp .private/openai.env.example .private/openai.env
   # Edit and set your key
   ```

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

Configs are per-site JSON files stored in `sites/`. See `sites/example.json` for a minimal template.

### Key Configuration Fields

- `name`: Friendly name for output folders
- `base_url`: Login/entry URL
- `login_attempts`: Retry count for login flows
- `viewport`: Browser viewport size (`width`/`height`)
- `login`: Credentials + selectors:
  - `username` / `password` (or env placeholders like `${MY_SITE_USERNAME}`)
  - `user_selector`, `pass_selector`, `submit_selector`, `success_selector`
- `watch`: Array of capture targets. Each target supports:
  - `name`, `url`, `root_selector`
  - `settle_ms`
  - `screenshot_full_page` or `screenshot_selector`
  - optional `pre_click_selector`, `pre_click_wait_ms`, `pre_click_steps`
  - optional `prefer_url_on_pre_click_change` (default `true`)

### Creating Configs

#### Recommended: Use the Bootstrap Recorder

The bootstrap recorder automatically discovers selectors by observing your actual login/navigation flow:

- **Via UI**: Bootstrap tab in the web UI (`ui_app.py`)
- **Via CLI**: `python3 bootstrap_recorder.py --url https://... --site-name my_site`

#### Alternative: Use a Vendor Template

Check `sites/templates-registry.json` for pre-configured templates:

```bash
# For Niagara systems:
cp sites/niagara.template.json sites/my-niagara-site.json

# For Trane Tracer Synchrony:
cp sites/trane-tracer-synchrony.template.json sites/my-trane-site.json
```

**For ReactJS/SPA systems**: Navigation selectors can be volatile. See [docs/REACTJS-GUIDE.md](docs/REACTJS-GUIDE.md) for strategies on stable selectors, handling loading states, and hash-based routing.

📖 **[See sites/README.md](sites/README.md) for complete configuration guide**

📖 **[See docs/CLI-GUIDE.md](docs/CLI-GUIDE.md) for bootstrap recorder CLI usage and Playwright codegen**

---

## 🧪 Current Status

Alpha, but beyond capture-only MVP.

Implemented and in active use:

- Read-only capture pipeline (`whistleblower.py`) with per-target artifacts
- Bootstrap flow recorder (`bootstrap_recorder.py`) for starter configs and click-step generation
- Local operations UI (`ui_app.py`) for bootstrap, one-off capture, scheduling, and analysis
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
- [x] `ui_app.py` supports bootstrap, one-off capture, scheduling, and analysis.
- [x] Private secrets are not committed (`sites/*.local.json`, `.private/*` ignored).
- [x] README quick start and config schema match real CLI behavior.

---

## 🧠 Capture Analysis

Whistleblower can analyze captured screenshots and DOM data using LLMs (OpenAI or xAI/Grok).

### Using the Web UI

1. Navigate to the **Analysis** tab
2. Add your API key (or use environment variable/private file)
3. Select a run or time range
4. Click **Analyze**

### Using the CLI

```bash
# Analyze latest run
python3 analyze_capture.py --site my-site

# Analyze with Grok
python3 analyze_capture.py --provider grok --site my-site

# Analyze time range
python3 analyze_capture.py \
  --site my-site \
  --start-utc 2026-02-01T00:00:00Z \
  --end-utc 2026-02-19T23:59:59Z
```

### Analysis Outputs

Generated per target:

- `analysis.md` - Human-readable findings
- `analysis.json` - Structured metadata

Run-level summary:

- `analysis_summary.json` - Overview across all targets

📖 **[See docs/CLI-GUIDE.md](docs/CLI-GUIDE.md) for complete analysis CLI reference**

---

## 📚 Additional Documentation

### React/SPA Frontend Support

- **[docs/REACT-DOCS-MAP.md](docs/REACT-DOCS-MAP.md)** - 🗺️ **START HERE** - Navigation guide for React documentation
- **[docs/REACTJS-GUIDE.md](docs/REACTJS-GUIDE.md)** - Comprehensive guide for React, Vue, Angular, and SPA frontends
- **[docs/REACT-QUICK-REF.md](docs/REACT-QUICK-REF.md)** - Quick reference with copy-paste config patterns
- **[docs/REACT-TROUBLESHOOTING.md](docs/REACT-TROUBLESHOOTING.md)** - Step-by-step troubleshooting checklist
- **[sites/ignition_perspective_annotated.example.json](sites/ignition_perspective_annotated.example.json)** - Annotated real-world example

### Project Documentation

- **[docs/CLI-GUIDE.md](docs/CLI-GUIDE.md)** - Complete CLI reference for automation and scripting
- **[docs/TESTING.md](docs/TESTING.md)** - Testing guide: how to run test_configs.py and test_functional.py, add tests for new sites
- **[docs/TEMPLATES.md](docs/TEMPLATES.md)** - Complete template system documentation and vendor support
- [sites/README.md](sites/README.md) - Site configuration quick-start and credential management
- [docs/ROADMAP.md](docs/ROADMAP.md) - Development roadmap and milestones
- [docs/CHANGELOG.md](docs/CHANGELOG.md) - Version history
- [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md) - Non-negotiable design constraints

---

## 📜 License

Whistleblower is released under the **MIT License**.

You are free to use, modify, and distribute this software for any purpose, including commercial use, without restriction. See [LICENSE](./LICENSE) for the full license text.

Contributions welcome.

---

## 🤝 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.
