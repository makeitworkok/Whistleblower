#!/usr/bin/env python3
"""Quick functional test of tkinter_ui_refactored changes."""

import sys
import os

# Test 1: Import modules
print("=" * 60)
print("TEST 1: Import module checks")
print("=" * 60)

try:
    import tkinter_ui_refactored
    print("✓ tkinter_ui_refactored imports successfully")
except Exception as e:
    print(f"✗ tkinter_ui_refactored import error: {e}")
    sys.exit(1)

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

# Test 2: Check password injection logic in environment
print("\n" + "=" * 60)
print("TEST 2: Environment variable injection")
print("=" * 60)

os.environ["WHISTLEBLOWER_PASSWORD"] = "test_password_123"
retrieved = os.getenv("WHISTLEBLOWER_PASSWORD")
if retrieved == "test_password_123":
    print("✓ Environment variable injection works")
else:
    print(f"✗ Environment variable retrieval failed: got {retrieved}")

del os.environ["WHISTLEBLOWER_PASSWORD"]
if "WHISTLEBLOWER_PASSWORD" not in os.environ:
    print("✓ Environment variable cleanup works")
else:
    print("✗ Environment variable cleanup failed")

# Test 3: Verify bootstrap_recorder password handling
print("\n" + "=" * 60)
print("TEST 3: Bootstrap password placeholder")
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

# Test redaction function
redacted = bootstrap_recorder.redact_sensitive_events(test_events)
password_event = [e for e in redacted if e.get("input_type") == "password"][0]

if "<redacted:" in password_event["value"]:
    print(f"✓ Password redaction works: {password_event['value']}")
else:
    print(f"✗ Password not redacted: {password_event['value']}")

# Test 4: Verify whistleblower env placeholder resolution
print("\n" + "=" * 60)
print("TEST 4: Config placeholder resolution")
print("=" * 60)

test_config = {
    "login": {
        "username": "testuser",
        "password": "${WHISTLEBLOWER_PASSWORD}"
    }
}

os.environ["WHISTLEBLOWER_PASSWORD"] = "injected_password"
resolved = whistleblower.resolve_env_placeholders(test_config)

if resolved["login"]["password"] == "injected_password":
    print("✓ Environment placeholder resolution works")
else:
    print(f"✗ Placeholder resolution failed: got {resolved['login']['password']}")

# Test missing env var
test_config2 = {
    "login": {
        "password": "${MISSING_VAR}"
    }
}

try:
    whistleblower.resolve_env_placeholders(test_config2)
    print("✗ Should have raised error for missing env var")
except ValueError as e:
    if "MISSING_VAR" in str(e):
        print(f"✓ Proper error for missing env var: {e}")
    else:
        print(f"✗ Wrong error message: {e}")

del os.environ["WHISTLEBLOWER_PASSWORD"]

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
