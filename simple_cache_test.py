#!/usr/bin/env python3
"""
Simple test to check browse cache functionality without full app startup.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if we can import the cache modules."""
    print("Testing imports...")
    
    try:
        # Test sequence card cache import
        from main_window.main_widget.sequence_card_tab.utils.cache_utils import ThumbnailCache
        print("✅ ThumbnailCache imported successfully")
        
        # Test browse cache import
        from main_window.main_widget.browse_tab.cache.browse_image_cache import (
            BrowseImageCache, get_browse_cache
        )
        print("✅ BrowseImageCache imported successfully")
        
        # Test ImageLoadingManager import
        from main_window.main_widget.browse_tab.thumbnail_box.components.image_loading_manager import (
            BROWSE_CACHE_AVAILABLE
        )
        print(f"✅ ImageLoadingManager imported, cache available: {BROWSE_CACHE_AVAILABLE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_creation():
    """Test creating cache instances."""
    print("\nTesting cache creation...")
    
    try:
        from main_window.main_widget.browse_tab.cache.browse_image_cache import (
            BrowseImageCache, get_browse_cache
        )
        
        # Test direct creation
        cache1 = BrowseImageCache(cache_size=100)
        print(f"✅ Direct cache creation: {cache1}")
        
        # Test global instance
        cache2 = get_browse_cache()
        print(f"✅ Global cache instance: {cache2}")
        
        # Test cache properties
        print(f"   Cache1 size: {cache1.thumbnail_cache.max_size}")
        print(f"   Cache2 size: {cache2.thumbnail_cache.max_size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_loading_integration():
    """Test ImageLoadingManager integration."""
    print("\nTesting ImageLoadingManager integration...")
    
    try:
        from main_window.main_widget.browse_tab.thumbnail_box.components.image_loading_manager import (
            ImageLoadingManager, BROWSE_CACHE_AVAILABLE
        )
        
        print(f"   Browse cache available: {BROWSE_CACHE_AVAILABLE}")
        
        if BROWSE_CACHE_AVAILABLE:
            from main_window.main_widget.browse_tab.cache.browse_image_cache import get_browse_cache
            cache = get_browse_cache()
            print(f"   Cache accessible: {cache is not None}")
            
            # Test cache stats
            stats = cache.get_cache_stats()
            print(f"   Initial cache stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ ImageLoadingManager integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_browse_tab_structure():
    """Analyze the browse tab structure to understand caching flow."""
    print("\nAnalyzing browse tab structure...")
    
    try:
        # Check if browse tab files exist
        browse_tab_path = Path("src/main_window/main_widget/browse_tab")
        
        print(f"   Browse tab directory: {browse_tab_path.exists()}")
        
        # Check key files
        key_files = [
            "browse_tab.py",
            "cache/browse_image_cache.py",
            "thumbnail_box/components/image_loading_manager.py",
            "ui_updater.py",
            "modern_progress_bar.py"
        ]
        
        for file_path in key_files:
            full_path = browse_tab_path / file_path
            exists = full_path.exists()
            print(f"   {file_path}: {'✅' if exists else '❌'}")
        
        # Check cache directory
        cache_dir = Path("browse_thumbnails")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.png"))
            print(f"   Cache directory: ✅ ({len(cache_files)} cached images)")
        else:
            print(f"   Cache directory: ❌ (not found)")
        
        return True
        
    except Exception as e:
        print(f"❌ Structure analysis error: {e}")
        return False

def main():
    """Main test function."""
    print("🔍 Simple Browse Cache Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Cache Creation Test", test_cache_creation),
        ("ImageLoadingManager Integration", test_image_loading_integration),
        ("Browse Tab Structure Analysis", analyze_browse_tab_structure),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
