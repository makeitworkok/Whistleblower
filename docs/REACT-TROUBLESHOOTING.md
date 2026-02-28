# React/SPA Troubleshooting Checklist

Quick diagnostic guide for when bootstrap recorder or main capture fails on React/SPA frontends.

---

## 🔍 Initial Diagnosis

Run through these questions first:

- [ ] Is this a React/Vue/Angular single-page application?
- [ ] Does the URL contain `#` hash routing (e.g., `app.com/#/dashboard`)?
- [ ] Do element class names look auto-generated (e.g., `css-1x2y3z4`)?
- [ ] Does content load after the initial page appears?
- [ ] Does clicking things not cause full page reloads?

**If you answered YES to 3+ questions above**, you're dealing with an SPA. Continue below.

---

## 🚨 Problem: Bootstrap Recorder Not Capturing Clicks

### Symptoms
- You click elements but `events.json` is empty
- Generated config has no `pre_click_steps`
- Console shows events but they're not saved

### Diagnosis Steps

1. **Check if clicks are registering:**
   ```bash
   # Look at raw events file
   cat data/bootstrap/<site>/*/events.json
   ```

2. **Verify event listener is loaded:**
   Open browser DevTools during recording:
   ```javascript
   console.log(window.__wbRecorderInstalled)  // Should be true
   ```

### Solutions

✅ **Solution 1: Let the page fully load before clicking**
- Wait 5-10 seconds after page appears
- Look for spinners/loading indicators to disappear
- Check that navigation elements are interactive

✅ **Solution 2: Re-run with increased viewport**
```bash
python3 bootstrap_recorder.py \
  --url "https://your-app.example.com/" \
  --site-name "my_site" \
  --viewport-width 1920 \
  --viewport-height 1080 \
  --record-video  # ← Helps debug what happened
```

✅ **Solution 3: Use Playwright codegen instead**
```bash
npx playwright codegen "https://your-app.example.com/" \
  --viewport-size 1920,1080
```
Then manually copy selectors to your config.

---

## 🚨 Problem: "Element Not Found" During Capture

### Symptoms
```
TimeoutError: Waiting for selector "[data-panel='main']" failed: timeout 30000ms exceeded
```

### Diagnosis Steps

1. **Is the selector correct?**
   ```bash
   # Test in browser DevTools console
   document.querySelector("[data-panel='main']")
   ```

2. **Does the element load late?**
   - Open the site manually and watch when element appears
   - Is there a loading spinner first?
   - How long does it take?

### Solutions

✅ **Solution 1: Increase settle_ms**
```json
{
  "settle_ms": 20000  // ← Increase from 10000 to 20000
}
```

✅ **Solution 2: Wait for loading indicator to disappear**
```json
{
  "pre_click_steps": [
    {
      "selector": ".loading-spinner",
      "action": "wait_for_hidden",
      "wait_ms": 10000
    }
  ]
}
```

✅ **Solution 3: Use a broader selector**
```json
{
  "root_selector": "body"  // ← Instead of specific component
}
```

✅ **Solution 4: Add selector candidates**
```json
{
  "selector": "[data-panel='main']",
  "selector_candidates": [
    "[data-panel='main']",
    "main[role='main']",
    "text=Dashboard"
  ]
}
```

---

## 🚨 Problem: Screenshot Captures Loading State

### Symptoms
- Screenshot shows spinners or "Loading..." text
- Content is partially loaded or blank
- Different every run

### Diagnosis Steps

1. **What does the manual flow feel like?**
   - Open site in browser
   - Navigate to target page
   - How long until content appears?

2. **Are there visual loading indicators?**
   - Spinners
   - Skeleton screens
   - "Loading..." text
   - Progress bars

### Solutions

✅ **Solution 1: Increase settle_ms significantly**
```json
{
  "settle_ms": 15000  // ← Try 15-20 seconds
}
```

✅ **Solution 2: Wait for specific loading indicators**
```json
{
  "pre_click_steps": [
    {
      "selector": "[aria-busy='true']",
      "action": "wait_for_hidden",
      "wait_ms": 15000
    }
  ]
}
```

✅ **Solution 3: Wait for actual content to appear**
```json
{
  "pre_click_steps": [
    {
      "selector": "[data-loaded='true']",
      "action": "wait_for_visible",
      "wait_ms": 10000
    }
  ]
}
```

---

## 🚨 Problem: Navigation Doesn't Reach Target URL

### Symptoms
```
TimeoutError: Navigation to https://app.example.com/#/dashboard did not complete
```
Or page stays on homepage instead of navigating.

### Diagnosis Steps

1. **Is this hash routing?**
   - URL contains `#` before path: `app.com/#/page`
   - Click navigation works, but direct URL doesn't

2. **Check browser network tab:**
   - Does request show as "cancelled" or "aborted"?
   - Does the browser actually load anything?

### Solutions

✅ **Solution 1: Use click navigation instead**
```json
{
  "url": "https://app.example.com/",  // ← Base URL only
  "pre_click_steps": [
    {
      "selector": "nav a[href='#/dashboard']",
      "action": "click",
      "wait_ms": 3000
    }
  ]
}
```

✅ **Solution 2: Let auto-retry handle it**
Whistleblower already catches `net::ERR_ABORTED` and retries. Just increase settle time:
```json
{
  "settle_ms": 12000
}
```

✅ **Solution 3: Navigate step-by-step**
```json
{
  "pre_click_steps": [
    {
      "selector": "[data-menu='equipment']",
      "action": "click",
      "wait_ms": 2000
    },
    {
      "selector": "[data-submenu='hvac']",
      "action": "click",
      "wait_ms": 2000
    }
  ]
}
```

---

## 🚨 Problem: Selector Works Once Then Fails

### Symptoms
- First run succeeds
- Subsequent runs fail with "element not found"
- Or element found but wrong content captured

### Diagnosis Steps

1. **Does React re-render change the DOM?**
   Open DevTools and inspect the element:
   - Does class name change each load?
   - Does element position shift?
   - Does component key change?

2. **Is there a race condition?**
   - Does element appear, disappear, then reappear?
   - Is there animation/transition?

### Solutions

✅ **Solution 1: Use stable data attributes**
```json
{
  "selector": "[data-testid='panel']"  // ← Instead of generated classes
}
```

✅ **Solution 2: Add extra wait time**
```json
{
  "settle_ms": 15000,
  "pre_click_steps": [
    {
      "selector": "...",
      "wait_ms": 5000  // ← Increase individual step wait
    }
  ]
}
```

✅ **Solution 3: Wait for animations to complete**
```json
{
  "settle_ms": 8000  // ← Extra time for CSS transitions
}
```

---

## 🚨 Problem: Login Success but Immediately Re-prompted

### Symptoms
- Login form fills correctly
- Page changes but then login form appears again
- Or capture fails with "login controls still visible"

### Diagnosis Steps

1. **Is there an in-app login modal?**
   - Does login appear after initial page load?
   - Is it a popup/modal instead of full page?

2. **Check session timeout:**
   - Does the site have aggressive session timeout?
   - Is there a "remember me" checkbox?

### Solutions

✅ **Solution 1: Update success selector**
```json
{
  "login": {
    "success_selector": "[data-testid='user-menu']"  // ← Specific to logged-in state
  }
}
```

✅ **Solution 2: Wait for dashboard content**
```json
{
  "login": {
    "success_selector": "main:has([data-dashboard='true'])"
  }
}
```

✅ **Solution 3: Increase login attempts**
```json
{
  "login_attempts": 3  // ← Try multiple times
}
```

---

## 🚨 Problem: Works in Bootstrap Recorder, Fails in Main Capture

### Symptoms
- Bootstrap recording succeeds perfectly
- Main capture with same config fails
- Timing seems different

### Diagnosis Steps

1. **Compare environments:**
   - Different network speed?
   - Different time of day (API response times)?
   - Different machine/browser version?

2. **Check timing assumptions:**
   - Did you rush through bootstrap recording?
   - Does real automation need more time?

### Solutions

✅ **Solution 1: Add buffer to all timing**
```json
{
  "settle_ms": 15000,  // ← Add 50% more time
  "pre_click_steps": [
    {
      "wait_ms": 3000  // ← Increase all step waits
    }
  ]
}
```

✅ **Solution 2: Add intermediate checks**
```json
{
  "pre_click_steps": [
    {
      "selector": "[data-step-1]",
      "action": "click",
      "wait_ms": 2000
    },
    {
      "selector": "[data-loading='true']",
      "action": "wait_for_hidden",
      "wait_ms": 10000
    },
    {
      "selector": "[data-step-2]",
      "action": "click",
      "wait_ms": 2000
    }
  ]
}
```

✅ **Solution 3: Use video recording to debug**
```bash
# Re-run bootstrap with video to see what happens
python3 bootstrap_recorder.py \
  --url "..." \
  --site-name "..." \
  --record-video
```

---

## 🛠️ General Debugging Workflow

### Step 1: Gather Information
```bash
# Run capture with full logs
python3 whistleblower.py --config sites/my_site.json 2>&1 | tee debug.log

# Check what was captured
ls -la data/my_site/latest/
```

### Step 2: Test Selectors Manually
```javascript
// In browser DevTools console:

// Does element exist?
document.querySelector('[data-panel="main"]')

// How many matches?
document.querySelectorAll('[data-tree-node]').length

// Is it visible?
const el = document.querySelector('[data-panel="main"]')
el.offsetParent !== null  // true if visible
```

### Step 3: Simplify Config
Strip down to minimal working version:
```json
{
  "watch": [
    {
      "name": "simple_test",
      "url": "https://app.example.com/",
      "root_selector": "body",  // ← Simplest possible
      "settle_ms": 20000,  // ← Very generous timing
      "screenshot_full_page": true
    }
  ]
}
```

Once working, gradually add complexity.

### Step 4: Use Bootstrap Recorder Again
```bash
python3 bootstrap_recorder.py \
  --url "https://app.example.com/" \
  --site-name "debug_session" \
  --record-video
```
Watch the video to see exactly when elements appear.

---

## 📚 Quick Reference

| Problem | First Thing to Try |
|---------|-------------------|
| Element not found | Increase `settle_ms` to 15000+ |
| Screenshot shows loader | Wait for loading indicator to hide |
| Navigation fails | Use click navigation instead of URL |
| Selector unstable | Switch to data attributes |
| Login loops | Update `success_selector` to logged-in state |
| Works manually, fails automated | Double all wait times |

---

## 🔗 Related Documentation

- [REACTJS-GUIDE.md](./REACTJS-GUIDE.md) - Full guide with explanations
- [REACT-QUICK-REF.md](./REACT-QUICK-REF.md) - Copy-paste config patterns
- [../README.md](../README.md) - Main Whistleblower docs

---

## 💡 Still Stuck?

1. **Record a video:** `--record-video` flag shows exactly what's happening
2. **Check the artifacts:** Look at `screenshot.png` and `dom.json` to see what was captured
3. **Test with Playwright codegen:** Interactive testing helps find correct selectors
4. **Simplify config to absolute minimum:** Then add complexity piece by piece

Remember: **Whistleblower is read-only**. If a selector would trigger a control action, don't use it.

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->
