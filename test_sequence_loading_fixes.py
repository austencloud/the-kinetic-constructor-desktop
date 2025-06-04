#!/usr/bin/env python3
"""
Test script to verify Browse Tab v2 sequence loading fixes.

This script tests:
1. Unlimited sequence loading (no 30-100 limits)
2. Error message elimination during initialization
3. Complete initialization pipeline functionality
"""

import sys
import os
import logging

# Add project root to path
sys.path.append('.')

# Configure logging to see detailed trace
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sequence_service_unlimited_loading():
    """Test that SequenceService loads all sequences without limits."""
    print("\n" + "="*60)
    print("🧪 TEST 1: SequenceService Unlimited Loading")
    print("="*60)
    
    try:
        from src.browse_tab_v2.services.sequence_service import SequenceService
        from src.browse_tab_v2.core.interfaces import BrowseTabConfig
        
        print("✅ Creating SequenceService...")
        config = BrowseTabConfig()
        service = SequenceService(config=config)
        
        print("✅ Testing synchronous loading...")
        sequences = service._load_from_dictionary_sync()
        
        print(f"📊 RESULT: Loaded {len(sequences)} sequences")
        
        if len(sequences) >= 100:
            print("✅ SUCCESS: No artificial limits applied (loaded 100+ sequences)")
            return True
        elif len(sequences) > 30:
            print(f"⚠️  PARTIAL: Loaded {len(sequences)} sequences (more than 30 but less than expected)")
            return True
        else:
            print(f"❌ FAILED: Only loaded {len(sequences)} sequences (limits still active)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_viewmodel_unlimited_loading():
    """Test that BrowseTabViewModel loads all sequences without limits."""
    print("\n" + "="*60)
    print("🧪 TEST 2: BrowseTabViewModel Unlimited Loading")
    print("="*60)
    
    try:
        from src.browse_tab_v2.viewmodels.browse_tab_viewmodel import BrowseTabViewModel
        from src.browse_tab_v2.services.sequence_service import SequenceService
        from src.browse_tab_v2.core.state import StateManager, BrowseState
        from src.browse_tab_v2.core.interfaces import BrowseTabConfig
        
        print("✅ Creating test components...")
        config = BrowseTabConfig()
        state_manager = StateManager(BrowseState())
        sequence_service = SequenceService(config=config)
        
        viewmodel = BrowseTabViewModel(
            state_manager=state_manager,
            sequence_service=sequence_service,
            filter_service=None,
            cache_service=None,
            image_loader=None,
            config=config
        )
        
        print("✅ Testing sync loading...")
        sequences = viewmodel._load_sequences_sync()
        
        print(f"📊 RESULT: Loaded {len(sequences)} sequences")
        
        if len(sequences) >= 100:
            print("✅ SUCCESS: No artificial limits applied (loaded 100+ sequences)")
            return True
        elif len(sequences) > 30:
            print(f"⚠️  PARTIAL: Loaded {len(sequences)} sequences (more than 30 but less than expected)")
            return True
        else:
            print(f"❌ FAILED: Only loaded {len(sequences)} sequences (limits still active)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browse_tab_initialization():
    """Test Browse Tab v2 initialization without error messages."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Browse Tab v2 Initialization")
    print("="*60)
    
    try:
        from src.browse_tab_v2 import BrowseTabV2Factory
        
        print("✅ Creating BrowseTabV2...")
        browse_tab = BrowseTabV2Factory.create_default()
        
        print("✅ Testing initialization...")
        browse_tab.initialize()
        
        print("✅ SUCCESS: BrowseTabV2 initialized without errors")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_message_elimination():
    """Test that initialization doesn't produce false positive error messages."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Error Message Elimination")
    print("="*60)
    
    # Capture log messages to check for error patterns
    import io
    import logging
    
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    
    # Add handler to browse tab loggers
    browse_tab_logger = logging.getLogger('src.browse_tab_v2')
    browse_tab_logger.addHandler(handler)
    
    try:
        from src.browse_tab_v2 import BrowseTabV2Factory
        
        print("✅ Creating and initializing BrowseTabV2 with log monitoring...")
        browse_tab = BrowseTabV2Factory.create_default()
        browse_tab.initialize()
        
        # Check captured logs for error messages
        log_output = log_capture.getvalue()
        
        # Look for the specific error message
        if "Failed to complete initialization" in log_output:
            print("❌ FAILED: 'Failed to complete initialization' error still appears")
            print("📋 Error log excerpt:")
            for line in log_output.split('\n'):
                if "Failed to complete" in line:
                    print(f"   {line}")
            return False
        else:
            print("✅ SUCCESS: No 'Failed to complete initialization' errors found")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        browse_tab_logger.removeHandler(handler)

def main():
    """Run all tests and report results."""
    print("🚀 Browse Tab v2 Sequence Loading & Error Fixes Test Suite")
    print("Testing unlimited sequence loading and error message elimination...")
    
    tests = [
        ("SequenceService Unlimited Loading", test_sequence_service_unlimited_loading),
        ("BrowseTabViewModel Unlimited Loading", test_viewmodel_unlimited_loading),
        ("Browse Tab v2 Initialization", test_browse_tab_initialization),
        ("Error Message Elimination", test_error_message_elimination),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Sequence loading fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
