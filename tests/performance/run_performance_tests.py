#!/usr/bin/env python3
"""
Quick Performance Test Runner for Browse Tab v2

This script provides convenient shortcuts for running specific performance tests
and integrates with the main stress test suite.

Usage:
    python run_performance_tests.py widget-speed
    python run_performance_tests.py navigation-speed
    python run_performance_tests.py thumbnail-speed
    python run_performance_tests.py scroll-stability
    python run_performance_tests.py memory-check
    python run_performance_tests.py full-suite
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Test configurations
TEST_CONFIGS = {
    'widget-speed': {
        'description': 'Test widget creation speed (target: <50ms)',
        'args': ['--widget-creation'],
        'focus': 'ModernThumbnailCard creation performance'
    },
    'navigation-speed': {
        'description': 'Test navigation responsiveness (target: <100ms)',
        'args': ['--navigation'],
        'focus': 'Section button click response time'
    },
    'thumbnail-speed': {
        'description': 'Test thumbnail interaction speed (target: <200ms)',
        'args': ['--thumbnails'],
        'focus': 'Thumbnail click to sequence viewer display'
    },
    'scroll-stability': {
        'description': 'Test scroll performance regression (target: 0ms frame drops)',
        'args': ['--scroll-regression'],
        'focus': 'Scroll event handling without performance cascades'
    },
    'memory-check': {
        'description': 'Test memory usage and leak detection',
        'args': ['--memory-stress'],
        'focus': 'Memory consumption and cleanup efficiency'
    },
    'multi-action': {
        'description': 'Test concurrent user actions',
        'args': ['--multi-action'],
        'focus': 'Simultaneous scroll, navigation, and thumbnail interactions'
    },
    'full-suite': {
        'description': 'Run complete stress test suite (all tests)',
        'args': ['--all'],
        'focus': 'Comprehensive performance analysis'
    },
    'quick-check': {
        'description': 'Quick performance check (reduced test set)',
        'args': ['--widget-creation', '--navigation', '--thumbnails', '--quick'],
        'focus': 'Fast validation of core performance metrics'
    }
}


def print_available_tests():
    """Print available test configurations."""
    print("Available Performance Tests:")
    print("=" * 50)
    for test_name, config in TEST_CONFIGS.items():
        print(f"{test_name:15} - {config['description']}")
        print(f"{'':15}   Focus: {config['focus']}")
        print()


def run_test(test_name: str, additional_args: List[str] = None) -> int:
    """Run specified performance test."""
    if test_name not in TEST_CONFIGS:
        print(f"Error: Unknown test '{test_name}'")
        print_available_tests()
        return 1
        
    config = TEST_CONFIGS[test_name]
    
    print(f"Running Performance Test: {test_name}")
    print(f"Description: {config['description']}")
    print(f"Focus: {config['focus']}")
    print("-" * 60)
    
    # Build command
    script_path = Path(__file__).parent / "stress_test_suite.py"
    cmd = [sys.executable, str(script_path)] + config['args']
    
    if additional_args:
        cmd.extend(additional_args)
        
    # Execute test
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        return 130
    except Exception as e:
        print(f"Error running test: {e}")
        return 1


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python run_performance_tests.py <test_name> [additional_args...]")
        print()
        print_available_tests()
        return 1
        
    test_name = sys.argv[1]
    additional_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    if test_name in ['--help', '-h', 'help']:
        print_available_tests()
        return 0
        
    return run_test(test_name, additional_args)


if __name__ == "__main__":
    sys.exit(main())
