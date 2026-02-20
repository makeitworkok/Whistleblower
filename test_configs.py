#!/usr/bin/env python3
"""Test suite for Whistleblower site configs."""

import json
import sys
from pathlib import Path

def validate_config(config_path):
    """Validate a single site config file."""
    print(f"\n{'='*60}")
    print(f"Testing: {config_path.name}")
    print('='*60)
    
    try:
        # 1. Load and parse JSON
        with open(config_path) as f:
            config = json.load(f)
        print("✅ JSON syntax valid")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {config_path}")
        return False
    
    # 2. Check required fields
    required_fields = ["name", "base_url", "login", "watch"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False
    print(f"✅ Required fields present")
    
    # 3. Validate login config
    login = config.get("login", {})
    login_required = ["username", "password", "user_selector", "pass_selector", "submit_selector"]
    login_missing = [f for f in login_required if f not in login]
    if login_missing:
        print(f"❌ Missing login fields: {login_missing}")
        return False
    print(f"✅ Login config valid")
    
    # 4. Check selectors (basic validation)
    selectors = [
        login.get("user_selector"),
        login.get("pass_selector"),
        login.get("submit_selector"),
        login.get("success_selector", "body")
    ]
    if any(not s or not isinstance(s, str) for s in selectors):
        print(f"❌ Invalid selectors: {selectors}")
        return False
    print(f"✅ Selectors look valid")
    
    # 5. Validate watch targets
    watch = config.get("watch", [])
    if not watch:
        print(f"⚠️  No watch targets configured")
    else:
        print(f"✅ Watch targets: {len(watch)}")
        for i, target in enumerate(watch):
            if "name" not in target or "url" not in target:
                print(f"   ❌ Target {i}: missing name or url")
                return False
            print(f"   ✓ Target {i}: {target['name']}")
    
    # 6. Detect login pattern
    user_sel = login.get("user_selector")
    pass_sel = login.get("pass_selector")
    
    # Niagara pattern: input.login-input and #password (often multi-step)
    if "login-input" in user_sel.lower():
        print(f"🔷 Detected: Niagara-style login (multi-step capable)")
    # Trane pattern: #userid, #password, #logon
    elif "userid" in user_sel.lower() and "password" in pass_sel.lower() and "logon" in login.get("submit_selector", "").lower():
        print(f"🔷 Detected: Trane Tracer Synchrony login (single-step)")
    # Generic pattern
    else:
        print(f"🔷 Detected: Custom/generic login pattern")
    
    print(f"\n✅ CONFIG VALID: {config_path.name}")
    return True

def main():
    """Run tests on all site configs."""
    sites_dir = Path("sites")
    
    # Find all .json files that are configs (not templates, not bootstrap, not steps, not registry)
    config_files = [
        f for f in sites_dir.glob("*.json")
        if not any(x in f.name for x in ["template", "bootstrap", "steps", "registry"])
    ]
    
    print("\n" + "="*60)
    print("WHISTLEBLOWER SITE CONFIG TEST SUITE")
    print("="*60)
    print(f"Found {len(config_files)} config files to test\n")
    
    results = {}
    for config_file in sorted(config_files):
        valid = validate_config(config_file)
        results[config_file.name] = valid
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    valid_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, valid in sorted(results.items()):
        status = "✅ PASS" if valid else "❌ FAIL"
        print(f"{status:10} {name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {valid_count}/{total_count} configs valid")
    print("="*60)
    
    return 0 if valid_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
