# Working with ReactJS and SPA Frontends in Whistleblower

> **Status**: Work in Progress  
> Last updated: 2026-02-19

## Overview

ReactJS and Single-Page Application (SPA) frontends present unique challenges for automation tools like Whistleblower. This guide covers strategies for reliably capturing screenshots and DOM state from React-based BAS/SCADA interfaces.

## Quick Start Templates

**Before diving into theory, grab a template:**

1. **[react-url-based.template.json](../sites/react-url-based.template.json)** - For sites where URLs change during navigation (✅ EASIEST, try this first)
2. **[react-click-based.template.json](../sites/react-click-based.template.json)** - For sites where URL stays same but views change (requires selector work)
3. **[trane-tracer-synchrony.template.json](../sites/trane-tracer-synchrony.template.json)** - Trane Tracer Synchrony login + baseline captures
4. **[ignition_perspective_annotated.example.json](../sites/ignition_perspective_annotated.example.json)** - Detailed Ignition Perspective example

**Workflow**: Run `bootstrap_recorder.py` → Check if generated config has multiple URLs → Pick template → Test → Adjust timing

See [REACT-QUICK-REF.md](REACT-QUICK-REF.md) for copy-paste config patterns.

## Key Challenges

### 1. **Dynamic Selectors**
React applications often generate:
- Auto-generated class names (e.g., `css-1x2y3z4`, `sc-AbCdEf`)
- Dynamic component identifiers
- Randomly hashed attributes
- Deeply nested component hierarchies

### 2. **Asynchronous Rendering**
- Components mount/unmount dynamically
- Data fetches happen after initial page load
- Loading states replace actual content
- Hydration delays on client-side rendering

### 3. **Hash-Based Routing**
- URL changes don't trigger full page reloads
- Navigation happens via JavaScript (React Router, etc.)
- `page.goto()` may not trigger expected state changes
- Browser considers navigation "aborted" (`net::ERR_ABORTED`)

### 4. **Event-Driven Updates**
- UI updates based on WebSocket/SSE data
- State changes triggered by timers
- Conditional rendering based on application state

---

## Solutions & Best Practices

### Strategy 1: Use Stable Selectors

#### Prefer Data Attributes
React apps often expose stable data attributes for testing:

```json
{
  "selector": "[data-testid='dashboard-panel']",
  "selector_candidates": [
    "[data-testid='dashboard-panel']",
    "[data-component='dashboard']",
    "#main-dashboard"
  ]
}
```

**Priority order:**
1. `data-testid`, `data-test`, `data-cy` (test attributes)
2. `data-component`, `data-view` (semantic attributes)
3. `id` attributes (if stable)
4. ARIA attributes: `[aria-label="Dashboard"]`, `[role="main"]`
5. Text content: `text=Dashboard` (use as last resort)

#### Avoid Fragile Selectors
❌ **Don't use:**
- Generated class names: `.css-1x2y3z4`, `.MuiBox-root-123`
- Deep nth-child chains: `div:nth-child(3) > div:nth-child(2)`
- Position-dependent selectors without context

✅ **Do use:**
- Semantic HTML: `nav`, `main`, `article`, `section`
- Stable custom attributes: `[data-component-path]`, `[data-widget-id]`
- Combined stable selectors: `nav[aria-label="Main"] button[aria-label="Dashboard"]`

### Strategy 2: Handle Loading States

#### Wait for Content, Not Just Elements

The built-in `wait_for_target_ready()` function checks for:
- Element exists in DOM
- Not showing "loading..." text
- Document ready state is "complete"
- Network activity has settled

**Enhance loading detection in your config:**

```json
{
  "name": "react_dashboard",
  "url": "https://your-spa.example.com/#/dashboard",
  "root_selector": "main[role='main']",
  "settle_ms": 15000,
  "screenshot_full_page": false,
  "pre_click_steps": [
    {
      "selector": "[data-testid='loading-indicator']",
      "action": "wait_for_hidden",
      "wait_ms": 5000
    }
  ]
}
```

#### Increase Settle Times
React apps often need more time to hydrate and fetch data:

```json
{
  "settle_ms": 15000,  // ← 15 seconds for complex dashboards
  "timeout_ms": 120000 // ← 2 minutes for slow networks
}
```

### Strategy 3: Use Bootstrap Recorder with React Apps

The `bootstrap_recorder.py` tool automatically handles many React challenges:

#### Recording a React Session

```bash
python3 bootstrap_recorder.py \
  --url "https://your-react-app.example.com/" \
  --site-name "react_scada" \
  --viewport-width 1920 \
  --viewport-height 1080 \
  --record-video
```

**What it captures:**
- Click events with multiple selector candidates
- Form field changes (including React controlled inputs)
- Navigation events and URL changes
- Timing between actions

#### Generated Output

**`sites/react_scada.bootstrap.json`** - Basic config
**`sites/react_scada.steps.json`** - Suggested pre-click steps with:
- Multiple selector candidates
- Inferred wait times based on observed delays
- Action types (click, dblclick)
- Element text for verification

#### Refining Bootstrap Output

1. **Review selector candidates:**
   ```json
   {
     "selector_candidates": [
       "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
       "text=AHU 2"
     ]
   }
   ```
   Choose the most stable selector (usually data attributes first).

2. **Adjust wait times:**
   Bootstrap recorder infers timing from your actions. Increase for slower environments:
   ```json
   {
     "wait_ms": 2000  // ← Increase to 3000-5000 for React hydration
   }
   ```

3. **Add loading state checks:**
   Manually add steps to wait for loaders to disappear.

### Strategy 4: Handle Hash Routing

React Router and similar libraries use hash-based navigation (`#/dashboard`). Whistleblower handles this automatically:

#### The Problem
```python
page.goto("https://app.example.com/#/dashboard")
# Browser may abort navigation with net::ERR_ABORTED
# because the page is already loaded
```

#### The Solution
Whistleblower's `goto_with_hash_abort_tolerance()` function:
- Catches `net::ERR_ABORTED` errors
- Polls for URL changes
- Waits for the React Router to update

**You don't need to do anything special** - this is handled automatically.

#### If Navigation Still Fails
Use `pre_click_steps` to navigate within the app:

```json
{
  "name": "dashboard",
  "url": "https://app.example.com/",
  "root_selector": "main",
  "pre_click_steps": [
    {
      "selector": "nav a[href='#/dashboard']",
      "action": "click",
      "wait_ms": 3000
    }
  ]
}
```

### Strategy 5: Multi-Step Navigation

For deeply nested views (tree navigation, tab switching, modal opening):

```json
{
  "name": "nested_equipment_view",
  "url": "https://app.example.com/#/equipment",
  "root_selector": "[data-view='equipment-detail']",
  "settle_ms": 12000,
  "pre_click_steps": [
    {
      "selector": "[data-tree-node='building-1']",
      "action": "click",
      "nth": 0,
      "wait_ms": 2000,
      "comment": "Expand building node in tree"
    },
    {
      "selector": "[data-tree-node='floor-2']",
      "action": "click",
      "nth": 0,
      "wait_ms": 2000,
      "comment": "Expand floor node"
    },
    {
      "selector": "[data-equipment-id='AHU-01']",
      "action": "dblclick",
      "nth": 0,
      "wait_ms": 5000,
      "comment": "Open equipment detail with double-click"
    }
  ]
}
```

**Key points:**
- Each step can have its own `wait_ms`
- Use `nth` to select specific elements in a list
- `action` can be `click` or `dblclick`
- Comments are ignored by Whistleblower but help with maintenance

### Strategy 6: Use Playwright Codegen for Reconnaissance

When selectors are completely unstable, use Playwright's code generator:

```bash
npx playwright codegen \
  "https://your-react-app.example.com/" \
  --viewport-size 1920,1080
```

**This opens an interactive browser where you can:**
1. Click through your navigation flow
2. See generated selectors in real-time
3. Copy stable selectors to your config
4. Test selectors in the Playwright inspector

**Save the session:**
```bash
npx playwright codegen \
  "https://your-react-app.example.com/" \
  --viewport-size 1920,1080 \
  -o codegen-session.ts
```

Then extract selectors from `codegen-session.ts`.

---

## Common React Patterns & Solutions

### Pattern: Material-UI (MUI)

**Problem:** Generated class names like `.MuiButton-root-123`

**Solution:** Use data attributes or ARIA labels:
```json
{
  "selector": "button[aria-label='Open Dashboard']",
  "selector_candidates": [
    "button[aria-label='Open Dashboard']",
    "button[data-testid='dashboard-btn']",
    "text=Dashboard"
  ]
}
```

### Pattern: Ant Design

**Solution:** Use `.ant-` prefixed stable classes:
```json
{
  "selector": ".ant-menu-item[data-menu-id='dashboard']",
  "selector_candidates": [
    ".ant-menu-item[data-menu-id='dashboard']",
    ".ant-menu-item:has-text('Dashboard')"
  ]
}
```

### Pattern: Perspective (Ignition)

Ignition's Perspective framework uses `data-component` attributes:

```json
{
  "selector": "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
  "selector_candidates": [
    "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
    "text=AHU 2"
  ]
}
```

**Note:** `data-component-path` values are often stable across sessions.

### Pattern: Custom React Components

If you control the React app, add test attributes:

```jsx
// Your React component
function DashboardPanel() {
  return (
    <div data-testid="dashboard-panel" data-component="dashboard">
      <h1 data-testid="dashboard-title">Building Status</h1>
      {/* ... */}
    </div>
  );
}
```

Then use in Whistleblower:
```json
{
  "selector": "[data-testid='dashboard-panel']"
}
```

---

## Debugging React Capture Issues

### Issue: "Element not found"

**Diagnosis:**
1. Check if element exists: Open DevTools and test selector
2. Is it in a shadow DOM? (Not currently supported)
3. Is it in an iframe? (Add iframe handling)
4. Does it load after initial render?

**Solutions:**
- Increase `settle_ms` to 15000+
- Add `pre_click_steps` to wait for loading indicators
- Use broader selectors: `[data-component*="dashboard"]` instead of exact match

### Issue: "Screenshot captures loading state"

**Diagnosis:**
Element exists but content isn't loaded yet.

**Solutions:**
```json
{
  "settle_ms": 20000,
  "pre_click_steps": [
    {
      "selector": "[data-loading='true']",
      "action": "wait_for_hidden",
      "wait_ms": 10000
    }
  ]
}
```

### Issue: "Navigation doesn't reach target URL"

**Diagnosis:**
Hash routing causing `ERR_ABORTED`.

**Solutions:**
1. Let auto-retry handle it (already implemented)
2. Navigate via clicks instead of `url`:
   ```json
   {
     "url": "https://app.example.com/",  // ← Base URL only
     "pre_click_steps": [
       {
         "selector": "nav a[href='#/target']",
         "action": "click",
         "wait_ms": 3000
       }
     ]
   }
   ```

### Issue: "Selector works once then fails"

**Diagnosis:**
React re-renders may change element references or component keys.

**Solutions:**
- Use attribute selectors instead of class names
- Add retry logic via multiple `selector_candidates`
- Check if element is conditionally rendered

---

## React-Specific Config Examples

### Example 1: Simple React Dashboard

```json
{
  "name": "react_simple",
  "base_url": "https://dashboard.example.com/",
  "ignore_https_errors": false,
  "login_attempts": 2,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "login": {
    "username": "${REACT_USER}",
    "password": "${REACT_PASS}",
    "user_selector": "input[name='username']",
    "pass_selector": "input[name='password']",
    "submit_selector": "button[type='submit']",
    "success_selector": "[data-testid='user-menu']"
  },
  "watch": [
    {
      "name": "main_dashboard",
      "url": "https://dashboard.example.com/#/dashboard",
      "root_selector": "main[role='main']",
      "settle_ms": 12000,
      "screenshot_full_page": true
    }
  ]
}
```

### Example 2: Complex Navigation with Tree

```json
{
  "name": "react_tree_nav",
  "base_url": "https://scada.example.com/",
  "ignore_https_errors": true,
  "login_attempts": 2,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "login": {
    "username": "${SCADA_USER}",
    "password": "${SCADA_PASS}",
    "user_selector": "#email",
    "pass_selector": "#password",
    "submit_selector": "button[aria-label='Log In']",
    "success_selector": "[aria-label='User Settings']"
  },
  "watch": [
    {
      "name": "equipment_detail",
      "url": "https://scada.example.com/#/equipment",
      "root_selector": "[data-view='equipment-detail']",
      "settle_ms": 15000,
      "screenshot_full_page": false,
      "screenshot_selector": "[data-panel='equipment-info']",
      "pre_click_steps": [
        {
          "selector": "[data-tree-expand][data-node-id='site-main']",
          "action": "click",
          "nth": 0,
          "wait_ms": 2000
        },
        {
          "selector": "[data-tree-node='building-hvac']",
          "action": "click",
          "nth": 0,
          "wait_ms": 2000
        },
        {
          "selector": "[data-equipment-card='AHU-01']",
          "action": "dblclick",
          "nth": 0,
          "wait_ms": 5000
        }
      ]
    }
  ]
}
```

### Example 3: Ignition Perspective (Real-World)

Based on the actual `BAS_DEMOclick` config in the repository:

```json
{
  "name": "ignition_perspective",
  "base_url": "https://demo.inductiveautomation.com/data/perspective/client/building-management-system-demo/",
  "ignore_https_errors": true,
  "login_attempts": 2,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "login": {
    "username": "",
    "password": "",
    "user_selector": "#username",
    "pass_selector": "#password",
    "submit_selector": "button[type='submit']",
    "success_selector": "body"
  },
  "watch": [
    {
      "name": "ahu_2_detail",
      "url": "https://demo.inductiveautomation.com/data/perspective/client/building-management-system-demo/",
      "root_selector": "body",
      "settle_ms": 10000,
      "screenshot_full_page": false,
      "pre_click_steps": [
        {
          "selector": "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
          "selector_candidates": [
            "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
            "text=AHU 2"
          ],
          "action": "click",
          "nth": 0,
          "wait_ms": 2000
        }
      ]
    }
  ]
}
```

---

## Best Practices Checklist

- [ ] **Always use `bootstrap_recorder.py` first** - Let it discover selectors automatically
- [ ] **Prefer data attributes** over class names or position-based selectors
- [ ] **Test selectors in DevTools** before adding to config
- [ ] **Increase `settle_ms`** to 12000-20000 for React apps
- [ ] **Use multiple `selector_candidates`** as fallbacks
- [ ] **Add pre-click steps** for multi-stage navigation
- [ ] **Handle loading states** explicitly
- [ ] **Document complex selectors** with comments in your JSON (strip before use)
- [ ] **Test on slow networks** to verify timeouts are sufficient
- [ ] **Review bootstrap suggestions** - don't blindly trust auto-generated selectors

---

## Future Improvements

Potential enhancements being considered:

- [ ] Auto-detect and wait for React hydration
- [ ] Smarter loading state detection (spinner patterns, skeleton screens)
- [ ] Support for shadow DOM elements
- [ ] Iframe navigation helpers
- [ ] Selector stability scoring
- [ ] Auto-fallback through selector candidates
- [ ] React DevTools integration for component path discovery

---

## Related Documentation

- [REACT-TROUBLESHOOTING.md](./REACT-TROUBLESHOOTING.md) - Step-by-step troubleshooting checklist
- [REACT-QUICK-REF.md](./REACT-QUICK-REF.md) - Quick reference with copy-paste snippets
- [`bootstrap_recorder.py`](../bootstrap_recorder.py) - Record sessions and generate configs
- [`whistleblower.py`](../whistleblower.py) - Main capture engine
- [`sites/example.json`](../sites/example.json) - Config template
- [`sites/ignition_perspective_annotated.example.json`](../sites/ignition_perspective_annotated.example.json) - Annotated real-world example
- [`README.md`](../README.md#bootstrap-a-config-by-recording-a-real-session) - Bootstrap documentation

---

## Questions or Issues?

If you encounter React-specific issues not covered here:

1. Run `bootstrap_recorder.py` with `--record-video` to capture the session
2. Review `data/bootstrap/<site>/events.json` for captured interactions
3. Check `sites/<site>.steps.json` for suggested selectors
4. Test selectors in browser DevTools console
5. Increase `settle_ms` and `wait_ms` values incrementally

Remember: **Whistleblower is read-only**. Never use selectors that trigger control actions or setpoint changes.

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->
