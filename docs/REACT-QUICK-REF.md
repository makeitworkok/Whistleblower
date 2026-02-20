# React/SPA Quick Reference

> Quick copy-paste snippets for common React automation patterns

## Selector Priority (Best to Worst)

```
1. data-testid, data-test, data-cy
2. data-component, data-view, data-widget-id
3. id (if stable)
4. ARIA: aria-label, role
5. Semantic HTML: nav, main, article
6. Text content: text=Dashboard
7. Stable framework classes: .ant-menu-item
---
❌ NEVER: Generated classes, nth-child chains
```

## Common Config Patterns

### Basic React Dashboard
```json
{
  "name": "dashboard",
  "url": "https://app.example.com/#/dashboard",
  "root_selector": "main[role='main']",
  "settle_ms": 12000,
  "screenshot_full_page": true
}
```

### Wait for Loading to Complete
```json
{
  "settle_ms": 15000,
  "pre_click_steps": [
    {
      "selector": "[data-loading='true']",
      "action": "wait_for_hidden",
      "wait_ms": 10000
    }
  ]
}
```

### Tree Navigation (Click to Expand)
```json
{
  "pre_click_steps": [
    {
      "selector": "[data-tree-node='building-1']",
      "action": "click",
      "nth": 0,
      "wait_ms": 2000
    },
    {
      "selector": "[data-tree-node='floor-2']",
      "action": "click",
      "nth": 0,
      "wait_ms": 2000
    }
  ]
}
```

### Double-Click to Open
```json
{
  "selector": "[data-equipment-id='AHU-01']",
  "action": "dblclick",
  "nth": 0,
  "wait_ms": 5000
}
```

### Navigate via Menu Click (Instead of URL)
```json
{
  "url": "https://app.example.com/",
  "pre_click_steps": [
    {
      "selector": "nav a[href='#/dashboard']",
      "action": "click",
      "wait_ms": 3000
    }
  ]
}
```

## Framework-Specific Selectors

### Material-UI (MUI)
```json
{
  "selector": "button[aria-label='Open Dashboard']",
  "selector_candidates": [
    "button[aria-label='Open Dashboard']",
    "button[data-testid='dashboard-btn']",
    ".MuiButton-root:has-text('Dashboard')"
  ]
}
```

### Ant Design
```json
{
  "selector": ".ant-menu-item[data-menu-id='dashboard']",
  "selector_candidates": [
    ".ant-menu-item[data-menu-id='dashboard']",
    ".ant-menu-item:has-text('Dashboard')"
  ]
}
```

### Ignition Perspective
```json
{
  "selector": "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
  "selector_candidates": [
    "div[data-component='ia.display.label'][data-component-path='C$0:0:0$0:1.0:0:0:0:1:1']",
    "text=AHU 2"
  ]
}
```

## Debugging Commands

### Test Selector in DevTools Console
```javascript
// Does element exist?
document.querySelector('[data-testid="dashboard"]')

// Multiple matches?
document.querySelectorAll('[data-tree-node]').length

// Is it visible?
document.querySelector('[data-panel="main"]').offsetParent !== null
```

### Bootstrap Recorder (Discover Selectors)
```bash
python3 bootstrap_recorder.py \
  --url "https://your-app.example.com/" \
  --site-name "my_site" \
  --viewport-width 1920 \
  --viewport-height 1080 \
  --record-video
```

### Playwright Codegen (Interactive Testing)
```bash
npx playwright codegen \
  "https://your-app.example.com/" \
  --viewport-size 1920,1080
```

## Common Issues & Fixes

| Issue | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| Element not found | Loads after page render | Increase `settle_ms` to 15000+ |
| Screenshot shows loader | Content not ready | Add pre-click wait for loader hidden |
| Navigation fails | Hash routing abort | Use click navigation instead of URL |
| Selector works once | React re-render changed DOM | Use data attributes, not classes |
| Slow initial load | React hydration | Increase `settle_ms` and add 5s buffer |

## Environment Variables Pattern

```json
{
  "login": {
    "username": "${MY_SITE_USERNAME}",
    "password": "${MY_SITE_PASSWORD}",
    "user_selector": "input[name='username']",
    "pass_selector": "input[type='password']",
    "submit_selector": "button[type='submit']",
    "success_selector": "[data-testid='user-menu']"
  }
}
```

```bash
export MY_SITE_USERNAME='operator'
export MY_SITE_PASSWORD='secure_password'
```

## Full Working Example

```json
{
  "name": "react_hvac_monitor",
  "base_url": "https://hvac.example.com/",
  "ignore_https_errors": false,
  "login_attempts": 2,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "login": {
    "username": "${HVAC_USER}",
    "password": "${HVAC_PASS}",
    "user_selector": "input[name='email']",
    "pass_selector": "input[name='password']",
    "submit_selector": "button[aria-label='Sign In']",
    "success_selector": "[data-testid='main-nav']"
  },
  "watch": [
    {
      "name": "building_overview",
      "url": "https://hvac.example.com/#/buildings",
      "root_selector": "main[role='main']",
      "settle_ms": 12000,
      "screenshot_full_page": true
    },
    {
      "name": "ahu_01_detail",
      "url": "https://hvac.example.com/#/equipment",
      "root_selector": "[data-view='equipment-detail']",
      "settle_ms": 15000,
      "screenshot_full_page": false,
      "screenshot_selector": "[data-panel='equipment-info']",
      "pre_click_steps": [
        {
          "selector": "[data-building-id='main']",
          "action": "click",
          "nth": 0,
          "wait_ms": 2000
        },
        {
          "selector": "[data-floor='2']",
          "action": "click",
          "nth": 0,
          "wait_ms": 2000
        },
        {
          "selector": "[data-equipment='AHU-01']",
          "action": "dblclick",
          "nth": 0,
          "wait_ms": 5000
        }
      ]
    }
  ]
}
```

---

**See [REACTJS-GUIDE.md](./REACTJS-GUIDE.md) for detailed explanations and troubleshooting.**
