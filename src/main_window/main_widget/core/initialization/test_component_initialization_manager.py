"""
Test for ComponentInitializationManager to verify the refactoring works correctly.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .component_initialization_manager import ComponentInitializationManager


class TestComponentInitializationManager(unittest.TestCase):
    """Test the ComponentInitializationManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.app_context = Mock()
        self.widget_manager = Mock()
        self.tab_manager = Mock()
        self.coordinator = Mock()

        # Set up mock attributes that the coordinator needs
        self.coordinator.main_layout = Mock()
        self.coordinator.state_manager = Mock()

        self.manager = ComponentInitializationManager(
            self.app_context, self.widget_manager, self.tab_manager, self.coordinator
        )

    def test_initialization(self):
        """Test that the manager initializes correctly."""
        self.assertEqual(self.manager.app_context, self.app_context)
        self.assertEqual(self.manager.widget_manager, self.widget_manager)
        self.assertEqual(self.manager.tab_manager, self.tab_manager)
        self.assertEqual(self.manager.coordinator, self.coordinator)
        self.assertFalse(self.manager._components_initialized)

    def test_initialize_widgets(self):
        """Test widget initialization."""
        self.manager._initialize_widgets()
        self.widget_manager.initialize_widgets.assert_called_once()

    def test_initialize_tabs(self):
        """Test tab initialization."""
        self.manager._initialize_tabs()
        self.tab_manager.initialize_tabs.assert_called_once()

    def test_initialize_state(self):
        """Test state initialization."""
        self.manager._initialize_state()
        self.coordinator.state_manager.initialize_state.assert_called_once()

    @patch("PyQt6.QtWidgets.QHBoxLayout")
    def test_setup_menu_bar_layout(self, mock_layout_class):
        """Test menu bar layout setup."""
        # Mock the menu bar widget
        mock_menu_bar = Mock()
        mock_menu_bar.social_media_widget = Mock()
        mock_menu_bar.navigation_widget = Mock()
        mock_menu_bar.settings_button = Mock()

        self.widget_manager.get_widget.return_value = mock_menu_bar

        # Mock the layout
        mock_layout = Mock()
        mock_layout_class.return_value = mock_layout

        self.manager._setup_menu_bar_layout()

        # Verify widget manager was called
        self.widget_manager.get_widget.assert_called_with("menu_bar")

        # Verify layout was created and configured
        mock_layout_class.assert_called_once()
        mock_layout.setContentsMargins.assert_called_with(0, 0, 0, 0)
        mock_layout.setSpacing.assert_called_with(0)

        # Verify widgets were added to layout
        self.assertEqual(mock_layout.addWidget.call_count, 3)

        # Verify layout was inserted into main layout
        self.coordinator.main_layout.insertLayout.assert_called_once_with(
            0, mock_layout
        )

    def test_setup_menu_bar_layout_no_menu_bar(self):
        """Test menu bar layout setup when menu bar is not available."""
        self.widget_manager.get_widget.return_value = None

        # Should not raise an exception
        self.manager._setup_menu_bar_layout()

        # Verify it tried to get the menu bar
        self.widget_manager.get_widget.assert_called_with("menu_bar")

    def test_handle_initialization_error(self):
        """Test error handling."""
        test_error = Exception("Test error")

        with self.assertRaises(Exception) as context:
            self.manager.handle_initialization_error(test_error)

        self.assertEqual(context.exception, test_error)

    def test_initialize_all_components_success(self):
        """Test successful full initialization."""
        # Mock all the methods to avoid complex setup
        self.manager._initialize_widgets = Mock()
        self.manager._initialize_services = Mock()
        self.manager._setup_menu_bar_layout = Mock()
        self.manager._initialize_tabs = Mock()
        self.manager._initialize_state = Mock()
        self.manager._load_saved_sequence = Mock()

        self.manager.initialize_all_components()

        # Verify all phases were called
        self.manager._initialize_widgets.assert_called_once()
        self.manager._initialize_services.assert_called_once()
        self.manager._setup_menu_bar_layout.assert_called_once()
        self.manager._initialize_tabs.assert_called_once()
        self.manager._initialize_state.assert_called_once()
        self.manager._load_saved_sequence.assert_called_once()

        # Verify initialization flag was set
        self.assertTrue(self.manager._components_initialized)

    def test_initialize_all_components_already_initialized(self):
        """Test that initialization is skipped if already done."""
        self.manager._components_initialized = True

        # Mock methods to verify they're not called
        self.manager._initialize_widgets = Mock()

        self.manager.initialize_all_components()

        # Verify no initialization methods were called
        self.manager._initialize_widgets.assert_not_called()


if __name__ == "__main__":
    unittest.main()
