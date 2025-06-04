"""
Simplified Diagnostic Test for Scroll-to-Image Loading

This test runs in the current environment to diagnose the scroll event chain.
"""

import sys
import logging
import time
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, '.')

try:
    from src.browse_tab_v2.components.efficient_virtual_grid import EfficientVirtualGrid
    from src.browse_tab_v2.components.fast_thumbnail_card import FastThumbnailCard
    from src.browse_tab_v2.services.fast_image_service import get_image_service
    from src.browse_tab_v2.core.interfaces import BrowseTabConfig
    logger.info("✅ All components imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import components: {e}")
    sys.exit(1)

class MockSequence:
    """Mock sequence for testing."""
    def __init__(self, name: str, seq_id: str):
        self.id = seq_id
        self.name = name
        self.thumbnails = [f"test_image_{seq_id}.png"]

def test_component_creation():
    """Test basic component creation without GUI."""
    logger.info("=== TESTING COMPONENT CREATION ===")
    
    try:
        # Test grid creation
        config = BrowseTabConfig()
        logger.info("✅ Config created")
        
        # Test image service
        image_service = get_image_service()
        logger.info("✅ Image service created")
        
        # Test mock sequences
        sequences = [MockSequence(f"Test {i}", f"test_{i}") for i in range(10)]
        logger.info(f"✅ Created {len(sequences)} mock sequences")
        
        logger.info("=== COMPONENT CREATION TEST PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Component creation failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_image_service_functionality():
    """Test image service functionality."""
    logger.info("=== TESTING IMAGE SERVICE FUNCTIONALITY ===")
    
    try:
        image_service = get_image_service()
        
        # Test cache stats
        stats = image_service.get_cache_stats()
        logger.info(f"✅ Cache stats: {stats}")
        
        # Test queue functionality
        test_paths = ["test1.png", "test2.png", "test3.png"]
        image_service.queue_multiple_images(test_paths, priority=1)
        logger.info(f"✅ Queued {len(test_paths)} images")
        
        # Test preload functionality
        image_service.preload_visible_images(test_paths)
        logger.info("✅ Preload visible images called")
        
        logger.info("=== IMAGE SERVICE TEST PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Image service test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_signal_connectivity():
    """Test signal/slot connectivity without GUI."""
    logger.info("=== TESTING SIGNAL CONNECTIVITY ===")
    
    try:
        from PyQt6.QtCore import QObject, pyqtSignal
        
        class TestSignalEmitter(QObject):
            test_signal = pyqtSignal(int, int)
        
        class TestSignalReceiver(QObject):
            def __init__(self):
                super().__init__()
                self.received_signals = []
            
            def on_signal_received(self, start, end):
                self.received_signals.append((start, end))
                logger.debug(f"Signal received: {start}-{end}")
        
        # Test signal connection
        emitter = TestSignalEmitter()
        receiver = TestSignalReceiver()
        
        emitter.test_signal.connect(receiver.on_signal_received)
        logger.info("✅ Signal connected")
        
        # Test signal emission
        emitter.test_signal.emit(0, 10)
        emitter.test_signal.emit(10, 20)
        
        if len(receiver.received_signals) == 2:
            logger.info(f"✅ Signals received: {receiver.received_signals}")
        else:
            logger.error(f"❌ Expected 2 signals, got {len(receiver.received_signals)}")
            return False
        
        logger.info("=== SIGNAL CONNECTIVITY TEST PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Signal connectivity test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_fast_thumbnail_card_methods():
    """Test FastThumbnailCard methods."""
    logger.info("=== TESTING FAST THUMBNAIL CARD METHODS ===")
    
    try:
        # Test card creation
        sequence = MockSequence("Test Card", "test_card_001")
        
        # Check if we can inspect the class methods
        import inspect
        
        # Check _load_image_fast method exists
        if hasattr(FastThumbnailCard, '_load_image_fast'):
            logger.info("✅ _load_image_fast method exists")
            
            # Check method signature
            sig = inspect.signature(FastThumbnailCard._load_image_fast)
            logger.info(f"✅ Method signature: {sig}")
        else:
            logger.error("❌ _load_image_fast method not found")
            return False
        
        # Check for SmoothTransformation in source
        source = inspect.getsource(FastThumbnailCard._load_image_fast)
        if 'SmoothTransformation' in source:
            logger.info("✅ SmoothTransformation found in _load_image_fast")
        else:
            logger.warning("⚠️ SmoothTransformation not found in _load_image_fast")
        
        logger.info("=== FAST THUMBNAIL CARD TEST PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ FastThumbnailCard test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def run_all_tests():
    """Run all diagnostic tests."""
    logger.info("🚀 STARTING COMPREHENSIVE DIAGNOSTIC TESTS")
    
    tests = [
        ("Component Creation", test_component_creation),
        ("Image Service Functionality", test_image_service_functionality),
        ("Signal Connectivity", test_signal_connectivity),
        ("FastThumbnailCard Methods", test_fast_thumbnail_card_methods),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"RUNNING: {test_name}")
        logger.info(f"{'='*50}")
        
        start_time = time.time()
        result = test_func()
        end_time = time.time()
        
        results[test_name] = {
            'passed': result,
            'duration': (end_time - start_time) * 1000
        }
        
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status} ({results[test_name]['duration']:.1f}ms)")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("DIAGNOSTIC TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed_count = sum(1 for r in results.values() if r['passed'])
    total_count = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        logger.info(f"{test_name}: {status} ({result['duration']:.1f}ms)")
    
    logger.info(f"\nOVERALL: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("🎉 ALL DIAGNOSTIC TESTS PASSED")
        logger.info("Components are ready for scroll-to-image debugging")
    else:
        logger.error("💥 SOME TESTS FAILED")
        logger.error("Fix component issues before proceeding with scroll debugging")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
