# CLI Reference Guide

This guide covers command-line usage for **whistleblower.py**, **bootstrap_recorder.py**, **analyze_capture.py**, and **test scripts**.

> **Note**: Most users should use the [local web UI](../README.md#-local-ui-recommended-for-non-devs) (`ui_app.py`) instead of these CLI commands. This guide is for automation, scripting, and advanced workflows.

---

## Table of Contents

- [Main Capture Runner](#main-capture-runner-whistleblowerpy)
- [Bootstrap Recorder](#bootstrap-recorder-bootstrap_recorderpy)
- [Analysis](#analysis-analyze_capturepy)
- [Testing](#testing)
- [Advanced: Playwright Codegen](#advanced-playwright-codegen)

---

## Main Capture Runner: whistleblower.py

Run a single capture operation from the command line.

### Usage

```bash
python3 whistleblower.py --config sites/my-site.json
```

### Options

- `--config` - Path to site configuration JSON file (required)
- `--record-video` - Record full browser interaction as video (debug only)

### With Video Recording

```bash
python3 whistleblower.py --config sites/my-site.json --record-video
```

Video output is saved per run at:
`data/<site_name>/<timestamp>/video/session.mp4`

**Note**: For normal scheduled/routine capture, omit `--record-video` to save disk space.

### Environment Variables

Credentials can be loaded from environment variables:

```bash
export MY_SITE_USERNAME='your_user'
export MY_SITE_PASSWORD='your_password'

python3 whistleblower.py --config sites/my-site.json
```

In your config file, reference them as:

```json
{
  "login": {
    "username": "${MY_SITE_USERNAME}",
    "password": "${MY_SITE_PASSWORD}"
  }
}
```

---

## Bootstrap Recorder: bootstrap_recorder.py

Generate a starter config by recording a real operator session.

### Usage Example

```bash
python3 bootstrap_recorder.py \
  --url "https://your-bas-host/login" \
  --site-name "my_site"
```

### Command Options

- `--url` - Base URL of the system (required)
- `--site-name` - Name for generated config files (required)
- `--ignore-https-errors` - Skip SSL certificate validation
- `--record-video` - Record the bootstrap session as video

### Complete Example

```bash
python3 bootstrap_recorder.py \
  --url "https://your-bas-host/login" \
  --site-name "my_site" \
  --ignore-https-errors \
  --record-video
```

### Interactive Session

1. The recorder opens a browser window
2. Perform your normal operator workflow:
   - Log in to the system
   - Navigate to dashboards/graphics you want to capture
   - Click through any menus or controls
3. Return to the terminal and press **Enter** when done

### Generated Outputs

- `sites/my_site.bootstrap.json` - Starter Whistleblower config with discovered selectors
- `sites/my_site.steps.json` - Suggested `pre_click_steps` for navigation
- `data/bootstrap/my_site/<timestamp>/` - Raw events, screenshots, optional video

### Using Generated Configs

1. Copy the bootstrap config to your working config:

   ```bash
   cp sites/my_site.bootstrap.json sites/my-site.json
   ```

2. Edit the config to add real credentials:

   Generated configs use environment placeholders by default:
   - `username`: `${MY_SITE_USERNAME}`
   - `password`: `${MY_SITE_PASSWORD}`

3. Add navigation steps from `my_site.steps.json` to your config's `watch[].pre_click_steps`

4. Test the config:

   ```bash
   export MY_SITE_USERNAME='your_user'
   export MY_SITE_PASSWORD='your_password'

   python3 whistleblower.py --config sites/my-site.json
   ```

---

## Analysis: analyze_capture.py

Run LLM-based analysis on captured screenshots and DOM data.

### Provider Options

- **OpenAI** (default): `--provider openai` (or omit `--provider`)
- **xAI/Grok**: `--provider xai` or `--provider grok`

### API Key Setup

#### Method 1: Environment Variable

```bash
export OPENAI_API_KEY='your_api_key'
```

For Grok/xAI:

```bash
export XAI_API_KEY='your_xai_key'
```

`GROK_API_KEY` is also recognized as a fallback.

#### Method 2: Private File (Recommended)

```bash
cp .private/openai.env.example .private/openai.env
# Edit .private/openai.env and set OPENAI_API_KEY or XAI_API_KEY
```

`analyze_capture.py` auto-loads `.private/openai.env`.

### Usage Examples

**Analyze latest run for a site (OpenAI):**

```bash
python3 analyze_capture.py --site ignition_demo
```

**Analyze with Grok/xAI:**

```bash
python3 analyze_capture.py --provider grok --site ignition_demo
```

**Analyze specific run directory:**

```bash
python3 analyze_capture.py --run-dir data/ignition_demo/20260212-174539
```

**Analyze time window across runs:**

```bash
python3 analyze_capture.py \
  --site ignition_demo \
  --start-utc 2026-02-01T00:00:00Z \
  --end-utc 2026-02-19T23:59:59Z
```

**Per-page analysis instead of combined summary:**

```bash
python3 analyze_capture.py --site ignition_demo --per-page
```

### Analysis Outputs

Written next to each captured target:

- `analysis.md` - Human-readable findings
- `analysis.json` - Structured metadata

Run-level summary:

- `analysis_summary.json` - Overview across all targets

---

## Testing

Validate configurations and test live system connectivity.

### Config Validation

Quick validation of all site configs (no network required):

```bash
python3 test_configs.py
```

This checks:

- JSON syntax
- Required fields
- Selector format
- Credential placeholders

### Functional Testing

Test actual login and capture on reachable systems:

```bash
python3 test_functional.py
```

This performs:

- Network connectivity check
- Login flow validation
- Screenshot capture test
- DOM extraction test

### Auto-Discovery

Both scripts auto-discover all `sites/*.json` files. Add new site configs and re-run—tests update automatically.

### Additional Resources

👉 **[docs/TESTING.md](TESTING.md)** - Detailed testing guide and troubleshooting

---

## Advanced: Playwright Codegen

For complex JavaScript-driven UIs where navigation is hard to script from static URLs.

### Basic Codegen

Record click paths and extract selectors:

```bash
npx playwright codegen https://your-bas-host.example.com/index.html --viewport-size 1920,1080
```

### Save Script While Recording

```bash
npx playwright codegen https://your-bas-host.example.com/index.html \
  --viewport-size 1920,1080 \
  -o codegen-session.ts
```

### Using Generated Selectors

Extract click actions from the generated script and add them to your site config under `watch[].pre_click_steps`:

```json
{
  "watch": [
    {
      "name": "my-page",
      "url": "https://example.com/dashboard",
      "pre_click_steps": [
        {
          "action": "click",
          "selector": "button[data-view='dashboard']",
          "wait_after_ms": 1000
        }
      ]
    }
  ]
}
```

---

## Scheduled Capture (Cron/Task Scheduler)

### Linux/macOS (cron)

Edit crontab:

```bash
crontab -e
```

Add entry (example: every 15 minutes):

```cron
*/15 * * * * cd /path/to/Whistleblower && /usr/bin/python3 whistleblower.py --config sites/my-site.json >> logs/capture.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., repeat every 15 minutes)
4. Action: Start a program
   - Program: `python3.exe`
   - Arguments: `whistleblower.py --config sites/my-site.json`
   - Start in: `C:\path\to\Whistleblower`

### Using the UI for Scheduling

The local web UI (`ui_app.py`) provides built-in scheduling without external tools:

```bash
python3 ui_app.py
```

Navigate to the Schedule tab and configure capture intervals.

---

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Ensure dependencies are installed
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

#### Selector Not Found

- Use `bootstrap_recorder.py` to discover actual selectors
- Check selector syntax in config
- Add `settle_ms` wait time for slow-loading pages

#### Login Fails

- Verify credentials in config or environment variables
- Check `success_selector` matches post-login page element
- Enable video recording to debug: `--record-video`

#### SSL Certificate Errors

Add to your site config:

```json
{
  "ignore_https_errors": true
}
```

Or use with bootstrap_recorder:

```bash
python3 bootstrap_recorder.py --url https://... --ignore-https-errors
```

#### Further Reading

- **[docs/REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md)** - SPA/React-specific issues
- **[docs/TESTING.md](TESTING.md)** - Testing and validation guide
- **[sites/README.md](../sites/README.md)** - Configuration guide

---

## Best Practices

1. **Use the UI for interactive work** - The web UI (`ui_app.py`) is easier for bootstrapping, one-off captures, and analysis
2. **Use CLI for automation** - Scripts, cron jobs, CI/CD pipelines
3. **Start with bootstrap_recorder** - Don't manually write selectors
4. **Test configs before scheduling** - Run `test_configs.py` and `test_functional.py`
5. **Store credentials safely** - Use environment variables, never commit configs with real passwords
6. **Monitor disk space** - Captures accumulate; rotate/archive old data periodically
7. **Skip video in production** - Only use `--record-video` for debugging

---

## Quick Reference

| Task | Command |
| ---- | ------- |
| Single capture | `python3 whistleblower.py --config sites/my-site.json` |
| Bootstrap config | `python3 bootstrap_recorder.py --url https://... --site-name my_site` |
| Analyze latest | `python3 analyze_capture.py --site my_site` |
| Validate configs | `python3 test_configs.py` |
| Test live systems | `python3 test_functional.py` |
| Start web UI | `python3 ui_app.py` |

---

For additional help, see:

- [Main README](../README.md)
- [Configuration Guide](../sites/README.md)
- [Testing Guide](TESTING.md)
- [React/SPA Guide](REACTJS-GUIDE.md)
