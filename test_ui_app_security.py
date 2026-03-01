#!/usr/bin/env python3
"""Test security fixes in ui_app.py (web UI)."""

import sys
import os
from pathlib import Path

print("=" * 60)
print("TEST 1: UI app input validation functions")
print("=" * 60)

# Import ui_app validation functions
try:
    import ui_app
    print("✓ ui_app imports successfully")
except Exception as e:
    print(f"✗ ui_app import error: {e}")
    sys.exit(1)

# Test URL validation
print("\nTesting URL validation:")
valid_urls = [
    "https://example.com",
    "http://localhost:8000",
    "https://site.io/login"
]

invalid_urls = [
    "not_a_url",
    "ftp://example.com",
    "/local/path",
    ""
]

for url in valid_urls:
    if ui_app.is_valid_http_url(url):
        print(f"  ✓ Valid URL accepted: {url}")
    else:
        print(f"  ✗ Valid URL rejected: {url}")
        sys.exit(1)

for url in invalid_urls:
    if not ui_app.is_valid_http_url(url):
        print(f"  ✓ Invalid URL rejected: {url}")
    else:
        print(f"  ✗ Invalid URL accepted: {url}")
        sys.exit(1)

# Test site name validation
print("\nTesting site name validation:")
valid_names = [
    "my_site",
    "site-123",
    "test.site",
    "a"
]

invalid_names = [
    "",
    "a" * 81,  # too long
    "site@invalid",
    "site/path",
    "site with spaces"
]

for name in valid_names:
    if ui_app.is_valid_site_name(name):
        print(f"  ✓ Valid name accepted: {name}")
    else:
        print(f"  ✗ Valid name rejected: {name}")
        sys.exit(1)

for name in invalid_names:
    if not ui_app.is_valid_site_name(name):
        print(f"  ✓ Invalid name rejected: {name}")
    else:
        print(f"  ✗ Invalid name accepted: {name}")
        sys.exit(1)

# Test bounded int parsing
print("\nTesting bounded integer parsing:")
result = ui_app.parse_bounded_int("1920", minimum=1, maximum=10000)
if result == 1920:
    print(f"  ✓ Valid int parsed: 1920")
else:
    print(f"  ✗ Valid int parsing failed")
    sys.exit(1)

result = ui_app.parse_bounded_int("20000", minimum=1, maximum=10000)
if result is None:
    print(f"  ✓ Out-of-range int rejected: 20000")
else:
    print(f"  ✗ Out-of-range int accepted: {result}")
    sys.exit(1)

result = ui_app.parse_bounded_int("invalid", minimum=1, maximum=10000)
if result is None:
    print(f"  ✓ Non-numeric string rejected")
else:
    print(f"  ✗ Non-numeric string accepted: {result}")
    sys.exit(1)

# Test relative path normalization
print("\nTesting relative path normalization:")
valid_paths = [
    "data/bootstrap",
    "sites/my_site.json",
    "path/to/file",
    ""
]

invalid_paths = [
    "/absolute/path",
    "../escaping",
    "path/../escape",
    "-invalid"
]

for path in valid_paths:
    result = ui_app.normalize_relative_path(path)
    if result is not None:
        print(f"  ✓ Valid path accepted: {path}")
    else:
        print(f"  ✗ Valid path rejected: {path}")
        sys.exit(1)

for path in invalid_paths:
    result = ui_app.normalize_relative_path(path)
    if result is None:
        print(f"  ✓ Invalid path rejected: {path}")
    else:
        print(f"  ✗ Invalid path accepted: {path}")
        sys.exit(1)

# Test analysis path security
print("\n" + "=" * 60)
print("TEST 2: Analysis path security")
print("=" * 60)

# Test safe path resolution
print("\nTesting safe analysis path resolution:")

# Create test markdown file structure
test_data_dir = Path("data/test_analysis")
test_data_dir.mkdir(parents=True, exist_ok=True)

test_md_file = test_data_dir / "report.md"
test_md_file.write_text("# Test Report")

# Test valid analysis path
result = ui_app.resolve_safe_analysis_path("data/test_analysis/report.md")
if result is not None and result.name == "report.md":
    print(f"  ✓ Valid analysis path accepted")
else:
    print(f"  ✗ Valid analysis path rejected")
    sys.exit(1)

# Test invalid: attempts to escape root
try:
    result = ui_app.resolve_safe_analysis_path("../../etc/passwd")
    if result is None:
        print(f"  ✓ Path traversal attempt blocked")
    else:
        print(f"  ✗ Path traversal not blocked")
        sys.exit(1)
except:
    print(f"  ✓ Path traversal attempt blocked (exception)")

# Test invalid: wrong file type
result = ui_app.resolve_safe_analysis_path("data/test_analysis/report.txt")
if result is None:
    print(f"  ✓ Non-markdown file rejected")
else:
    print(f"  ✗ Non-markdown file accepted")
    sys.exit(1)

# Clean up
import shutil
shutil.rmtree(test_data_dir, ignore_errors=True)

print("\n" + "=" * 60)
print("✓ ALL WEB UI SECURITY TESTS PASSED")
print("=" * 60)
print("\nSummary:")
print("  - URL validation prevents invalid/dangerous URLs")
print("  - Site name validation prevents special characters")
print("  - Viewport bounds validation prevents extreme values")
print("  - Path normalization prevents directory traversal")
print("  - Analysis path security restricts to allowed markdown files")
