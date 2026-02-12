# Whistleblower

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-0db7ed.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)](#current-status)

> Read-only evidence capture for BAS dashboards.

**Whistleblower** is a read-only watchdog for building automation systems.

It logs into whatever BAS web interface you've got (Niagara, Metasys, Tracer, Honeywell, Siemens, Distech, janky custom shit—doesn't matter), navigates the graphics/dashboards, and grabs what the operator actually sees: screenshots, DOM text, element states.

The goal: catch when the pretty pictures lie about what's really happening in the building. No assumptions, no deep integrations—just evidence.

No write access.  
No drivers.  
No vendor SDKs.  
No cloud.  
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

Intentionally **read-only** and **vendor-agnostic**. Works on whatever crap UI the system exposes via browser.

---

## 🚫 What it deliberately does NOT do

- ❌ Setpoint changes or control actions
- ❌ BACnet/Modbus/Lon protocol stacks
- ❌ Niagara SDKs, vendor APIs, or deep integrations
- ❌ Cloud uploads, telemetry, or phoning home
- ❌ Automatic alerting (yet—coming after reliable capture)

If the graphics are bullshitting you, Whistleblower just documents the bullshit. What you do next is on you.

---

## 🧰 Requirements

- Docker (Linux/macOS/Windows)
- Valid credentials for the BAS web interface you want to watch
- Internet only for the initial Docker build (pulls Python + Playwright deps)

That's literally it.

---

## 🗂️ Repository layout

```
Whistleblower/
├── Dockerfile
├── requirements.txt
├── whistleblower.py          # The main script (Playwright automation)
├── sites/
│   └── example.json          # Template—copy & edit for your site
├── data/                     # Runtime output (screenshots, DOM, etc.)
│   └── .gitkeep
├── README.md
└── LICENSE                   # MIT
```

- `sites/` → per-site JSON configs (URLs, creds, login selectors, pages to hit)
- `data/` → where the goods land (don't commit this)

---

## ⚡ Quick Start

1. Clone it

   ```bash
   git clone https://github.com/makeitworkok/Whistleblower.git
   cd Whistleblower
   ```

2. Make an output dir (if not already there)

   ```bash
   mkdir -p data
   ```

3. Build the image (first time takes a bit—downloads browser binaries)

   ```bash
   docker build -t whistleblower .
   ```

4. Set up your private config (never commit this!)

   ```bash
   cp sites/example.json sites/my-site.json
   ```

   Edit `sites/my-site.json` with your real URL, username/password, login selectors, and pages/selectors. (See example.json comments for format.)

5. Run it

   **Linux/macOS:**

   ```bash
   docker run --rm \
     -v "$(pwd)/sites:/app/sites" \
     -v "$(pwd)/data:/app/data" \
     whistleblower --config /app/sites/my-site.json
   ```

   **Windows (PowerShell):**

   ```powershell
   docker run --rm `
     -v "${PWD}\sites:/app/sites" `
     -v "${PWD}\data:/app/data" `
     whistleblower --config /app/sites/my-site.json
   ```

6. Optional: record the full interaction as video

   ```bash
   docker run --rm \
     -v "$(pwd)/sites:/app/sites" \
     -v "$(pwd)/data:/app/data" \
     whistleblower --config /app/sites/my-site.json --record-video
   ```

   Video output is saved per run at:
   `data/<site_name>/<timestamp>/video/session.mp4`

---

## 📁 Output Example

After a successful run:

```
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
- `watch`: Array of capture targets. Each target supports:
  - `name`, `url`, `root_selector`
  - `settle_ms`
  - `screenshot_full_page` or `screenshot_selector`
  - optional `pre_click_selector`, `pre_click_wait_ms`, `pre_click_steps`

BAS UIs vary wildly—some need delays, some have iframes, some throw modals. Tweak selectors and add waits in code as needed for your target.

### Record steps with Playwright codegen

If the UI is JS-driven and hard to script from static URLs, record your click path and pull selectors:

```bash
npx playwright codegen https://tracersynchronydemo.trane.com/hui/index.html --viewport-size 1920,1080
```

Useful variant (save script while recording):

```bash
npx playwright codegen https://tracersynchronydemo.trane.com/hui/index.html --viewport-size 1920,1080 -o codegen-session.ts
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

   docker run --rm \
     -e MY_SITE_USERNAME \
     -e MY_SITE_PASSWORD \
     -v "$(pwd)/sites:/app/sites" \
     -v "$(pwd)/data:/app/data" \
     whistleblower --config /app/sites/my_site.local.json
   ```

---

## 🧪 Current Status

Early alpha—MVP capture works (login → nav → screenshot/DOM dump), tested on a private test site with real screenshots landing in data/.

Focus right now: rock-solid navigation and capture reliability across flaky UIs.

Next up (no hard dates):

- Basic change detection (compare runs)
- Simple rule-based "whistles" (e.g., fan icon says running but temp dropping)
- Optional local LLM narration of diffs (still read-only)

No rush. Build what works.

## 🚦 Alpha Exit Checklist

Mark this complete before cutting `v0.1.0-alpha`:

- [ ] `docker build -t whistleblower .` succeeds on a clean machine.
- [ ] At least 2 representative site configs run successfully (`--record-video` on).
- [ ] Each run writes `screenshot.png`, `dom.json`, `meta.json` per target.
- [ ] `readiness_error` is `null` for baseline demo targets.
- [ ] `bootstrap_recorder.py` generates usable `*.bootstrap.json` and `*.steps.json`.
- [ ] `analyze_capture.py` produces `analysis.md` + `analysis_summary.json`.
- [ ] Private secrets are not committed (`sites/*.local.json`, `.private/*` ignored).
- [ ] README quick start and config schema match real CLI behavior.

---

## 🧠 Analyze Captures with an Agent

After a Whistleblower run completes, you can ask an LLM to review each captured target
using both `screenshot.png` and `dom.json`.

1. Set API key:

   ```bash
   export OPENAI_API_KEY='your_api_key'
   ```

   Optional (recommended): store once in a private file:

   ```bash
   cp .private/openai.env.example .private/openai.env
   # edit .private/openai.env and set OPENAI_API_KEY=...
   ```

   `analyze_capture.py` auto-loads `.private/openai.env`.

2. Analyze the latest run for a site:

   ```bash
   python3 analyze_capture.py --site ignition_demo
   ```

3. Or analyze an explicit run directory:

   ```bash
   python3 analyze_capture.py --run-dir data/ignition_demo/20260212-174539
   ```

Outputs are written next to each target:
- `analysis.md` (human-readable findings)
- `analysis.json` (structured metadata)

And one run-level file:
- `analysis_summary.json`

---

## 📜 License

MIT. Fork it, break it, fix it, use it on whatever the hell you want.
