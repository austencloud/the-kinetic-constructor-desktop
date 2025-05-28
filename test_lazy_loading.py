#!/usr/bin/env python3
"""
Test script to verify lazy loading implementation is working.

This script will:
1. Check if ModernThumbnailImageLabel is being used
2. Verify lazy loading components are initialized
3. Test visual feedback systems
4. Show debug information about the implementation
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging to see our debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """Test that all our new components can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from main_window.main_widget.browse_tab.thumbnail_box.modern_thumbnail_image_label import ModernThumbnailImageLabel
        print("✅ ModernThumbnailImageLabel imported successfully")
        
        from main_window.main_widget.browse_tab.lazy_loading.browse_tab_lazy_loader import BrowseTabLazyLoader
        print("✅ BrowseTabLazyLoader imported successfully")
        
        from main_window.main_widget.browse_tab.lazy_loading.loading_indicator import LoadingIndicator
        print("✅ LoadingIndicator imported successfully")
        
        from main_window.main_widget.browse_tab.lazy_loading.viewport_manager import ViewportManager
        print("✅ ViewportManager imported successfully")
        
        from main_window.main_widget.browse_tab.thumbnail_box.components import (
            ImageLoadingManager, VisualStateManager, LazyLoadingCoordinator
        )
        print("✅ All component managers imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_backward_compatibility():
    """Test that backward compatibility wrapper works."""
    print("\n🔄 Testing backward compatibility...")
    
    try:
        from main_window.main_widget.browse_tab.thumbnail_box.thumbnail_image_label import ThumbnailImageLabel
        from main_window.main_widget.browse_tab.thumbnail_box.modern_thumbnail_image_label import ModernThumbnailImageLabel
        
        # Check if they're the same class
        if ThumbnailImageLabel is ModernThumbnailImageLabel:
            print("✅ Backward compatibility wrapper working correctly")
            return True
        else:
            print("❌ Backward compatibility wrapper not working")
            return False
            
    except ImportError as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def test_glassmorphism_styling():
    """Test that glassmorphism styling is available."""
    print("\n🎨 Testing glassmorphism styling...")
    
    try:
        from styles.glassmorphism_styler import GlassmorphismStyler
        
        # Test creating a glassmorphism card
        style = GlassmorphismStyler.create_glassmorphism_card(
            None, blur_radius=20, opacity=0.12, border_radius=14
        )
        
        if style and "background-color" in style:
            print("✅ Glassmorphism styling working correctly")
            return True
        else:
            print("❌ Glassmorphism styling not generating CSS")
            return False
            
    except Exception as e:
        print(f"❌ Glassmorphism styling test failed: {e}")
        return False

def test_component_architecture():
    """Test that the component architecture is working."""
    print("\n🏗️ Testing component architecture...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QLabel
        from PyQt6.QtCore import QSize
        
        # Create a minimal QApplication if none exists
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create a mock thumbnail box
        class MockThumbnailBox:
            def __init__(self):
                self.in_sequence_viewer = False
                self.margin = 10
                
                # Mock sequence picker
                class MockSequencePicker:
                    def __init__(self):
                        class MockScrollWidget:
                            def width(self):
                                return 800
                            def calculate_scrollbar_width(self):
                                return 20
                        self.scroll_widget = MockScrollWidget()
                
                self.sequence_picker = MockSequencePicker()
                
                # Mock browse tab
                class MockBrowseTab:
                    def __init__(self):
                        class MockSelectionHandler:
                            def on_thumbnail_clicked(self, label):
                                pass
                        self.selection_handler = MockSelectionHandler()
                
                self.browse_tab = MockBrowseTab()
                
                # Mock state
                class MockState:
                    def __init__(self):
                        self.thumbnails = []
                
                self.state = MockState()
        
        # Test creating ModernThumbnailImageLabel
        from main_window.main_widget.browse_tab.thumbnail_box.modern_thumbnail_image_label import ModernThumbnailImageLabel
        
        mock_box = MockThumbnailBox()
        label = ModernThumbnailImageLabel(mock_box)
        
        # Test that components are initialized
        if (hasattr(label, '_image_loading_manager') and 
            hasattr(label, '_visual_state_manager') and 
            hasattr(label, '_lazy_loading_coordinator')):
            print("✅ Component architecture working correctly")
            return True
        else:
            print("❌ Component architecture not initialized properly")
            return False
            
    except Exception as e:
        print(f"❌ Component architecture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Lazy Loading Implementation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_backward_compatibility,
        test_glassmorphism_styling,
        test_component_architecture
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Lazy loading implementation is working.")
        print("\n💡 To see lazy loading in action:")
        print("   1. Start the application")
        print("   2. Open the browse tab")
        print("   3. Check the console for lazy loading debug messages")
        print("   4. Look for glassmorphism loading indicators")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
