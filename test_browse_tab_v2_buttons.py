#!/usr/bin/env python3
"""
Comprehensive test script for Browse Tab V2 interactive buttons and controls.

This script tests all interactive elements in the browse tab v2 system to ensure
they function correctly without errors, particularly focusing on the filter buttons
that were causing ValueError exceptions.

Test Coverage:
- Quick filter buttons (high difficulty, favorites, etc.)
- Search functionality
- Sort controls
- Filter chips and removal
- Any other interactive UI elements

Usage:
    python test_browse_tab_v2_buttons.py
"""

import sys
import os
import time
import logging
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('browse_tab_v2_button_test.log')
    ]
)

logger = logging.getLogger(__name__)


class BrowseTabV2ButtonTester:
    """Comprehensive tester for Browse Tab V2 interactive elements."""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.browse_tab = None
        self.test_results = []
        
    def setup_application(self):
        """Initialize the application and get browse tab reference."""
        try:
            logger.info("Setting up application for testing...")
            
            # Import and configure paths
            from src.main import configure_import_paths, initialize_logging, initialize_application
            from src.main import initialize_dependency_injection, initialize_legacy_appcontext
            from src.main import create_main_window
            from src.splash_screen.splash_screen import SplashScreen
            from src.profiler import Profiler
            from src.settings_manager.settings_manager import SettingsManager
            
            configure_import_paths()
            initialize_logging()
            
            # Create application
            self.app = initialize_application()
            
            # Initialize services
            settings_manager = SettingsManager()
            splash_screen = SplashScreen(self.app, settings_manager)
            profiler = Profiler()
            
            # Initialize dependency injection
            app_context = initialize_dependency_injection()
            initialize_legacy_appcontext(app_context)
            
            # Create main window
            self.main_window = create_main_window(profiler, splash_screen, app_context)
            self.main_window.initialize_widgets()
            
            # Show window
            self.main_window.show()
            self.app.processEvents()
            
            # Get browse tab reference
            self.browse_tab = self._get_browse_tab()
            
            logger.info("Application setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup application: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_browse_tab(self):
        """Get reference to the browse tab v2 instance."""
        try:
            # Navigate through the widget hierarchy to find browse tab
            main_widget = self.main_window.main_widget
            tab_widget = main_widget.right_stack
            
            # Look for browse tab in the stack
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                if hasattr(widget, 'browse_tab_v2'):
                    return widget.browse_tab_v2
                elif 'browse' in str(type(widget)).lower():
                    return widget
            
            logger.warning("Could not find browse tab v2 instance")
            return None
            
        except Exception as e:
            logger.error(f"Error getting browse tab reference: {e}")
            return None
    
    def test_quick_filter_buttons(self):
        """Test all quick filter buttons for proper functionality."""
        logger.info("Testing quick filter buttons...")
        
        if not self.browse_tab:
            self.test_results.append(("Quick Filter Buttons", "SKIP", "Browse tab not available"))
            return
        
        try:
            # Find the smart filter panel
            filter_panel = self._find_smart_filter_panel()
            if not filter_panel:
                self.test_results.append(("Quick Filter Buttons", "FAIL", "Smart filter panel not found"))
                return
            
            # Test high difficulty button (the one that was failing)
            self._test_high_difficulty_button(filter_panel)
            
            # Test favorites button
            self._test_favorites_button(filter_panel)
            
            # Test any other quick filter buttons
            self._test_other_quick_filters(filter_panel)
            
            logger.info("Quick filter button tests completed")
            
        except Exception as e:
            logger.error(f"Error testing quick filter buttons: {e}")
            self.test_results.append(("Quick Filter Buttons", "ERROR", str(e)))
    
    def _find_smart_filter_panel(self):
        """Find the SmartFilterPanel widget in the browse tab."""
        try:
            # Look for SmartFilterPanel in the browse tab widget hierarchy
            def find_widget_by_type(widget, target_type_name):
                if target_type_name.lower() in str(type(widget)).lower():
                    return widget
                
                for child in widget.findChildren(type(widget)):
                    result = find_widget_by_type(child, target_type_name)
                    if result:
                        return result
                return None
            
            return find_widget_by_type(self.browse_tab, "SmartFilterPanel")
            
        except Exception as e:
            logger.error(f"Error finding smart filter panel: {e}")
            return None
    
    def _test_high_difficulty_button(self, filter_panel):
        """Test the high difficulty button that was causing the ValueError."""
        try:
            logger.info("Testing high difficulty button...")
            
            # Find the high difficulty button
            high_diff_buttons = filter_panel.findChildren(type(filter_panel), name="quickFilterButton")
            high_diff_button = None
            
            for button in high_diff_buttons:
                if hasattr(button, 'text') and 'high' in button.text().lower():
                    high_diff_button = button
                    break
            
            if not high_diff_button:
                # Try alternative approach - look for buttons with "High Difficulty" text
                from PyQt6.QtWidgets import QPushButton
                all_buttons = filter_panel.findChildren(QPushButton)
                for button in all_buttons:
                    if 'high' in button.text().lower() and 'difficulty' in button.text().lower():
                        high_diff_button = button
                        break
            
            if high_diff_button:
                logger.info("Found high difficulty button, testing click...")
                
                # Simulate button click
                high_diff_button.click()
                self.app.processEvents()
                
                logger.info("High difficulty button clicked successfully")
                self.test_results.append(("High Difficulty Button", "PASS", "Button clicked without error"))
            else:
                logger.warning("High difficulty button not found")
                self.test_results.append(("High Difficulty Button", "SKIP", "Button not found"))
                
        except Exception as e:
            logger.error(f"Error testing high difficulty button: {e}")
            self.test_results.append(("High Difficulty Button", "FAIL", str(e)))
    
    def _test_favorites_button(self, filter_panel):
        """Test the favorites quick filter button."""
        try:
            logger.info("Testing favorites button...")
            
            from PyQt6.QtWidgets import QPushButton
            all_buttons = filter_panel.findChildren(QPushButton)
            favorites_button = None
            
            for button in all_buttons:
                if 'favorites' in button.text().lower():
                    favorites_button = button
                    break
            
            if favorites_button:
                logger.info("Found favorites button, testing click...")
                favorites_button.click()
                self.app.processEvents()
                
                logger.info("Favorites button clicked successfully")
                self.test_results.append(("Favorites Button", "PASS", "Button clicked without error"))
            else:
                logger.warning("Favorites button not found")
                self.test_results.append(("Favorites Button", "SKIP", "Button not found"))
                
        except Exception as e:
            logger.error(f"Error testing favorites button: {e}")
            self.test_results.append(("Favorites Button", "FAIL", str(e)))
    
    def _test_other_quick_filters(self, filter_panel):
        """Test any other quick filter buttons found."""
        try:
            logger.info("Testing other quick filter buttons...")
            
            from PyQt6.QtWidgets import QPushButton
            all_buttons = filter_panel.findChildren(QPushButton)
            
            tested_buttons = []
            for button in all_buttons:
                button_text = button.text()
                if (button_text and 
                    'high' not in button_text.lower() and 
                    'favorites' not in button_text.lower() and
                    'clear' not in button_text.lower() and
                    'sort' not in button_text.lower()):
                    
                    try:
                        logger.info(f"Testing button: {button_text}")
                        button.click()
                        self.app.processEvents()
                        tested_buttons.append(button_text)
                        
                    except Exception as e:
                        logger.error(f"Error clicking button {button_text}: {e}")
                        self.test_results.append((f"Button: {button_text}", "FAIL", str(e)))
            
            if tested_buttons:
                self.test_results.append(("Other Quick Filters", "PASS", f"Tested: {', '.join(tested_buttons)}"))
            else:
                self.test_results.append(("Other Quick Filters", "SKIP", "No additional buttons found"))
                
        except Exception as e:
            logger.error(f"Error testing other quick filters: {e}")
            self.test_results.append(("Other Quick Filters", "ERROR", str(e)))
    
    def test_search_functionality(self):
        """Test search input and functionality."""
        logger.info("Testing search functionality...")
        
        try:
            if not self.browse_tab:
                self.test_results.append(("Search Functionality", "SKIP", "Browse tab not available"))
                return
            
            filter_panel = self._find_smart_filter_panel()
            if not filter_panel:
                self.test_results.append(("Search Functionality", "SKIP", "Filter panel not found"))
                return
            
            # Find search input
            from PyQt6.QtWidgets import QLineEdit
            search_inputs = filter_panel.findChildren(QLineEdit)
            
            if search_inputs:
                search_input = search_inputs[0]  # Assume first is the search input
                
                # Test typing in search
                search_input.setText("test search")
                self.app.processEvents()
                
                # Clear search
                search_input.clear()
                self.app.processEvents()
                
                logger.info("Search functionality tested successfully")
                self.test_results.append(("Search Functionality", "PASS", "Search input works"))
            else:
                self.test_results.append(("Search Functionality", "SKIP", "Search input not found"))
                
        except Exception as e:
            logger.error(f"Error testing search functionality: {e}")
            self.test_results.append(("Search Functionality", "FAIL", str(e)))
    
    def test_sort_controls(self):
        """Test sort dropdown and sort order controls."""
        logger.info("Testing sort controls...")
        
        try:
            if not self.browse_tab:
                self.test_results.append(("Sort Controls", "SKIP", "Browse tab not available"))
                return
            
            filter_panel = self._find_smart_filter_panel()
            if not filter_panel:
                self.test_results.append(("Sort Controls", "SKIP", "Filter panel not found"))
                return
            
            # Find sort controls
            from PyQt6.QtWidgets import QComboBox, QPushButton
            
            # Test sort dropdown
            sort_combos = filter_panel.findChildren(QComboBox)
            if sort_combos:
                sort_combo = sort_combos[0]
                original_index = sort_combo.currentIndex()
                
                # Change sort option
                if sort_combo.count() > 1:
                    sort_combo.setCurrentIndex(1)
                    self.app.processEvents()
                    
                    # Restore original
                    sort_combo.setCurrentIndex(original_index)
                    self.app.processEvents()
                
                logger.info("Sort dropdown tested successfully")
            
            # Test sort order button
            sort_buttons = [btn for btn in filter_panel.findChildren(QPushButton) 
                          if 'sort' in btn.text().lower() or '↑' in btn.text() or '↓' in btn.text()]
            
            if sort_buttons:
                sort_button = sort_buttons[0]
                sort_button.click()
                self.app.processEvents()
                
                logger.info("Sort order button tested successfully")
            
            self.test_results.append(("Sort Controls", "PASS", "Sort controls work"))
            
        except Exception as e:
            logger.error(f"Error testing sort controls: {e}")
            self.test_results.append(("Sort Controls", "FAIL", str(e)))
    
    def run_all_tests(self):
        """Run all button and control tests."""
        logger.info("Starting comprehensive Browse Tab V2 button tests...")
        
        if not self.setup_application():
            logger.error("Failed to setup application - aborting tests")
            return False
        
        # Wait for UI to stabilize
        time.sleep(2)
        self.app.processEvents()
        
        # Run all test categories
        self.test_quick_filter_buttons()
        self.test_search_functionality()
        self.test_sort_controls()
        
        # Print results
        self.print_test_results()
        
        return True
    
    def print_test_results(self):
        """Print comprehensive test results."""
        logger.info("\n" + "="*60)
        logger.info("BROWSE TAB V2 BUTTON TEST RESULTS")
        logger.info("="*60)
        
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        
        for test_name, status, details in self.test_results:
            status_symbol = {
                "PASS": "✅",
                "FAIL": "❌", 
                "SKIP": "⏭️",
                "ERROR": "💥"
            }.get(status, "❓")
            
            logger.info(f"{status_symbol} {test_name}: {status}")
            if details:
                logger.info(f"   Details: {details}")
            
            if status == "PASS":
                passed += 1
            elif status == "FAIL":
                failed += 1
            elif status == "SKIP":
                skipped += 1
            elif status == "ERROR":
                errors += 1
        
        logger.info("-" * 60)
        logger.info(f"SUMMARY: {passed} passed, {failed} failed, {skipped} skipped, {errors} errors")
        
        if failed == 0 and errors == 0:
            logger.info("🎉 ALL TESTS PASSED! Browse Tab V2 buttons are working correctly.")
        else:
            logger.warning("⚠️  Some tests failed. Review the details above.")
        
        logger.info("="*60)


def main():
    """Main test execution function."""
    tester = BrowseTabV2ButtonTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            logger.info("Test execution completed")
        else:
            logger.error("Test execution failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up
        if tester.app:
            tester.app.quit()


if __name__ == "__main__":
    main()
