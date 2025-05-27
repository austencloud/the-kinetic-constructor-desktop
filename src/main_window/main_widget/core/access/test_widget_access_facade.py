"""
Test for WidgetAccessFacade to verify widget access functionality.
"""

import unittest
from unittest.mock import Mock
from PyQt6.QtWidgets import QApplication, QWidget
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .widget_access_facade import WidgetAccessFacade


class TestWidgetAccessFacade(unittest.TestCase):
    """Test the WidgetAccessFacade functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.widget_manager = Mock()
        self.tab_manager = Mock()
        
        self.facade = WidgetAccessFacade(self.widget_manager, self.tab_manager)
    
    def test_initialization(self):
        """Test that the facade initializes correctly."""
        self.assertEqual(self.facade.widget_manager, self.widget_manager)
        self.assertEqual(self.facade.tab_manager, self.tab_manager)
    
    def test_get_widget_found(self):
        """Test getting a widget that exists."""
        mock_widget = QWidget()
        self.widget_manager.get_widget.return_value = mock_widget
        
        result = self.facade.get_widget("test_widget")
        
        self.assertEqual(result, mock_widget)
        self.widget_manager.get_widget.assert_called_with("test_widget")
    
    def test_get_widget_not_found(self):
        """Test getting a widget that doesn't exist."""
        self.widget_manager.get_widget.return_value = None
        
        result = self.facade.get_widget("nonexistent_widget")
        
        self.assertIsNone(result)
        self.widget_manager.get_widget.assert_called_with("nonexistent_widget")
    
    def test_get_tab_widget_found(self):
        """Test getting a tab widget that exists."""
        mock_tab = QWidget()
        self.tab_manager.get_tab_widget.return_value = mock_tab
        
        result = self.facade.get_tab_widget("test_tab")
        
        self.assertEqual(result, mock_tab)
        self.tab_manager.get_tab_widget.assert_called_with("test_tab")
    
    def test_get_tab_widget_not_found(self):
        """Test getting a tab widget that doesn't exist."""
        self.tab_manager.get_tab_widget.return_value = None
        
        result = self.facade.get_tab_widget("nonexistent_tab")
        
        self.assertIsNone(result)
        self.tab_manager.get_tab_widget.assert_called_with("nonexistent_tab")
    
    def test_show_settings_dialog_success(self):
        """Test showing settings dialog when available."""
        mock_dialog = Mock()
        mock_dialog.show = Mock()
        self.widget_manager.get_widget.return_value = mock_dialog
        
        result = self.facade.show_settings_dialog()
        
        self.assertTrue(result)
        self.widget_manager.get_widget.assert_called_with("settings_dialog")
        mock_dialog.show.assert_called_once()
    
    def test_show_settings_dialog_not_available(self):
        """Test showing settings dialog when not available."""
        self.widget_manager.get_widget.return_value = None
        
        result = self.facade.show_settings_dialog()
        
        self.assertFalse(result)
        self.widget_manager.get_widget.assert_called_with("settings_dialog")
    
    def test_show_settings_dialog_no_show_method(self):
        """Test showing settings dialog when widget has no show method."""
        mock_dialog = Mock()
        del mock_dialog.show  # Remove show method
        self.widget_manager.get_widget.return_value = mock_dialog
        
        result = self.facade.show_settings_dialog()
        
        self.assertFalse(result)
        self.widget_manager.get_widget.assert_called_with("settings_dialog")
    
    def test_show_full_screen_overlay_success(self):
        """Test showing full screen overlay when available."""
        mock_overlay = Mock()
        mock_overlay.show_image = Mock()
        self.widget_manager.get_widget.return_value = mock_overlay
        
        test_image_data = "test_image_data"
        result = self.facade.show_full_screen_overlay(test_image_data)
        
        self.assertTrue(result)
        self.widget_manager.get_widget.assert_called_with("full_screen_overlay")
        mock_overlay.show_image.assert_called_with(test_image_data)
    
    def test_show_full_screen_overlay_not_available(self):
        """Test showing full screen overlay when not available."""
        self.widget_manager.get_widget.return_value = None
        
        result = self.facade.show_full_screen_overlay("test_data")
        
        self.assertFalse(result)
        self.widget_manager.get_widget.assert_called_with("full_screen_overlay")
    
    def test_get_construct_tab(self):
        """Test getting construct tab."""
        mock_tab = QWidget()
        self.tab_manager.get_tab_widget.return_value = mock_tab
        
        result = self.facade.get_construct_tab()
        
        self.assertEqual(result, mock_tab)
        self.tab_manager.get_tab_widget.assert_called_with("construct")
    
    def test_get_learn_tab(self):
        """Test getting learn tab."""
        mock_tab = QWidget()
        self.tab_manager.get_tab_widget.return_value = mock_tab
        
        result = self.facade.get_learn_tab()
        
        self.assertEqual(result, mock_tab)
        self.tab_manager.get_tab_widget.assert_called_with("learn")
    
    def test_get_browse_tab(self):
        """Test getting browse tab."""
        mock_tab = QWidget()
        self.tab_manager.get_tab_widget.return_value = mock_tab
        
        result = self.facade.get_browse_tab()
        
        self.assertEqual(result, mock_tab)
        self.tab_manager.get_tab_widget.assert_called_with("browse")
    
    def test_get_sequence_card_tab(self):
        """Test getting sequence card tab."""
        mock_tab = QWidget()
        self.tab_manager.get_tab_widget.return_value = mock_tab
        
        result = self.facade.get_sequence_card_tab()
        
        self.assertEqual(result, mock_tab)
        self.tab_manager.get_tab_widget.assert_called_with("sequence_card")
    
    def test_is_widget_available_true(self):
        """Test checking widget availability when widget exists."""
        self.widget_manager.get_widget.return_value = QWidget()
        
        result = self.facade.is_widget_available("test_widget")
        
        self.assertTrue(result)
        self.widget_manager.get_widget.assert_called_with("test_widget")
    
    def test_is_widget_available_false(self):
        """Test checking widget availability when widget doesn't exist."""
        self.widget_manager.get_widget.return_value = None
        
        result = self.facade.is_widget_available("test_widget")
        
        self.assertFalse(result)
        self.widget_manager.get_widget.assert_called_with("test_widget")
    
    def test_is_tab_available_true(self):
        """Test checking tab availability when tab exists."""
        self.tab_manager.get_tab_widget.return_value = QWidget()
        
        result = self.facade.is_tab_available("test_tab")
        
        self.assertTrue(result)
        self.tab_manager.get_tab_widget.assert_called_with("test_tab")
    
    def test_is_tab_available_false(self):
        """Test checking tab availability when tab doesn't exist."""
        self.tab_manager.get_tab_widget.return_value = None
        
        result = self.facade.is_tab_available("test_tab")
        
        self.assertFalse(result)
        self.tab_manager.get_tab_widget.assert_called_with("test_tab")
    
    def test_get_widget_status(self):
        """Test getting widget status."""
        # Mock widget availability
        def mock_get_widget(name):
            available_widgets = ["menu_bar", "settings_dialog"]
            return QWidget() if name in available_widgets else None
        
        def mock_get_tab_widget(name):
            available_tabs = ["construct", "browse"]
            return QWidget() if name in available_tabs else None
        
        self.widget_manager.get_widget.side_effect = mock_get_widget
        self.tab_manager.get_tab_widget.side_effect = mock_get_tab_widget
        
        status = self.facade.get_widget_status()
        
        # Verify structure
        self.assertIn("widgets", status)
        self.assertIn("tabs", status)
        
        # Verify some specific statuses
        self.assertTrue(status["widgets"]["menu_bar"])
        self.assertTrue(status["widgets"]["settings_dialog"])
        self.assertFalse(status["widgets"]["full_screen_overlay"])
        
        self.assertTrue(status["tabs"]["construct"])
        self.assertTrue(status["tabs"]["browse"])
        self.assertFalse(status["tabs"]["learn"])


if __name__ == '__main__':
    unittest.main()
