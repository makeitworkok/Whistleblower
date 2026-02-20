# Testing Guide

This document explains how to run Whistleblower's test suite and add tests for new BAS sites.

## Quick Start

```powershell
# Validate all site configs (syntax, structure, patterns)
python test_configs.py

# Run functional tests on reachable sites
python test_functional.py
```

---

## Test Suite Overview

Whistleblower includes two automated test scripts:

### 1. **test_configs.py** - Configuration Validation

Validates the syntax and structure of all site configuration files without requiring network access.

**What it checks:**
- ✅ JSON syntax (valid parsing)
- ✅ Required fields (name, base_url, login, watch)
- ✅ Login configuration (user_selector, pass_selector, submit_selector, success_selector)
- ✅ Selector validity (non-empty strings)
- ✅ Watch targets (each has name and url)
- 🔷 Login pattern detection (Niagara vs. Trane vs. Custom)

**Usage:**
```powershell
python test_configs.py
```

**Example output:**
```
============================================================
WHISTLEBLOWER SITE CONFIG TEST SUITE
============================================================
Found 5 config files to test

============================================================
Testing: localNiagara.json
============================================================
✅ JSON syntax valid
✅ Required fields present
✅ Login config valid
✅ Selectors look valid
✅ Watch targets: 3
   ✓ Target 0: prelogin
   ✓ Target 1: login
   ✓ Target 2: dashboard
🔷 Detected: Niagara-style login (multi-step capable)

✅ CONFIG VALID: localNiagara.json

[... more configs ...]

============================================================
SUMMARY: 5/5 configs valid
```

### 2. **test_functional.py** - Live Execution Testing

Runs whistleblower.py against each site config and verifies execution completes without fatal errors. Gracefully handles unreachable systems (network, credentials).

**What it tests:**
- Whistleblower.py execution with config
- Process exit codes
- Error detection in stdout/stderr
- Timeout handling (per-config timeouts)

**Usage:**
```powershell
python test_functional.py
```

**Example output:**
```
============================================================
WHISTLEBLOWER FUNCTIONAL COMPATIBILITY TESTS
============================================================

Niagara multi-step login - LOCAL SYSTEM
============================================================
FUNCTIONAL TEST: localNiagara
Running: whistleblower.py --config sites\localNiagara.json
Timeout: 90 seconds
(This will attempt to log in and capture targets)
------------------------------------------------------------
STDOUT:
[Playwright browser launch...]
✅ Execution successful (exit code 0)

============================================================
Trane Tracer - SKIP if network unavailable
============================================================
FUNCTIONAL TEST: 196-21test
...
⚠️  Timeout after 30 seconds
   This could mean:
   - Network connectivity issue (host unreachable)
   - System is responding slowly
   - Login credentials incorrect

============================================================
FUNCTIONAL TEST SUMMARY
============================================================
✅ PASS       localNiagara         - Success
⚠️  SKIP       196-21test           - Timeout - network expected
⚠️  SKIP       196-22test           - Timeout - network expected
...
```

---

## Adding Tests for New Sites

### Step 1: Create Configuration File
Create a new site configuration in `sites/{name}.json`:

```json
{
  "name": "my-new-building",
  "base_url": "https://bms.example.com",
  "ignore_https_errors": true,
  "login": {
    "username": "operator",
    "password": "secret",
    "user_selector": "#user_field",
    "pass_selector": "#password_field",
    "submit_selector": "button[type='submit']",
    "success_selector": "main, [role='main']"
  },
  "watch": [
    {
      "name": "main_dashboard",
      "url": "https://bms.example.com/dashboard",
      "root_selector": "body",
      "settle_ms": 5000
    }
  ]
}
```

See [sites/README.md](../sites/README.md) for template options and [docs/TEMPLATES.md](TEMPLATES.md) for detailed configuration guide.

### Step 2: Validate Configuration
```powershell
python test_configs.py
```

The new config will be automatically discovered and tested. Check that:
- JSON is valid
- All required fields are present
- Login pattern is correctly detected

### Step 3: Test Execution
```powershell
python test_functional.py
```

If your site is reachable:
- Whistleblower will attempt login
- Targets will be captured
- Artifacts appear in `data/{name}/TIMESTAMP/`

If unreachable:
- Test gracefully times out (expected for remote/demo systems)
- No false failures

---

## Understanding Test Results

### Config Tests: Green Light Checklist
```
✅ JSON syntax valid
✅ Required fields present
✅ Login config valid
✅ Selectors look valid
✅ Watch targets: N
🔷 Detected: [Pattern]
✅ CONFIG VALID
```

**Action:** Ready to test functionally

### Config Tests: Red Light Issues

| Issue | Fix |
|-------|-----|
| `❌ JSON parse error` | Fix JSON syntax (missing comma, quote, bracket) |
| `❌ Missing required fields` | Add name, base_url, login, or watch |
| `❌ Missing login fields` | Add user_selector, pass_selector, submit_selector |
| `❌ Invalid selectors` | Ensure selectors are non-empty strings (use browser DevTools to verify) |
| `❌ Target missing name or url` | Each watch target needs `name` and `url` fields |

### Functional Tests: Expected Outcomes

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ PASS | System is reachable, login succeeded, capture completed | Verify artifacts in `data/` |
| ⚠️  SKIP | Network/credentials prevented capture (expected for remote) | Manual test if available |

---

## Troubleshooting Tests

### "Config file not found"
```powershell
# Ensure config is in sites/ directory
ls sites/ | grep -i your-site-name
```

### "Unexpected token" / JSON errors
```powershell
# Validate JSON syntax using PowerShell
Get-Content sites/your-config.json | ConvertFrom-Json
```

### Selectors not working in functional test
1. Use `bootstrap_recorder.py` to auto-discover selectors:
   ```powershell
   python bootstrap_recorder.py
   ```
2. Verify selectors in browser DevTools (F12)
3. Test CSS selectors in browser console: `document.querySelector("#id")`

### Timeouts on local systems
- Increase timeout in `test_functional.py` (change `timeout_sec` parameter)
- Check if system is running and accessible
- Verify credentials are correct
- Check network connectivity

---

## Continuous Testing Workflow

When adding new BAS vendors:

1. **Discover** (first time only)
   ```powershell
   python bootstrap_recorder.py
   # Outputs: sites/new-vendor.bootstrap.json
   ```

2. **Validate**
   ```powershell
   python test_configs.py
   # Should show: ✅ CONFIG VALID
   ```

3. **Test**
   ```powershell
   python test_functional.py
   # Check for: ✅ PASS or ⚠️  SKIP (expected)
   ```

4. **Verify Artifacts**
   ```powershell
   ls data/new-vendor/ | Sort-Object -Descending | Select-Object -First 1
   # Latest timestamp contains your captures
   ```

5. **Document** (optional)
   - Add to [sites/README.md](../sites/README.md) vendor table
   - Update [sites/templates-registry.json](../sites/templates-registry.json) with profile

---

## Test Coverage

Current test suite validates:
- ✅ Configuration syntax (JSON parsing)
- ✅ Configuration structure (required fields)
- ✅ Whistleblower.py execution with configs
- ✅ Login pattern detection
- ✅ Multi-step login handling (Niagara)
- ✅ Single-step login handling (Trane, React)

**Not tested (manual):**
- Screenshot quality/completeness
- DOM capture accuracy
- Selector accuracy on specific systems
- Timing issues (settle_ms tuning)
- Custom credential providers

---

## CI/CD Integration (Future)

To integrate tests into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Validate all site configs
  run: python test_configs.py

- name: Run functional tests
  run: python test_functional.py
  # Only on self-hosted runners with network access to test systems
```

---

## Questions or Issues?

Check [README.md](../README.md) for troubleshooting and [TEMPLATES.md](TEMPLATES.md) for configuration details.
