#!/usr/bin/env python3
"""
Comprehensive test runner for sequence generation system.

This script runs all sequence generation tests and provides detailed reporting
on the health of the sequence generation system.
"""

import sys
import os
import unittest
import logging
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_test_suite():
    """Run the complete sequence generation test suite."""
    print("=" * 80)
    print("SEQUENCE GENERATION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test modules
    test_modules = [
        'test_sequence_generation_comprehensive',
        'test_image_generation_workflow'
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for module_name in test_modules:
        print(f"Loading tests from {module_name}...")
        try:
            # Import the test module
            test_module = __import__(module_name)
            
            # Load tests from the module
            module_suite = test_loader.loadTestsFromModule(test_module)
            test_suite.addTest(module_suite)
            
            # Count tests
            test_count = module_suite.countTestCases()
            total_tests += test_count
            print(f"  ✓ Loaded {test_count} tests from {module_name}")
            
        except Exception as e:
            print(f"  ✗ Failed to load tests from {module_name}: {e}")
            traceback.print_exc()
    
    print(f"\nTotal tests loaded: {total_tests}")
    print("-" * 80)
    
    # Run the tests
    if total_tests > 0:
        # Capture test output
        test_output = StringIO()
        test_errors = StringIO()
        
        with redirect_stdout(test_output), redirect_stderr(test_errors):
            runner = unittest.TextTestRunner(
                stream=test_output,
                verbosity=2,
                buffer=True
            )
            result = runner.run(test_suite)
        
        # Print results
        print("TEST RESULTS:")
        print("-" * 40)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        # Print detailed output
        output_content = test_output.getvalue()
        error_content = test_errors.getvalue()
        
        if output_content:
            print("\nTEST OUTPUT:")
            print("-" * 40)
            print(output_content)
        
        if error_content:
            print("\nTEST ERRORS:")
            print("-" * 40)
            print(error_content)
        
        # Print failure details
        if result.failures:
            print("\nFAILURE DETAILS:")
            print("-" * 40)
            for test, failure in result.failures:
                print(f"\nFAILED: {test}")
                print(failure)
        
        # Print error details
        if result.errors:
            print("\nERROR DETAILS:")
            print("-" * 40)
            for test, error in result.errors:
                print(f"\nERROR: {test}")
                print(error)
        
        # Summary
        print("\n" + "=" * 80)
        if result.wasSuccessful():
            print("✓ ALL TESTS PASSED!")
            print("The sequence generation system is working correctly.")
        else:
            print("✗ SOME TESTS FAILED!")
            print("The sequence generation system has issues that need to be addressed.")
            
            # Provide specific guidance
            if any("'GeneratedSequenceData' object has no attribute 'beats'" in str(failure) 
                   for _, failure in result.failures + result.errors):
                print("\n⚠️  CRITICAL BUG DETECTED:")
                print("   The 'beats' attribute error is still present in the codebase.")
                print("   This indicates the fix was not applied correctly or there are")
                print("   additional locations that need to be updated.")
        
        print("=" * 80)
        
        return result.wasSuccessful()
    
    else:
        print("No tests were loaded. Please check the test modules.")
        return False


def validate_fix():
    """Validate that the critical AttributeError fix is working."""
    print("\nVALIDATING CRITICAL BUG FIX:")
    print("-" * 40)
    
    try:
        # Test the fix directly
        from main_window.main_widget.sequence_card_tab.generation.generated_sequence_data import GeneratedSequenceData
        from main_window.main_widget.sequence_card_tab.generation.generation_params import GenerationParams
        
        # Create test data
        params = GenerationParams(
            length=4,
            level=1,
            generation_mode="circular",
            prop_continuity="continuous",
            turn_intensity=3,
            CAP_type="rotated"
        )
        
        sequence_data = [
            {"word": "TEST", "author": "test", "level": 1},
            {"sequence_start_position": True},
            {"beat": 1, "letter": "T"},
            {"beat": 2, "letter": "E"},
        ]
        
        generated_data = GeneratedSequenceData(sequence_data, params)
        
        # Test that sequence_data attribute exists and works
        assert hasattr(generated_data, 'sequence_data'), "sequence_data attribute missing"
        assert generated_data.sequence_data == sequence_data, "sequence_data not stored correctly"
        
        # Test that beats attribute does NOT exist (this should raise AttributeError)
        try:
            _ = generated_data.beats
            print("✗ CRITICAL: beats attribute still exists - this should not happen!")
            return False
        except AttributeError:
            print("✓ Confirmed: beats attribute correctly does not exist")
        
        print("✓ GeneratedSequenceData structure is correct")
        print("✓ Critical bug fix is working properly")
        return True
        
    except Exception as e:
        print(f"✗ Error validating fix: {e}")
        traceback.print_exc()
        return False


def main():
    """Main test runner function."""
    print("Starting sequence generation system validation...")
    
    # First validate the critical fix
    fix_valid = validate_fix()
    
    # Then run the comprehensive test suite
    tests_passed = run_test_suite()
    
    # Final summary
    print("\nFINAL VALIDATION SUMMARY:")
    print("-" * 40)
    print(f"Critical bug fix: {'✓ WORKING' if fix_valid else '✗ FAILED'}")
    print(f"Test suite: {'✓ PASSED' if tests_passed else '✗ FAILED'}")
    
    if fix_valid and tests_passed:
        print("\n🎉 SUCCESS: Sequence generation system is fully functional!")
        return 0
    else:
        print("\n❌ FAILURE: Issues detected in sequence generation system.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
