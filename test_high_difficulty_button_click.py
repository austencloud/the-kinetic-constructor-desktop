#!/usr/bin/env python3
"""
Simple test to verify the high difficulty button works in the running application.

This script will attempt to find and click the high difficulty button to ensure
the ValueError: Invalid operator: greater_than_or_equal error has been resolved.
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_high_difficulty_button_in_running_app():
    """Test the high difficulty button in a running application instance."""
    print("Testing high difficulty button in running application...")
    
    try:
        # Import PyQt6 for finding widgets
        from PyQt6.QtWidgets import QApplication, QPushButton
        from PyQt6.QtCore import QTimer
        
        # Get the running application instance
        app = QApplication.instance()
        if not app:
            print("❌ No running QApplication found. Please start the application first.")
            return False
        
        print("✅ Found running QApplication")
        
        # Find all top-level widgets (main windows)
        top_level_widgets = app.topLevelWidgets()
        main_window = None
        
        for widget in top_level_widgets:
            if hasattr(widget, 'main_widget') or 'MainWindow' in str(type(widget)):
                main_window = widget
                break
        
        if not main_window:
            print("❌ Could not find main window")
            return False
        
        print("✅ Found main window")
        
        # Find all QPushButton widgets in the application
        all_buttons = main_window.findChildren(QPushButton)
        high_diff_button = None
        
        print(f"Found {len(all_buttons)} buttons in the application")
        
        # Look for the high difficulty button
        for button in all_buttons:
            button_text = button.text()
            if button_text and 'high' in button_text.lower() and 'difficulty' in button_text.lower():
                high_diff_button = button
                print(f"✅ Found high difficulty button: '{button_text}'")
                break
        
        if not high_diff_button:
            print("❌ Could not find high difficulty button")
            # List all button texts for debugging
            print("Available buttons:")
            for button in all_buttons[:20]:  # Show first 20 buttons
                if button.text():
                    print(f"  - '{button.text()}'")
            return False
        
        # Test clicking the button
        print("🔄 Testing button click...")
        
        try:
            # Click the button
            high_diff_button.click()
            
            # Process events to ensure the click is handled
            app.processEvents()
            
            print("✅ High difficulty button clicked successfully!")
            print("✅ No ValueError exception occurred - the fix is working!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error clicking high difficulty button: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("="*60)
    print("HIGH DIFFICULTY BUTTON TEST")
    print("="*60)
    print("This test will attempt to click the high difficulty button")
    print("in the currently running application to verify the fix.")
    print("-"*60)
    
    # Wait a moment for the application to be ready
    time.sleep(1)
    
    success = test_high_difficulty_button_in_running_app()
    
    print("-"*60)
    if success:
        print("🎉 TEST PASSED! High difficulty button works correctly.")
        print("✅ The FilterCriteria 'greater_than_or_equal' fix is successful.")
    else:
        print("❌ TEST FAILED! Please check the application state.")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
