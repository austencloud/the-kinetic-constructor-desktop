#!/usr/bin/env python3
"""
Debug script to identify where the application is freezing.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_detailed_logging():
    """Setup very detailed logging to track where the freeze occurs."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug_freeze.log', mode='w')
        ]
    )
    
    # Enable debug logging for specific modules
    debug_modules = [
        'main_window.main_widget.browse_tab.ui_updater',
        'main_window.main_widget.browse_tab.sequence_picker',
        'main_window.main_widget.browse_tab.filter_manager',
        'main_window.main_widget.browse_tab.browse_tab',
    ]
    
    for module in debug_modules:
        logger = logging.getLogger(module)
        logger.setLevel(logging.DEBUG)
    
    print("🔍 Detailed logging enabled")

def add_freeze_detection():
    """Add freeze detection to critical methods."""
    try:
        # Import after setting up logging
        from main_window.main_widget.browse_tab.ui_updater import UIUpdater
        
        # Monkey patch critical methods to add freeze detection
        original_create_and_show = UIUpdater._create_and_show_thumbnails_chunked_sync
        
        def debug_create_and_show(self, skip_scaling=True, total_sequences=None):
            print(f"🚀 ENTERING _create_and_show_thumbnails_chunked_sync")
            print(f"   skip_scaling: {skip_scaling}")
            print(f"   total_sequences: {total_sequences}")
            
            start_time = time.time()
            
            try:
                result = original_create_and_show(self, skip_scaling, total_sequences)
                elapsed = time.time() - start_time
                print(f"✅ COMPLETED _create_and_show_thumbnails_chunked_sync in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ FAILED _create_and_show_thumbnails_chunked_sync after {elapsed:.2f}s: {e}")
                raise
        
        UIUpdater._create_and_show_thumbnails_chunked_sync = debug_create_and_show
        print("✅ Added freeze detection to UIUpdater")
        
    except Exception as e:
        print(f"❌ Failed to add freeze detection: {e}")

def add_filter_detection():
    """Add detection to filter application."""
    try:
        from main_window.main_widget.browse_tab.filter_manager.filter_manager import FilterManager
        
        original_apply_filter = FilterManager.apply_filter
        
        def debug_apply_filter(self, filter_criteria):
            print(f"🔍 ENTERING apply_filter")
            print(f"   filter_criteria: {filter_criteria}")
            
            start_time = time.time()
            
            try:
                result = original_apply_filter(self, filter_criteria)
                elapsed = time.time() - start_time
                print(f"✅ COMPLETED apply_filter in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ FAILED apply_filter after {elapsed:.2f}s: {e}")
                raise
        
        FilterManager.apply_filter = debug_apply_filter
        print("✅ Added freeze detection to FilterManager")
        
    except Exception as e:
        print(f"❌ Failed to add filter detection: {e}")

def main():
    """Main debug function."""
    print("🚀 Starting Freeze Detection Debug")
    print("=" * 50)
    
    # Setup detailed logging
    setup_detailed_logging()
    
    # Add freeze detection
    add_freeze_detection()
    add_filter_detection()
    
    print("\n🔍 Starting application with freeze detection...")
    print("Watch for:")
    print("  - 🚀 ENTERING messages (shows where we enter methods)")
    print("  - ✅ COMPLETED messages (shows successful completion)")
    print("  - ❌ FAILED messages (shows where errors occur)")
    print("  - If you see ENTERING but no COMPLETED, that's where it freezes!")
    print("\n" + "=" * 50)
    
    # Import and run the main application
    try:
        import main
        # The main module will run automatically when imported
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Application crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
