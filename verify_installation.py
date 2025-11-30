#!/usr/bin/env python3
"""
Final verification script for GestureCanvas.
Runs all test suites and validates environment setup.
"""

import unittest
import sys
import os
import importlib.util
import subprocess
import time

def check_import(module_name):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def run_test_suite(path):
    """Run a specific test suite."""
    print(f"\nRunning {path}...")
    result = subprocess.run(
        [sys.executable, path],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"✅ {path} PASSED")
        return True
    else:
        print(f"❌ {path} FAILED")
        print(result.stderr)
        return False

def main():
    print("="*60)
    print("GESTURECANVAS FINAL VERIFICATION")
    print("="*60)
    
    # 1. Environment Check
    print("\n[1/3] Checking Environment...")
    required_modules = [
        'cv2', 'mediapipe', 'numpy', 'PIL', 'gradio', 
        'torch', 'diffusers', 'transformers'
    ]
    
    all_modules_ok = True
    for mod in required_modules:
        if check_import(mod):
            print(f"  ✅ {mod:<15} found")
        else:
            print(f"  ❌ {mod:<15} MISSING")
            all_modules_ok = False
    
    if not all_modules_ok:
        print("\n❌ Environment check failed. Please run: pip install -r requirements.txt")
        return
    
    # 2. Component Tests
    print("\n[2/3] Running Test Suites...")
    test_files = [
        'tests/test_unit.py',
        'tests/test_canvas.py',
        'tests/test_style_transfer.py',
        'tests/test_threading.py',
        'tests/test_performance.py'
    ]
    
    all_tests_passed = True
    for test_file in test_files:
        if not run_test_suite(test_file):
            all_tests_passed = False
    
    # 3. File Structure Check
    print("\n[3/3] Checking File Structure...")
    required_files = [
        'app.py', 'canvas.py', 'style_transfer.py', 'threading_manager.py',
        'README.md', 'ARCHITECTURE.md', 'USER_GUIDE.md'
    ]
    
    all_files_ok = True
    for f in required_files:
        if os.path.exists(f):
            print(f"  ✅ {f:<20} found")
        else:
            print(f"  ❌ {f:<20} MISSING")
            all_files_ok = False
            
    print("\n" + "="*60)
    if all_modules_ok and all_tests_passed and all_files_ok:
        print("🎉 VERIFICATION SUCCESSFUL! System is ready for deployment.")
        sys.exit(0)
    else:
        print("❌ VERIFICATION FAILED. Please check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
