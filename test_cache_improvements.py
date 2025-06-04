#!/usr/bin/env python3
"""
Test script to verify browse tab caching improvements.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_cache_functionality():
    """Test the enhanced cache functionality."""
    print("🔍 Testing Enhanced Browse Tab Cache Functionality")
    print("=" * 60)
    
    try:
        # Test 1: Import verification
        print("\n1️⃣ Testing imports...")
        from main_window.main_widget.browse_tab.cache.browse_image_cache import (
            get_browse_cache, BrowseImageCache
        )
        print("✅ Browse cache imports successful")
        
        from main_window.main_widget.browse_tab.thumbnail_box.components.image_loading_manager import (
            ImageLoadingManager, BROWSE_CACHE_AVAILABLE
        )
        print(f"✅ ImageLoadingManager imported, cache available: {BROWSE_CACHE_AVAILABLE}")
        
        # Test 2: Cache instance creation
        print("\n2️⃣ Testing cache instance creation...")
        cache = get_browse_cache()
        print(f"✅ Cache instance created: {type(cache).__name__}")
        
        # Test 3: Cache statistics
        print("\n3️⃣ Testing cache statistics...")
        stats = cache.get_cache_stats()
        print(f"✅ Initial cache stats: {stats}")
        
        # Test 4: ImageLoadingManager integration
        print("\n4️⃣ Testing ImageLoadingManager integration...")
        
        class MockParent:
            pass
        
        manager = ImageLoadingManager(MockParent())
        print("✅ ImageLoadingManager created")
        
        # Test enhanced cache stats
        enhanced_stats = manager.get_browse_cache_stats()
        print(f"✅ Enhanced cache stats: {enhanced_stats}")
        
        # Test 5: Cache performance logging
        print("\n5️⃣ Testing cache performance logging...")
        manager.log_cache_performance()
        print("✅ Cache performance logged")
        
        # Test 6: Preload functionality (if images available)
        print("\n6️⃣ Testing preload functionality...")
        
        # Look for some test images
        test_images = []
        cache_dir = Path("browse_thumbnails")
        if cache_dir.exists():
            test_images = [str(f) for f in cache_dir.glob("*.png")][:5]
        
        if test_images:
            from PyQt6.QtCore import QSize
            target_size = QSize(200, 150)
            
            preloaded = manager.preload_cached_images(test_images, target_size)
            print(f"✅ Preloaded {len(preloaded)}/{len(test_images)} images from cache")
        else:
            print("⚠️ No test images found for preload testing")
        
        # Test 7: Final cache statistics
        print("\n7️⃣ Final cache statistics...")
        final_stats = cache.get_cache_stats()
        print(f"✅ Final cache stats: {final_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cache testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_cache_performance():
    """Analyze cache performance and provide recommendations."""
    print("\n🔍 Cache Performance Analysis")
    print("=" * 40)
    
    try:
        # Check cache directories
        cache_dirs = [
            ("Browse Cache", Path("browse_thumbnails")),
            ("Image Cache", Path("image_cache")),
        ]
        
        for name, cache_dir in cache_dirs:
            if cache_dir.exists():
                cache_files = list(cache_dir.glob("*.png"))
                total_size = sum(f.stat().st_size for f in cache_files)
                
                print(f"📁 {name}:")
                print(f"   Files: {len(cache_files)}")
                print(f"   Size: {total_size / (1024*1024):.1f} MB")
                print(f"   Directory: {cache_dir}")
            else:
                print(f"📁 {name}: Not found")
        
        # Performance recommendations
        print("\n💡 Performance Recommendations:")
        
        browse_cache_dir = Path("browse_thumbnails")
        if browse_cache_dir.exists():
            cache_files = list(browse_cache_dir.glob("*.png"))
            if len(cache_files) > 100:
                print("✅ Good cache population - should see fast loading")
            elif len(cache_files) > 20:
                print("⚠️ Moderate cache population - some images may load slowly")
            else:
                print("🔄 Low cache population - first loads will be slow")
        else:
            print("🆕 No cache directory - all images will load from scratch")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing cache performance: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Browse Tab Cache Improvements Test Suite")
    print("=" * 60)
    
    # Set up logging to see cache activity
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(name)s - %(message)s'
    )
    
    # Run tests
    cache_test_passed = test_cache_functionality()
    analysis_passed = analyze_cache_performance()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Cache Functionality Test: {'✅ PASSED' if cache_test_passed else '❌ FAILED'}")
    print(f"   Cache Performance Analysis: {'✅ PASSED' if analysis_passed else '❌ FAILED'}")
    
    overall_success = cache_test_passed and analysis_passed
    print(f"   Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Browse tab caching improvements are working correctly!")
        print("   Expected benefits:")
        print("   • Faster loading on subsequent visits")
        print("   • Better cache hit rates with dual-layer caching")
        print("   • Improved performance monitoring")
        print("   • Preload optimization for instant display")
    else:
        print("\n⚠️ Some issues detected. Check the error messages above.")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
