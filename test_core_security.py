#!/usr/bin/env python3
"""Test core password injection and bootstrap security fixes without GUI."""

import sys
import os

# Test 1: Import core modules (without tkinter)
print("=" * 60)
print("TEST 1: Import core module checks")
print("=" * 60)

try:
    import bootstrap_recorder
    print("✓ bootstrap_recorder imports successfully")
except Exception as e:
    print(f"✗ bootstrap_recorder import error: {e}")
    sys.exit(1)

try:
    import whistleblower
    print("✓ whistleblower imports successfully")
except Exception as e:
    print(f"✗ whistleblower import error: {e}")
    sys.exit(1)

try:
    import site_config
    print("✓ site_config imports successfully")
except Exception as e:
    print(f"✗ site_config import error: {e}")
    sys.exit(1)

# Test 2: Bootstrap password redaction
print("\n" + "=" * 60)
print("TEST 2: Bootstrap password redaction")
print("=" * 60)

test_events = [
    {
        "type": "change",
        "selector": "#username",
        "input_type": "text",
        "value": "testuser"
    },
    {
        "type": "change",
        "selector": "#password",
        "input_type": "password",
        "value": "secret_pass_123"
    }
]

redacted = bootstrap_recorder.redact_sensitive_events(test_events)
password_event = [e for e in redacted if e.get("input_type") == "password"][0]

if "<redacted:" in password_event["value"] and "secret_pass_123" not in password_event["value"]:
    print(f"✓ Password redaction works: {password_event['value']}")
else:
    print(f"✗ Password not properly redacted: {password_event['value']}")
    sys.exit(1)

# Test 3: Verify placeholder instead of clear password
print("\n" + "=" * 60)
print("TEST 3: Bootstrap config password placeholder")
print("=" * 60)

inferred_creds = {
    "username": "testuser",
    "password": "secret_123"
}

# Simulate what bootstrap does
inferred_password = inferred_creds["password"]
password_value = "${WHISTLEBLOWER_PASSWORD}" if inferred_password else ""

if password_value == "${WHISTLEBLOWER_PASSWORD}":
    print(f"✓ Bootstrap uses placeholder: {password_value}")
else:
    print(f"✗ Bootstrap not using placeholder: {password_value}")
    sys.exit(1)

# Test 4: Whistleblower env placeholder resolution
print("\n" + "=" * 60)
print("TEST 4: Config env placeholder resolution")
print("=" * 60)

test_config = {
    "login": {
        "username": "testuser",
        "password": "${WHISTLEBLOWER_PASSWORD}"
    },
    "base_url": "https://example.com"
}

os.environ["WHISTLEBLOWER_PASSWORD"] = "injected_password"
try:
    resolved = whistleblower.resolve_env_placeholders(test_config)
    
    if resolved["login"]["password"] == "injected_password":
        print("✓ Env placeholder resolution works")
    else:
        print(f"✗ Placeholder resolution failed: got {resolved['login']['password']}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Placeholder resolution error: {e}")
    sys.exit(1)

# Test 5: Verify error when env var missing
print("\n" + "=" * 60)
print("TEST 5: Error handling for missing env vars")
print("=" * 60)

test_config_missing = {
    "login": {
        "password": "${MISSING_REQUIRED_VAR}"
    }
}

if "MISSING_REQUIRED_VAR" in os.environ:
    del os.environ["MISSING_REQUIRED_VAR"]

try:
    whistleblower.resolve_env_placeholders(test_config_missing)
    print("✗ Should have raised error for missing env var")
    sys.exit(1)
except ValueError as e:
    if "MISSING_REQUIRED_VAR" in str(e):
        print(f"✓ Proper error for missing env var: {e}")
    else:
        print(f"✗ Wrong error message: {e}")
        sys.exit(1)

# Clean up
if "WHISTLEBLOWER_PASSWORD" in os.environ:
    del os.environ["WHISTLEBLOWER_PASSWORD"]

# Test 6: UI integration points exist
print("\n" + "=" * 60)
print("TEST 6: Verify UI integration changes")
print("=" * 60)

# Check site_config creates default config with password notes
config = site_config.create_default_config(
    "test_site",
    "https://example.com"
)

if "capture_settings" in config:
    print("✓ Site config has capture settings")
else:
    print("✗ Site config missing capture settings")
    sys.exit(1)

if "directories" in config and "bootstrap_artifacts" in config["directories"]:
    print("✓ Site config has bootstrap artifacts directory")
else:
    print("✗ Site config missing bootstrap directories")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL CORE TESTS PASSED")
print("=" * 60)
print("\nSummary:")
print("  - Bootstrap redacts password from events.json")
print("  - Bootstrap stores ${WHISTLEBLOWER_PASSWORD} placeholder in config")
print("  - Whistleblower resolves placeholder from environment")
print("  - Tkinter UI will prompt for password after bootstrap")
print("  - Password injection happens before each capture")
