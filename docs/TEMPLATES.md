# Whistleblower Templates & Vendor Support

This document provides a comprehensive guide to Whistleblower's **template system** and **BAS vendor support**.

---

## Table of Contents

1. [What are Templates?](#what-are-templates)
2. [Available Templates](#available-templates)
3. [Quick Start by Vendor](#quick-start-by-vendor)
4. [Auto-Discovery with bootstrap_recorder](#auto-discovery-with-bootstrap_recorder)
5. [Creating Custom Templates](#creating-custom-templates)
6. [Login Patterns](#login-patterns)
7. [Credential Management](#credential-management)

---

## What are Templates?

Templates are **JSON configuration files** that serve as starting points for capturing different BAS (Building Automation System) vendors.

### Why Templates?

- **Different vendors use different login patterns** (single-page, multi-page, OAuth, etc.)
- **Different selectors** for username/password fields vary by vendor
- **Different URL patterns** (hash routing vs. traditional routing)
- **Different HTTPS cert handling** (many BAS systems use self-signed certs)

A template **encodes the patterns** for a specific vendor, so you don't have to discover them from scratch.

### File Organization

```
sites/
├── *.template.json          # Vendor templates (templates, not configs)
├── *.json                   # Active configs (ready to run)
├── *.bootstrap.json         # Auto-discovered configs (from bootstrap_recorder)
├── *.steps.json             # Navigation steps from bootstrap_recorder
├── README.md                # Template quick-start guide
└── templates-registry.json  # Registry of all available templates
```

---

## Available Templates

### 1. Niagara (Tridium)

**File:** `niagara.template.json`

**Use when:** You have a Niagara Framework (N4) system

**Login Pattern:** **2-step multi-page**
- Page 1 (`/prelogin`): Username entry
- Page 2 (`/login`): Password entry (auto-redirect after Step 1)

**Key Selectors:**
```json
{
  "user_selector": "input.login-input",
  "pass_selector": "#password",
  "submit_selector": "#login-submit"
}
```

**Special Notes:**
- HTTPS is standard (often self-signed → use `ignore_https_errors: true`)
- Dashboards use `.px` files (PointExtreme)
- Example URLs: `/prelogin`, `/login`, `/ord/file:%5Epx/PxFile.px`

**Setup Example:**
```bash
cp sites/niagara.template.json sites/my-building.json
# Edit sites/my-building.json:
#   - Replace "your_niagara_host" with actual hostname
#   - Set NIAGARA_USERNAME and NIAGARA_PASSWORD env vars
python3 whistleblower.py --config sites/my-building.json
```

---

### 2. Meatball Tracers

**File:** `trane-tracer-synchrony.template.json`

**Use when:** You have a Meatball/Tracers system

**Login Pattern:** **Single-step form**
- Standard HTML form with username and password fields

**Key Selectors:**
```json
{
  "user_selector": "#userid",
  "pass_selector": "#password",
  "submit_selector": "#logon"
}
```

**Special Notes:**
- Uses `/hui/index.html` for login landing
- Uses `/hui/hui.html` for main app shell
- Hash-routed views (e.g., `#app=devices&view=SUMMARY`)
- Enterprise system with typical HTTPS

**Setup Example:**
```bash
cp sites/trane-tracer-synchrony.template.json sites/my-tracer.json
# Edit sites/my-tracer.json
#   - Replace "your-meatball-host" with actual hostname
#   - Set TRANE_USERNAME and TRANE_PASSWORD env vars
python3 whistleblower.py --config sites/my-tracer.json
```

---

### 3. React/SPA with URL Routing

**File:** `react-url-based.template.json`

**Use when:** Custom web app or vendor SPA with hash-based routing

**Login Pattern:** **Single-step form**

**Key Characteristics:**
- Modern React/Vue/Angular SPA
- Navigation via URL hash (#/path)
- Reliable URL targeting (no fragile click selectors)
- Often custom implementations

**Setup Example:**
```bash
cp sites/react-url-based.template.json sites/my-app.json
# Customize selectors based on your app's HTML
python3 whistleblower.py --config sites/my-app.json
```

---

### 4. React/SPA with Click Navigation

**File:** `react-click-based.template.json`

**Use when:** Custom web app where navigation is click-based, not URL-based

**Login Pattern:** **Single-step form**

**Key Characteristics:**
- Navigation happens via menu clicks
- No URL change (or indirect URL changes)
- Requires `pre_click_selector` or `pre_click_steps`
- More fragile (click selectors may change with UI updates)

**Example with pre_click_selector:**
```json
{
  "watch": [
    {
      "name": "reports_view",
      "url": "https://myapp.local/dashboard",
      "pre_click_selector": ".menu-reports",
      "pre_click_wait_ms": 2000,
      "settle_ms": 5000
    }
  ]
}
```

---

### 5. Generic / Custom

**File:** `example.json`

**Use when:** You don't know what template fits

**Approach:**
- Use `bootstrap_recorder.py` to discover selectors automatically
- Copy generated `.bootstrap.json` and customize as needed
- Contribut your findings so we can build more templates!

---

## Quick Start by Vendor

### I have a **Niagara** system

```bash
# 1. Copy template
cp sites/niagara.template.json sites/my-niagara.json

# 2. Edit with your hostname and credentials
nano sites/my-niagara.json
#   name: "my-building"
#   base_url: "https://my-niagara-server.local"
#   login.username: "ReadOnly" (or use env var ${NIAGARA_USERNAME})
#   login.password: "..." (or use env var ${NIAGARA_PASSWORD})

# 3. Test
python3 whistleblower.py --config sites/my-niagara.json

# 4. Schedule
python3 ui_app.py  # Then use web UI for scheduling
```

### I have a **Meatball Tracers** system

```bash
cp sites/trane-tracer-synchrony.template.json sites/my-tracer.json
# Edit similarly, customize watch URLs
python3 whistleblower.py --config sites/my-tracer.json
```

### I have a **custom/unknown** system

```bash
# 1. Use auto-discovery
python3 bootstrap_recorder.py --url https://your-system.local --site-name my-system

# 2. Review what was discovered
cat sites/my-system.bootstrap.json

# 3. Test it
python3 whistleblower.py --config sites/my-system.bootstrap.json

# 4. If successful, move to active config
mv sites/my-system.bootstrap.json sites/my-system.json

# 5. (Optional) Create a template from your successful config
#    Then submit a PR to help others with the same system!
```

### I have **multiple sites** of the same vendor

```bash
# Copy template once per site
cp sites/niagara.template.json sites/building-a.json
cp sites/niagara.template.json sites/building-b.json
cp sites/niagara.template.json sites/building-c.json

# Customize each with different URLs/credentials
nano sites/building-a.json   # https://building-a.local ...
nano sites/building-b.json   # https://building-b.local ...
nano sites/building-c.json   # https://building-c.local ...

# Now you can capture all three independently
python3 whistleblower.py --config sites/building-a.json &
python3 whistleblower.py --config sites/building-b.json &
python3 whistleblower.py --config sites/building-c.json &
```

---

## Auto-Discovery with bootstrap_recorder

`bootstrap_recorder.py` is a **tool for discovering** login selectors and navigation patterns automatically.

### How It Works

1. Launches a real Chromium browser
2. **Records all your interactions:**
   - Form fills (username, password)
   - Clicks and navigation
   - Form submissions
   - Page loads and redirects
3. **Captures evidence:**
   - Screenshots of each page
   - CSS selectors for elements you interact with
   - Full interaction log
   - (Optional) Video of session
4. **Generates a starter config** with discovered selectors

### Usage

```bash
python3 bootstrap_recorder.py \
  --url https://your-system.local \
  --site-name my-vendor \
  --ignore-https-errors        # If self-signed certs
```

### What It Outputs

- `sites/my-vendor.bootstrap.json` — Discovered config (ready to test!)
- `sites/my-vendor.steps.json` — Suggested navigation steps
- `data/bootstrap/my-vendor/<timestamp>/` — Evidence:
  - Screenshots
  - DOM extracts
  - Interaction log
  - (Optional) video/session.mp4

### Next Steps After Recording

1. **Test the bootstrap config:**
   ```bash
   python3 whistleblower.py --config sites/my-vendor.bootstrap.json
   ```

2. **If it works:**
   ```bash
   # Promote to active config
   mv sites/my-vendor.bootstrap.json sites/my-vendor.json
   ```

3. **If it doesn't work, debug:**
   - Review screenshots in `data/bootstrap/my-vendor/*/`
   - Review interaction log in `sites/my-vendor.bootstrap.json`
   - Try auto-discovery again with `--headed` to watch browser
   - Or manually adjust selectors based on discovered patterns

---

## Login Patterns

Whistleblower supports different login architectures:

### Pattern 1: Single-Step Login (Most Common)

```
User fills username + password on same page → Submit
```

**Selectors:**
```json
{
  "user_selector": "#username",
  "pass_selector": "#password",
  "submit_selector": "button[type='submit']"
}
```

**Whistleblower behavior:**
- Waits for BOTH fields to be visible and enabled
- Fills username
- Fills password
- Submits form
- Waits for success indicator

---

### Pattern 2: Multi-Step Login (Niagara, Some Custom Systems)

```
Page 1: User enters username, submits
   ↓ (page redirects)
Page 2: User enters password, submits
   ↓
Success
```

**Selectors:**
```json
{
  "user_selector": "input.login-input",
  "pass_selector": "#password",
  "submit_selector": "#login-submit"
}
```

**Whistleblower behavior (auto-adaptive):**
- Waits for username OR password field to appear
- If only username visible → Fill it, submit, wait for password page
- If only password visible → Fill it, submit
- If both visible → Fill both, submit (single-step fallback)

---

### Pattern 3: Form-Based with Special Fields

```
Email (instead of username)
Company ID + username
Password
CSRF token
```

**Approach:**
1. Use `bootstrap_recorder.py` to discover all fields
2. Add to config:
   ```json
   {
     "user_selector": "#email",  // or whatever the field is
     "pass_selector": "#password"
   }
   ```

---

### Pattern 4: OAuth / SSO / Advanced Auth

Not yet natively supported. **Workaround options:**
1. Set up a **read-only API user** if the system offers one (bypass login)
2. Use **bootstrap_recorder.py** to log in manually, then schedule captures (session stays alive)
3. Configure **environment-specific accounts** that have longer session timeouts

---

## Credential Management

### Option 1: Environment Variables (Recommended)

**In config:**
```json
{
  "login": {
    "username": "${NIAGARA_USERNAME}",
    "password": "${NIAGARA_PASSWORD}",
    ...
  }
}
```

**In shell:**
```bash
export NIAGARA_USERNAME="ReadOnly"
export NIAGARA_PASSWORD="SecurePassword123"
python3 whistleblower.py --config sites/my-site.json
```

**Advantages:**
- ✅ Credentials never stored in files
- ✅ Easy to use with CI/CD systems (GitHub Actions, Jenkins, etc.)
- ✅ Different credentials per environment (dev/prod)

---

### Option 2: .env File (Convenient, but less secure)

**Create `.env`:**
```
NIAGARA_USERNAME=ReadOnly
NIAGARA_PASSWORD=SecurePassword123
```

**In config:**
```json
{
  "login": {
    "username": "${NIAGARA_USERNAME}",
    "password": "${NIAGARA_PASSWORD}"
  }
}
```

**Load in shell:**
```bash
set -a; source .env; set +a
python3 whistleblower.py --config sites/my-site.json
```

**Advantages:**
- ✅ Credentials in one place
- ⚠️ File must be gitignored (never commit!)

---

### Option 3: Direct in Config (NOT RECOMMENDED)

```json
{
  "login": {
    "username": "ReadOnly",
    "password": "SecurePassword123"
  }
}
```

**Disadvantages:**
- ❌ Credentials in plaintext in config file
- ❌ Must be gitignored or credentials leak
- ❌ Hard to use in CI/CD

**Use only for:**
- Testing/dev environments
- Demo/sandbox systems (not real buildings)

---

## Creating Custom Templates

If your BAS vendor isn't in the registry, you can create a template:

### Step 1: Discovery (Using bootstrap_recorder)

```bash
python3 bootstrap_recorder.py \
  --url https://your-system.local \
  --site-name my-vendor-name \
  --ignore-https-errors
```

### Step 2: Review Generated Config

```bash
cat sites/my-vendor-name.bootstrap.json
```

Extract key information:
- Login selectors found
- Navigation paths
- Success indicators
- Screenshot evidence in `data/bootstrap/my-vendor-name/`

### Step 3: Create Template

Copy and edit `sites/example.json` or another template as base:

```json
{
  "_meta": {
    "template_type": "my-vendor",
    "vendor": "Vendor Corporation",
    "system": "Product Name (Version)",
    "description": "Brief description of login flow",
    "login_pattern": "single-step or multi-step"
  },
  
  "name": "your_site_name",
  "base_url": "https://your-vendor-host",
  
  "ignore_https_errors": true,
  "login_attempts": 2,
  
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  
  "login": {
    "username": "${MY_VENDOR_USERNAME}",
    "password": "${MY_VENDOR_PASSWORD}",
    "user_selector": "...",      // From bootstrap_recorder output
    "pass_selector": "...",      // From bootstrap_recorder output
    "submit_selector": "...",    // From bootstrap_recorder output
    "success_selector": "..."    // Indicator of successful login
  },
  
  "watch": [
    {
      "name": "page_1",
      "url": "...",               // From bootstrap_recorder output
      "root_selector": "body",
      "settle_ms": 5000
    },
    // ... more pages
  ]
}
```

### Step 4: Test Your Template

```bash
cp sites/my-vendor-name.bootstrap.json sites/my-vendor-test.json
python3 whistleblower.py --config sites/my-vendor-test.json --headed
```

Watch the browser to see if it:
1. Logs in successfully
2. Navigates to all pages
3. Captures screenshots without errors

### Step 5: Share It (Optional)

Help the community! Consider:
1. Renaming to `my-vendor.template.json`
2. Adding to `sites/templates-registry.json`
3. Opening a PR on the [Whistleblower repository](https://github.com/makeitworkok/Whistleblower)

---

## Troubleshooting

### Login fails: "could not find enabled login controls"

**Possible causes:**
1. Wrong selectors (changed in vendor update)
2. Fields disabled/hidden (wait time too short)
3. Multi-step misdetection

**Solutions:**
- Run `bootstrap_recorder.py` again to re-discover
- Increase `login_attempts` in config
- Check `ignore_https_errors` setting
- Add screenshots to see what page you're actually on

### Captures show login page, not dashboard

**Causes:**
- Session expires between login and capture
- Redirect loops
- CSRF token issues

**Solutions:**
- Increase `post_login_wait_ms` to 20000
- Check success_selector (make it more specific)
- Use UI instead of CLI (sessions stay alive longer)

### "Timeout waiting for locator..."

**Causes:**
- Selectors are wrong
- Fields not visible (CSS display:none)
- JavaScript takes too long to render

**Solutions:**
- Run in `--headed` mode to watch browser
- Increase `settle_ms`
- Check HTML in browser dev tools vs. selector in config
- Try bootstrap_recorder to confirm selectors

---

## Resources

- [Main README](../README.md)
- [sites/README.md](../sites/README.md) — Quick config guide
- [sites/templates-registry.json](../sites/templates-registry.json) — Full registry
- Example configs in `sites/` directory

---

## Contributing

Have a new BAS vendor?  
Have a template improvement?  
Want to add Johnson Controls, Honeywell, Schneider Electric, etc.?

**Please contribute!**

1. Create your template using the process above
2. Test thoroughly
3. Open a PR on [GitHub](https://github.com/makeitworkok/Whistleblower)

Your template will help others with the same system! 🙏

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->
