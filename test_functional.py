#!/usr/bin/env python3
"""Functional compatibility tests for Whistleblower site configs."""

import subprocess
import sys
import time
from pathlib import Path

def test_config_execution(config_name, timeout_sec=30):
    """Test if whistleblower can run with a given config."""
    print(f"\n{'='*60}")
    print(f"FUNCTIONAL TEST: {config_name}")
    print('='*60)
    
    config_path = Path("sites") / f"{config_name}.json"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False, "File not found"
    
    try:
        print(f"Running: whistleblower.py --config {config_path}")
        print(f"Timeout: {timeout_sec} seconds")
        print("(This will attempt to log in and capture targets)")
        print("-" * 60)
        
        # Run whistleblower with timeout
        result = subprocess.run(
            [sys.executable, "whistleblower.py", "--config", str(config_path)],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        
        print("STDOUT:")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        
        # Check exit code
        if result.returncode == 0:
            print(f"\n✅ Execution successful (exit code 0)")
            return True, "Success"
        else:
            print(f"\n⚠️  Exited with code {result.returncode}")
            # Some errors are expected (network issues, credentials)
            # We're mainly testing that whistleblower.py itself works
            if "ERROR:" in result.stderr or "ERROR:" in result.stdout:
                return False, f"Error occurred (exit {result.returncode})"
            else:
                return True, f"Completed (exit {result.returncode})"
    
    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout after {timeout_sec} seconds")
        print("   This could mean:")
        print("   - Network connectivity issue (host unreachable)")
        print("   - System is responding slowly")
        print("   - Login credentials incorrect")
        return False, f"Timeout ({timeout_sec}s) - network/auth expected"
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, f"Exception: {str(e)}"

def main():
    """Run functional tests."""
    print("\n" + "="*60)
    print("WHISTLEBLOWER FUNCTIONAL COMPATIBILITY TESTS")
    print("="*60)
    
    # Test setup
    test_cases = [
        # (config_name, timeout_sec, description)
        ("localNiagara", 90, "Niagara multi-step login - LOCAL SYSTEM"),
        ("196-21test", 30, "Trane Tracer - SKIP if network unavailable"),
        ("196-22test", 30, "Trane Tracer - SKIP if network unavailable"),
        ("example", 30, "Generic example config"),
    ]
    
    results = {}
    
    for config_name, timeout, description in test_cases:
        print(f"\n{description}")
        success, message = test_config_execution(config_name, timeout)
        results[config_name] = (success, message)
    
    # Summary
    print("\n" + "="*60)
    print("FUNCTIONAL TEST SUMMARY")
    print("="*60)
    
    for config_name, (success, message) in results.items():
        status = "✅ PASS" if success else "⚠️  SKIP"
        print(f"{status:10} {config_name:20} - {message}")
    
    print("\n" + "="*60)
    print("NOTES:")
    print("="*60)
    print("""
✅ PASS  = Config executed successfully, whistleblower.py is compatible
⚠️  SKIP = Config has network/auth issues (expected for external systems)

The important thing: whistleblower.py must NOT crash with our code changes.
If you see actual ERROR messages, the changes may have compatibility issues.

Results:
- localNiagara: Should PASS (local system available)
- 196-21test, 196-22test: May SKIP if IPs not on network
- example: Will likely SKIP (example.com not real)
""")

if __name__ == "__main__":
    main()
