"""
Test for LayoutCoordinator to verify the layout management functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication, QWidget
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .layout_coordinator import LayoutCoordinator
from .layout_mode import LayoutMode


class TestLayoutCoordinator(unittest.TestCase):
    """Test the LayoutCoordinator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = Mock()
        self.tab_manager = Mock()
        
        # Set up mock attributes that the coordinator needs
        self.coordinator.main_content_stack = Mock()
        self.coordinator.content_layout = Mock()
        self.coordinator.left_stack = Mock()
        self.coordinator.right_stack = Mock()
        self.coordinator.main_layout = Mock()
        
        self.layout_coordinator = LayoutCoordinator(self.coordinator, self.tab_manager)
    
    def test_initialization(self):
        """Test that the layout coordinator initializes correctly."""
        self.assertEqual(self.layout_coordinator.coordinator, self.coordinator)
        self.assertEqual(self.layout_coordinator.tab_manager, self.tab_manager)
        self.assertEqual(self.layout_coordinator._current_layout_mode, LayoutMode.STACK)
    
    def test_switch_to_stack_layout(self):
        """Test switching to stack layout."""
        self.layout_coordinator._current_layout_mode = LayoutMode.FULL_WIDGET
        
        self.layout_coordinator.switch_to_stack_layout(2, 3)
        
        # Verify stack container is shown
        self.coordinator.main_content_stack.setCurrentIndex.assert_called_with(0)
        
        # Verify stretch factors are applied
        self.coordinator.content_layout.setStretch.assert_any_call(0, 2)
        self.coordinator.content_layout.setStretch.assert_any_call(1, 3)
        
        # Verify width constraints are cleared
        self.coordinator.left_stack.setMaximumWidth.assert_called_with(16777215)
        self.coordinator.left_stack.setMinimumWidth.assert_called_with(0)
        self.coordinator.right_stack.setMaximumWidth.assert_called_with(16777215)
        self.coordinator.right_stack.setMinimumWidth.assert_called_with(0)
        
        # Verify mode is updated
        self.assertEqual(self.layout_coordinator._current_layout_mode, LayoutMode.STACK)
    
    def test_switch_to_stack_layout_already_stack(self):
        """Test switching to stack layout when already in stack mode."""
        self.layout_coordinator._current_layout_mode = LayoutMode.STACK
        
        self.layout_coordinator.switch_to_stack_layout(1, 1)
        
        # Should not call setCurrentIndex since already in stack mode
        self.coordinator.main_content_stack.setCurrentIndex.assert_not_called()
        
        # But should still apply stretch factors
        self.coordinator.content_layout.setStretch.assert_any_call(0, 1)
        self.coordinator.content_layout.setStretch.assert_any_call(1, 1)
    
    def test_switch_to_full_widget_layout_new_widget(self):
        """Test switching to full widget layout with a new widget."""
        test_widget = QWidget()
        
        # Mock that widget is not found in stack
        self.coordinator.main_content_stack.count.return_value = 2
        self.coordinator.main_content_stack.widget.return_value = None
        self.coordinator.main_content_stack.addWidget.return_value = 2
        
        self.layout_coordinator.switch_to_full_widget_layout(test_widget)
        
        # Verify widget is added to stack
        self.coordinator.main_content_stack.addWidget.assert_called_with(test_widget)
        
        # Verify stack is switched to the widget
        self.coordinator.main_content_stack.setCurrentIndex.assert_called_with(2)
        
        # Verify mode is updated
        self.assertEqual(self.layout_coordinator._current_layout_mode, LayoutMode.FULL_WIDGET)
    
    def test_switch_to_full_widget_layout_existing_widget(self):
        """Test switching to full widget layout with an existing widget."""
        test_widget = QWidget()
        
        # Mock that widget is found at index 1
        self.coordinator.main_content_stack.count.return_value = 3
        self.coordinator.main_content_stack.widget.side_effect = lambda i: test_widget if i == 1 else None
        
        self.layout_coordinator.switch_to_full_widget_layout(test_widget)
        
        # Verify widget is NOT added again
        self.coordinator.main_content_stack.addWidget.assert_not_called()
        
        # Verify stack is switched to the existing widget
        self.coordinator.main_content_stack.setCurrentIndex.assert_called_with(1)
        
        # Verify mode is updated
        self.assertEqual(self.layout_coordinator._current_layout_mode, LayoutMode.FULL_WIDGET)
    
    def test_get_current_layout_mode(self):
        """Test getting current layout mode."""
        self.layout_coordinator._current_layout_mode = LayoutMode.FULL_WIDGET
        result = self.layout_coordinator.get_current_layout_mode()
        self.assertEqual(result, LayoutMode.FULL_WIDGET)
    
    def test_update_layout_for_tab_full_widget(self):
        """Test updating layout for a full widget tab."""
        test_widget = QWidget()
        self.tab_manager.get_tab_widget.return_value = test_widget
        
        # Mock the switch method
        self.layout_coordinator.switch_to_full_widget_layout = Mock()
        
        self.layout_coordinator.update_layout_for_tab("browse")
        
        # Verify tab widget is retrieved
        self.tab_manager.get_tab_widget.assert_called_with("browse")
        
        # Verify full widget layout is used
        self.layout_coordinator.switch_to_full_widget_layout.assert_called_with(test_widget)
    
    def test_update_layout_for_tab_stack(self):
        """Test updating layout for a stack-based tab."""
        test_widget = QWidget()
        self.tab_manager.get_tab_widget.return_value = test_widget
        
        # Mock the switch method
        self.layout_coordinator.switch_to_stack_layout = Mock()
        
        self.layout_coordinator.update_layout_for_tab("construct")
        
        # Verify tab widget is retrieved
        self.tab_manager.get_tab_widget.assert_called_with("construct")
        
        # Verify stack layout is used
        self.layout_coordinator.switch_to_stack_layout.assert_called_with()
    
    def test_update_layout_for_tab_no_widget(self):
        """Test updating layout when tab widget is not found."""
        self.tab_manager.get_tab_widget.return_value = None
        
        # Should not raise an exception
        self.layout_coordinator.update_layout_for_tab("nonexistent")
        
        # Verify tab widget lookup was attempted
        self.tab_manager.get_tab_widget.assert_called_with("nonexistent")
    
    def test_get_layout_info(self):
        """Test getting layout information."""
        self.layout_coordinator._current_layout_mode = LayoutMode.FULL_WIDGET
        self.coordinator.main_content_stack.currentIndex.return_value = 2
        self.coordinator.main_content_stack.count.return_value = 3
        self.coordinator.content_layout.stretch.side_effect = lambda i: i + 1
        
        info = self.layout_coordinator.get_layout_info()
        
        expected = {
            "current_mode": "full_widget",
            "stack_index": 2,
            "stack_count": 3,
            "left_stretch": 1,
            "right_stretch": 2,
        }
        
        self.assertEqual(info, expected)


if __name__ == '__main__':
    unittest.main()
