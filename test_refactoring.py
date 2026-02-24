#!/usr/bin/env python3
"""
Quick test to verify refactored bootstrap_recorder and whistleblower modules work.
This tests that the modules can be imported and the new functions are callable.
"""

import sys
from pathlib import Path


def test_imports():
    """Test that modules can be imported."""
    print("Testing imports...")
    try:
        import bootstrap_recorder
        import whistleblower
        print("✓ Successfully imported bootstrap_recorder and whistleblower")
        return True
    except ImportError as exc:
        print(f"✗ Import failed: {exc}")
        return False


def test_bootstrap_function_exists():
    """Test that run_bootstrap() function exists."""
    print("\nTesting bootstrap_recorder.run_bootstrap() exists...")
    try:
        import bootstrap_recorder
        assert hasattr(bootstrap_recorder, 'run_bootstrap'), "run_bootstrap function not found"
        assert callable(bootstrap_recorder.run_bootstrap), "run_bootstrap is not callable"
        print("✓ bootstrap_recorder.run_bootstrap() exists and is callable")
        return True
    except (AssertionError, ImportError) as exc:
        print(f"✗ Test failed: {exc}")
        return False


def test_capture_function_exists():
    """Test that run_capture() function exists."""
    print("\nTesting whistleblower.run_capture() exists...")
    try:
        import whistleblower
        assert hasattr(whistleblower, 'run_capture'), "run_capture function not found"
        assert callable(whistleblower.run_capture), "run_capture is not callable"
        print("✓ whistleblower.run_capture() exists and is callable")
        return True
    except (AssertionError, ImportError) as exc:
        print(f"✗ Test failed: {exc}")
        return False


def test_cli_still_works():
    """Test that CLI entry points still exist."""
    print("\nTesting CLI compatibility...")
    try:
        import bootstrap_recorder
        import whistleblower
        assert hasattr(bootstrap_recorder, 'main'), "bootstrap_recorder.main() not found"
        assert hasattr(whistleblower, 'main'), "whistleblower.main() not found"
        assert callable(bootstrap_recorder.main), "bootstrap_recorder.main() not callable"
        assert callable(whistleblower.main), "whistleblower.main() not callable"
        print("✓ CLI entry points (main functions) still exist")
        return True
    except (AssertionError, ImportError) as exc:
        print(f"✗ Test failed: {exc}")
        return False


def test_function_signatures():
    """Test that functions have expected parameters."""
    print("\nTesting function signatures...")
    try:
        import inspect
        import bootstrap_recorder
        import whistleblower
        
        # Check bootstrap signature
        bootstrap_sig = inspect.signature(bootstrap_recorder.run_bootstrap)
        bootstrap_params = list(bootstrap_sig.parameters.keys())
        expected_bootstrap = ['url', 'site_name', 'output_dir', 'config_out', 'steps_out',
                             'viewport_width', 'viewport_height', 'ignore_https_errors',
                             'record_video', 'browser_type']
        for param in expected_bootstrap:
            assert param in bootstrap_params, f"Missing parameter: {param}"
        print(f"✓ bootstrap_recorder.run_bootstrap() has correct parameters")
        
        # Check capture signature
        capture_sig = inspect.signature(whistleblower.run_capture)
        capture_params = list(capture_sig.parameters.keys())
        expected_capture = ['config_path', 'data_dir', 'timeout_ms', 'settle_ms',
                           'post_login_wait_ms', 'headed', 'record_video',
                           'video_width', 'video_height']
        for param in expected_capture:
            assert param in capture_params, f"Missing parameter: {param}"
        print(f"✓ whistleblower.run_capture() has correct parameters")
        
        return True
    except (AssertionError, ImportError) as exc:
        print(f"✗ Test failed: {exc}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Whistleblower Refactoring Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_bootstrap_function_exists,
        test_capture_function_exists,
        test_cli_still_works,
        test_function_signatures,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All tests passed! Refactoring successful.")
        return 0
    else:
        print("✗ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
