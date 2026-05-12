#!/usr/bin/env python3
"""
Quick Start: Setup & Run Testbenches

This script helps you:
1. Check if cocotb and simulator are installed
2. Run testbenches with proper environment
3. Generate test reports
"""

import subprocess
import sys
import platform
from pathlib import Path

def check_dependency(cmd, package_name):
    """Check if a command/package is available"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, timeout=5, check=True)
        print(f"✓ {package_name} found")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        print(f"✗ {package_name} NOT found")
        return False

def install_cocotb():
    """Guide user to install cocotb"""
    print("\n" + "="*60)
    print("Installing cocotb and tools...")
    print("="*60)
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-U", "cocotb", "cocotb-tools"], check=True)
        print("✓ cocotb installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install cocotb")
        print("  Try manually: pip install cocotb cocotb-tools")
        return False

def setup():
    """Check dependencies and setup"""
    print("="*60)
    print("OV7670→VGA Pipeline Testbench Setup")
    print("="*60)
    print()
    
    # Check Python
    print(f"Python: {sys.version.split()[0]}")
    
    # Check cocotb
    print("\nChecking dependencies:")
    cocotb_ok = check_dependency("python", "cocotb")
    if not cocotb_ok:
        print("\nAttempting to install cocotb...")
        cocotb_ok = install_cocotb()
    
    # Check simulator
    print("\nChecking simulators:")
    sim_found = False
    
    # Icarus Verilog
    if check_dependency("iverilog", "Icarus Verilog (iverilog)"):
        sim_found = True
    
    # Vivado/xsim
    if platform.system() == "Windows":
        # Try to find Vivado installation
        vivado_paths = [
            "C:\\Xilinx\\Vivado\\*\\bin\\xsim.bat",
            "C:\\Xilinx\\Vivado\\*\\bin\\vivado.exe",
        ]
        for path in vivado_paths:
            if Path(path.replace("*", "2025.2")).exists():
                print("✓ Vivado (xsim) found")
                sim_found = True
                break
    
    if not sim_found:
        print("\n⚠ No simulator found!")
        print("  Install one of:")
        print("  - Icarus Verilog: http://bleyer.org/icarus/")
        print("  - Vivado (includes xsim): https://www.xilinx.com/")
        print("  - VCS, ModelSim, etc.")
    
    print()
    return cocotb_ok and sim_found

def run_tests():
    """Run all testbenches"""
    print("\n" + "="*60)
    print("Running Testbenches")
    print("="*60)
    print()
    
    test_dir = Path(__file__).parent
    
    tests = [
        ("sccb_controller_test.py", "SCCB Controller"),
        ("camera_capture_test.py", "Camera Capture"),
        ("vga_controller_test.py", "VGA Controller"),
    ]
    
    for test_file, description in tests:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"✗ {description} test not found: {test_file}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"{'='*60}")
        
        try:
            # Set simulator (prefer icarus for speed)
            env = {}
            env["SIM"] = "icarus"
            
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=str(test_dir),
                capture_output=False,
                timeout=300  # 5 minute timeout per test
            )
            
            if result.returncode == 0:
                print(f"✓ {description} PASSED")
            else:
                print(f"✗ {description} FAILED (exit code {result.returncode})")
                
        except subprocess.TimeoutExpired:
            print(f"✗ {description} TIMEOUT (exceeded 300s)")
        except Exception as e:
            print(f"✗ {description} ERROR: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OV7670→VGA Testbench Runner")
    parser.add_argument("--setup", action="store_true", help="Run setup/dependency check")
    parser.add_argument("--run", action="store_true", help="Run all testbenches")
    parser.add_argument("--test", type=str, help="Run specific test (sccb/camera/vga)")
    
    args = parser.parse_args()
    
    if args.setup:
        return 0 if setup() else 1
    
    elif args.test:
        test_map = {
            "sccb": "sccb_controller_test.py",
            "camera": "camera_capture_test.py",
            "vga": "vga_controller_test.py",
        }
        test_file = test_map.get(args.test.lower())
        if test_file:
            print(f"Running {test_file}...")
            ret = subprocess.run([sys.executable, test_file], cwd=Path(__file__).parent)
            return ret.returncode
        else:
            print(f"Unknown test: {args.test}")
            print(f"Valid options: {', '.join(test_map.keys())}")
            return 1
    
    elif args.run or len(sys.argv) == 1:
        # Default: setup + run
        if setup():
            run_tests()
            return 0
        else:
            print("\n⚠ Setup incomplete. Fix dependencies and try again.")
            return 1
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
