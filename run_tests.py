#!/usr/bin/env python3
"""
Test runner script for Blink.

This script runs all automated tests using pytest.
Run this script to execute the full test suite.
"""

import subprocess
import sys
import os

def run_tests():
    """Run the test suite."""
    print("Running Blink test suite...")
    print("=" * 50)

    # Change to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Run pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short"
    ], capture_output=False)

    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
