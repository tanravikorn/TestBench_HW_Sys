"""
Master Test Runner for OV7670→VGA Pipeline
Runs all testbenches for:
1. SCCB Controller (camera configuration via I2C-like protocol)
2. Camera Capture (pixel ingest to BRAM)
3. VGA Controller (frame reading and VGA output timing)
"""

import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def cocotb_has_failures(results_xml: Path) -> bool:
    if not results_xml.exists():
        return True
    tree = ET.parse(results_xml)
    root = tree.getroot()
    failures = root.findall(".//failure")
    errors = root.findall(".//error")
    testcases = root.findall(".//testcase")
    return len(failures) > 0 or len(errors) > 0 or len(testcases) == 0


def run_tests():
    test_files = [
        "./sccb_controller_test.py",
        "./camera_capture_test.py",
        "./vga_controller_test.py",
    ]

    results = {}
    
    print("=" * 70)
    print("OV7670→VGA Pipeline Test Suite")
    print("=" * 70)
    print()

    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            results[test_file] = "SKIP"
            continue

        test_name = Path(test_file).stem
        print(f"Running {test_name}...")
        print("-" * 70)
        
        try:
            results_xml = Path("./sim_build/results.xml")
            if results_xml.exists():
                results_xml.unlink()
            completed = subprocess.run(
                [sys.executable, test_file],
                check=False,
                timeout=420,
            )
            ret = completed.returncode
            has_failures = cocotb_has_failures(results_xml)
            if ret == 0 and not has_failures:
                print(f"✓ {test_name} PASSED\n")
                results[test_file] = "PASS"
            else:
                print(f"✗ {test_name} FAILED (exit code: {ret})\n")
                results[test_file] = "FAIL"
        except subprocess.TimeoutExpired:
            print(f"✗ {test_name} TIMEOUT (>420s)\n")
            results[test_file] = "ERROR"
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}\n")
            results[test_file] = "ERROR"

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_file, status in results.items():
        test_name = Path(test_file).stem
        status_icon = {"PASS": "✓", "FAIL": "✗", "ERROR": "⚠", "SKIP": "⊘"}
        print(f"{status_icon.get(status, '?')} {test_name}: {status}")
    
    print()
    total = len(results)
    passed = sum(1 for s in results.values() if s == "PASS")
    failed = sum(1 for s in results.values() if s == "FAIL")
    errors = sum(1 for s in results.values() if s == "ERROR")
    skipped = sum(1 for s in results.values() if s == "SKIP")
    
    print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Errors: {errors} | Skipped: {skipped}")
    
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
