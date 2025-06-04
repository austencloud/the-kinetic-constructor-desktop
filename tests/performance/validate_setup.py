#!/usr/bin/env python3
"""
Setup Validation Script for Browse Tab v2 Performance Stress Test Suite

This script validates that all dependencies and components are properly configured
for running the performance stress tests.

Usage:
    python validate_setup.py
"""

import sys
import importlib
from pathlib import Path
from typing import List, Tuple, Dict, Any

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        return False, f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}"
    return True, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def check_required_packages() -> List[Tuple[str, bool, str]]:
    """Check if required packages are available."""
    required_packages = [
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets', 
        'PyQt6.QtTest',
        'psutil',
        'json',
        'csv',
        'argparse',
        'logging',
        'datetime',
        'pathlib',
        'dataclasses'
    ]
    
    results = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            results.append((package, True, "Available"))
        except ImportError as e:
            results.append((package, False, f"Missing: {e}"))
    
    return results

def check_browse_tab_modules() -> List[Tuple[str, bool, str]]:
    """Check if browse tab v2 modules are importable."""
    # Add src to path
    src_path = Path(__file__).parent.parent.parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    
    browse_modules = [
        'browse_tab_v2.browse_tab_v2',
        'browse_tab_v2.components.modern_thumbnail_card',
        'browse_tab_v2.components.modern_sequence_viewer',
        'browse_tab_v2.components.efficient_virtual_grid',
        'browse_tab_v2.services.sequence_service',
        'browse_tab_v2.services.cache_service',
        'browse_tab_v2.services.fast_image_service'
    ]
    
    results = []
    for module in browse_modules:
        try:
            importlib.import_module(module)
            results.append((module, True, "Available"))
        except ImportError as e:
            results.append((module, False, f"Missing: {e}"))
    
    return results

def check_file_structure() -> List[Tuple[str, bool, str]]:
    """Check if required files exist."""
    base_path = Path(__file__).parent
    required_files = [
        'stress_test_suite.py',
        'run_performance_tests.py',
        'test_config.json',
        'README.md'
    ]
    
    results = []
    for file_name in required_files:
        file_path = base_path / file_name
        if file_path.exists():
            results.append((file_name, True, f"Found at {file_path}"))
        else:
            results.append((file_name, False, f"Missing: {file_path}"))
    
    return results

def check_output_directory() -> Tuple[bool, str]:
    """Check if output directory can be created."""
    try:
        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)
        
        # Test write permissions
        test_file = output_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
        return True, f"Output directory ready: {output_dir.absolute()}"
    except Exception as e:
        return False, f"Cannot create output directory: {e}"

def validate_test_config() -> Tuple[bool, str]:
    """Validate test configuration file."""
    try:
        import json
        config_path = Path(__file__).parent / "test_config.json"
        
        if not config_path.exists():
            return False, "test_config.json not found"
            
        with open(config_path) as f:
            config = json.load(f)
            
        # Check required sections
        required_sections = [
            'performance_targets',
            'test_parameters', 
            'output_settings',
            'integration_settings'
        ]
        
        missing_sections = [s for s in required_sections if s not in config]
        if missing_sections:
            return False, f"Missing config sections: {missing_sections}"
            
        return True, "Configuration file valid"
    except Exception as e:
        return False, f"Configuration validation failed: {e}"

def run_basic_qt_test() -> Tuple[bool, str]:
    """Test basic Qt functionality."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # Create minimal Qt application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        # Test timer functionality
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: None)
        timer.start(1)
        
        # Process events briefly
        app.processEvents()
        
        return True, "Qt functionality working"
    except Exception as e:
        return False, f"Qt test failed: {e}"

def print_section(title: str, results: List[Tuple[str, bool, str]]):
    """Print a validation section."""
    print(f"\n{title}")
    print("=" * len(title))
    
    for name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {name:30} - {message}")

def main():
    """Main validation function."""
    print("Browse Tab v2 Performance Stress Test Suite - Setup Validation")
    print("=" * 70)
    
    all_passed = True
    
    # Check Python version
    python_ok, python_msg = check_python_version()
    print(f"\nPython Version: {'✅' if python_ok else '❌'} {python_msg}")
    if not python_ok:
        all_passed = False
    
    # Check required packages
    package_results = check_required_packages()
    print_section("Required Packages", package_results)
    if not all(result[1] for result in package_results):
        all_passed = False
    
    # Check browse tab modules
    module_results = check_browse_tab_modules()
    print_section("Browse Tab v2 Modules", module_results)
    if not all(result[1] for result in module_results):
        all_passed = False
        print("\n⚠️  Browse tab modules not found. This is expected if running outside the main application.")
        print("   The stress test suite will need to be run from the main application context.")
    
    # Check file structure
    file_results = check_file_structure()
    print_section("Required Files", file_results)
    if not all(result[1] for result in file_results):
        all_passed = False
    
    # Check output directory
    output_ok, output_msg = check_output_directory()
    print(f"\nOutput Directory: {'✅' if output_ok else '❌'} {output_msg}")
    if not output_ok:
        all_passed = False
    
    # Check configuration
    config_ok, config_msg = validate_test_config()
    print(f"Configuration: {'✅' if config_ok else '❌'} {config_msg}")
    if not config_ok:
        all_passed = False
    
    # Test Qt functionality
    qt_ok, qt_msg = run_basic_qt_test()
    print(f"Qt Functionality: {'✅' if qt_ok else '❌'} {qt_msg}")
    if not qt_ok:
        all_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ Setup validation PASSED - Ready to run performance tests!")
        print("\nNext steps:")
        print("  python run_performance_tests.py quick-check")
        print("  python stress_test_suite.py --all")
    else:
        print("❌ Setup validation FAILED - Please fix the issues above")
        print("\nCommon solutions:")
        print("  pip install PyQt6 psutil")
        print("  Ensure you're running from the correct directory")
        print("  Check that browse tab v2 modules are available")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
