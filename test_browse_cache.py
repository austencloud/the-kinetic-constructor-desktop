#!/usr/bin/env python3
"""
Test script to verify browse tab image caching functionality.
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_browse_cache():
    """Test the browse image cache functionality."""
    print("🔍 Testing Browse Tab Image Cache...")
    
    try:
        # Import the browse cache
        from main_window.main_widget.browse_tab.cache.browse_image_cache import (
            get_browse_cache, BrowseImageCache
        )
        
        print("✅ Successfully imported browse cache modules")
        
        # Create cache instance
        cache = get_browse_cache()
        print(f"✅ Created cache instance: {cache}")
        print(f"   Cache size: {cache.thumbnail_cache.max_size}")
        print(f"   Total requests: {cache.total_requests}")
        print(f"   Cache hits: {cache.cache_hits}")
        print(f"   Cache misses: {cache.cache_misses}")
        
        # Test cache statistics
        cache_stats = cache.get_cache_stats()
        print(f"✅ Cache statistics: {cache_stats}")
        
        # Test with a sample image if available
        test_image_path = "test_image.png"
        if os.path.exists(test_image_path):
            print(f"🖼️ Testing with sample image: {test_image_path}")
            
            # Test cache miss (first load)
            size = QSize(200, 200)
            cached_image = cache.get_cached_image(test_image_path, size)
            print(f"   First load (should be miss): {cached_image is not None}")
            
            # Test loading and caching
            loaded_image = cache.load_and_cache_image(test_image_path, size)
            print(f"   Load and cache: {loaded_image is not None}")
            
            # Test cache hit (second load)
            cached_image2 = cache.get_cached_image(test_image_path, size)
            print(f"   Second load (should be hit): {cached_image2 is not None}")
            
            # Print updated stats
            print(f"   Updated stats - Hits: {cache.cache_hits}, Misses: {cache.cache_misses}")
        else:
            print(f"⚠️ No test image found at {test_image_path}")
        
        # Test batch operations
        print("🔄 Testing batch operations...")
        image_paths = []
        for cache_file in Path("browse_thumbnails").glob("*.png"):
            image_paths.append(str(cache_file))
            if len(image_paths) >= 5:  # Test with 5 images
                break
        
        if image_paths:
            print(f"   Testing with {len(image_paths)} cached images")
            size = QSize(150, 150)
            
            # Test batch retrieval
            batch_results = cache.get_batch_cached_images(image_paths, size)
            print(f"   Batch cache hits: {len(batch_results)}/{len(image_paths)}")
            
            # Load missing images
            for path in image_paths:
                if path not in batch_results:
                    loaded = cache.load_and_cache_image(path, size)
                    if loaded:
                        print(f"   ✅ Loaded and cached: {os.path.basename(path)}")
            
            # Test batch retrieval again
            batch_results2 = cache.get_batch_cached_images(image_paths, size)
            print(f"   Second batch cache hits: {len(batch_results2)}/{len(image_paths)}")
        
        # Final statistics
        final_stats = cache.get_cache_stats()
        print(f"🏁 Final cache statistics: {final_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing browse cache: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_loading_manager():
    """Test the ImageLoadingManager integration with browse cache."""
    print("\n🔍 Testing ImageLoadingManager Cache Integration...")
    
    try:
        from main_window.main_widget.browse_tab.thumbnail_box.components.image_loading_manager import (
            ImageLoadingManager
        )
        
        print("✅ Successfully imported ImageLoadingManager")
        
        # Create a mock parent for testing
        class MockParent:
            def __init__(self):
                pass
        
        parent = MockParent()
        manager = ImageLoadingManager(parent)
        print(f"✅ Created ImageLoadingManager: {manager}")
        
        # Test if browse cache is available
        from main_window.main_widget.browse_tab.thumbnail_box.components.image_loading_manager import (
            BROWSE_CACHE_AVAILABLE
        )
        print(f"   Browse cache available: {BROWSE_CACHE_AVAILABLE}")
        
        if BROWSE_CACHE_AVAILABLE:
            from main_window.main_widget.browse_tab.cache.browse_image_cache import get_browse_cache
            cache = get_browse_cache()
            print(f"   Cache instance accessible: {cache is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ImageLoadingManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Browse Tab Cache Testing Suite")
    print("=" * 50)
    
    # Create QApplication for Qt operations
    app = QApplication(sys.argv)
    
    # Run tests
    cache_test_passed = test_browse_cache()
    manager_test_passed = test_image_loading_manager()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Browse Cache Test: {'✅ PASSED' if cache_test_passed else '❌ FAILED'}")
    print(f"   ImageLoadingManager Test: {'✅ PASSED' if manager_test_passed else '❌ FAILED'}")
    
    overall_success = cache_test_passed and manager_test_passed
    print(f"   Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
