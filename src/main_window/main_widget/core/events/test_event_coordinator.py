"""
Test for EventCoordinator to verify the event handling functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .event_coordinator import EventCoordinator


class TestEventCoordinator(unittest.TestCase):
    """Test the EventCoordinator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = Mock()
        self.tab_manager = Mock()
        self.widget_manager = Mock()
        self.state_manager = Mock()
        self.image_drag_drop_handler = Mock()
        
        # Set up mock signals
        self.tab_manager.tab_changed = Mock()
        self.widget_manager.widget_ready = Mock()
        self.state_manager.state_changed = Mock()
        self.image_drag_drop_handler.image_dropped = Mock()
        self.image_drag_drop_handler.images_dropped = Mock()
        self.image_drag_drop_handler.drop_error = Mock()
        self.coordinator.state_changed = Mock()
        
        self.event_coordinator = EventCoordinator(
            self.coordinator,
            self.tab_manager,
            self.widget_manager,
            self.state_manager,
            self.image_drag_drop_handler
        )
    
    def test_initialization(self):
        """Test that the event coordinator initializes correctly."""
        self.assertEqual(self.event_coordinator.coordinator, self.coordinator)
        self.assertEqual(self.event_coordinator.tab_manager, self.tab_manager)
        self.assertEqual(self.event_coordinator.widget_manager, self.widget_manager)
        self.assertEqual(self.event_coordinator.state_manager, self.state_manager)
        self.assertEqual(self.event_coordinator.image_drag_drop_handler, self.image_drag_drop_handler)
    
    def test_connect_all_signals(self):
        """Test connecting all signals."""
        self.event_coordinator.connect_all_signals()
        
        # Verify manager signals are connected
        self.tab_manager.tab_changed.connect.assert_called_with(self.event_coordinator.handle_tab_changed)
        self.widget_manager.widget_ready.connect.assert_called_with(self.event_coordinator.handle_widget_ready)
        self.state_manager.state_changed.connect.assert_called_with(self.coordinator.state_changed.emit)
        
        # Verify image drop signals are connected
        self.image_drag_drop_handler.image_dropped.connect.assert_called_with(self.event_coordinator.handle_image_dropped)
        self.image_drag_drop_handler.images_dropped.connect.assert_called_with(self.event_coordinator.handle_images_dropped)
        self.image_drag_drop_handler.drop_error.connect.assert_called_with(self.event_coordinator.handle_drop_error)
    
    def test_handle_tab_changed(self):
        """Test handling tab change events."""
        # Mock layout coordinator
        self.coordinator.layout_coordinator = Mock()
        
        self.event_coordinator.handle_tab_changed("construct")
        
        # Verify state is updated
        self.state_manager.set_current_tab.assert_called_with("construct")
        
        # Verify widget visibility is updated
        self.widget_manager.update_for_tab.assert_called_with("construct")
        
        # Verify layout is updated
        self.coordinator.layout_coordinator.update_layout_for_tab.assert_called_with("construct")
        
        # Verify signal is emitted
        self.coordinator.tab_changed.emit.assert_called_with("construct")
    
    def test_handle_tab_changed_no_layout_coordinator(self):
        """Test handling tab change when layout coordinator is not available."""
        # Don't set layout_coordinator attribute
        
        # Should not raise an exception
        self.event_coordinator.handle_tab_changed("construct")
        
        # Verify other operations still work
        self.state_manager.set_current_tab.assert_called_with("construct")
        self.widget_manager.update_for_tab.assert_called_with("construct")
        self.coordinator.tab_changed.emit.assert_called_with("construct")
    
    def test_update_navigation_highlighting(self):
        """Test updating navigation highlighting."""
        # Mock menu bar and navigation widget
        mock_menu_bar = Mock()
        mock_navigation_widget = Mock()
        mock_menu_bar.navigation_widget = mock_navigation_widget
        
        self.widget_manager.get_widget.return_value = mock_menu_bar
        
        self.event_coordinator.update_navigation_highlighting("browse")
        
        # Verify menu bar is retrieved
        self.widget_manager.get_widget.assert_called_with("menu_bar")
        
        # Verify navigation highlighting is updated
        mock_navigation_widget.on_tab_changed_programmatically.assert_called_with("browse")
    
    def test_update_navigation_highlighting_no_menu_bar(self):
        """Test updating navigation highlighting when menu bar is not available."""
        self.widget_manager.get_widget.return_value = None
        
        # Should not raise an exception
        self.event_coordinator.update_navigation_highlighting("browse")
        
        # Verify menu bar lookup was attempted
        self.widget_manager.get_widget.assert_called_with("menu_bar")
    
    def test_update_navigation_highlighting_no_method(self):
        """Test updating navigation highlighting when method is not available."""
        # Mock menu bar without the required method
        mock_menu_bar = Mock()
        mock_navigation_widget = Mock()
        del mock_navigation_widget.on_tab_changed_programmatically  # Remove the method
        mock_menu_bar.navigation_widget = mock_navigation_widget
        
        self.widget_manager.get_widget.return_value = mock_menu_bar
        
        # Should not raise an exception
        self.event_coordinator.update_navigation_highlighting("browse")
        
        # Verify menu bar is retrieved
        self.widget_manager.get_widget.assert_called_with("menu_bar")
    
    def test_handle_widget_ready(self):
        """Test handling widget ready events."""
        self.event_coordinator.handle_widget_ready("menu_bar")
        
        # Verify tab manager is notified
        self.tab_manager.on_widget_ready.assert_called_with("menu_bar")
    
    def test_handle_image_dropped(self):
        """Test handling single image drop events."""
        # Should not raise an exception
        self.event_coordinator.handle_image_dropped("/path/to/image.png")
    
    def test_handle_images_dropped(self):
        """Test handling multiple images drop events."""
        image_paths = ["/path/to/image1.png", "/path/to/image2.png"]
        
        # Should not raise an exception
        self.event_coordinator.handle_images_dropped(image_paths)
    
    def test_handle_drop_error(self):
        """Test handling drag and drop errors."""
        # Should not raise an exception
        self.event_coordinator.handle_drop_error("Test error message")
    
    def test_disconnect_all_signals(self):
        """Test disconnecting all signals."""
        self.event_coordinator.disconnect_all_signals()
        
        # Verify all signals are disconnected
        self.tab_manager.tab_changed.disconnect.assert_called_once()
        self.widget_manager.widget_ready.disconnect.assert_called_once()
        self.state_manager.state_changed.disconnect.assert_called_once()
        self.image_drag_drop_handler.image_dropped.disconnect.assert_called_once()
        self.image_drag_drop_handler.images_dropped.disconnect.assert_called_once()
        self.image_drag_drop_handler.drop_error.disconnect.assert_called_once()
    
    def test_get_connection_status(self):
        """Test getting connection status."""
        # Mock receivers count
        self.tab_manager.tab_changed.receivers.return_value = 1
        self.widget_manager.widget_ready.receivers.return_value = 1
        self.state_manager.state_changed.receivers.return_value = 1
        self.image_drag_drop_handler.image_dropped.receivers.return_value = 1
        
        status = self.event_coordinator.get_connection_status()
        
        expected = {
            "tab_manager_connected": True,
            "widget_manager_connected": True,
            "state_manager_connected": True,
            "image_drop_connected": True,
        }
        
        self.assertEqual(status, expected)


if __name__ == '__main__':
    unittest.main()
