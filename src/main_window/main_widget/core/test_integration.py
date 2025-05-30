"""
Integration test for the refactored MainWidgetCoordinator architecture.

This test verifies that all components work together correctly and that
the refactored architecture maintains full backward compatibility.
"""

import unittest
from unittest.mock import Mock, MagicMock
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from main_widget_coordinator import MainWidgetCoordinator


class TestMainWidgetCoordinatorIntegration(unittest.TestCase):
    """Integration test for the refactored MainWidgetCoordinator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.main_window = Mock()
        self.splash_screen = Mock()
        self.app_context = Mock()
        
        # Mock app context services
        self.app_context.settings_manager = Mock()
        self.app_context.json_manager = Mock()
        self.app_context.get_service = Mock(return_value=None)
        
        # Mock json manager
        self.app_context.json_manager.loader_saver = Mock()
        self.app_context.json_manager.loader_saver.load_current_sequence = Mock(return_value=[])
    
    def test_coordinator_initialization(self):
        """Test that the coordinator initializes all components correctly."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Verify all specialized components are initialized
        self.assertIsNotNone(coordinator.initialization_manager)
        self.assertIsNotNone(coordinator.layout_coordinator)
        self.assertIsNotNone(coordinator.event_coordinator)
        self.assertIsNotNone(coordinator.legacy_compatibility_provider)
        self.assertIsNotNone(coordinator.widget_access_facade)
        
        # Verify core managers are still present
        self.assertIsNotNone(coordinator.tab_manager)
        self.assertIsNotNone(coordinator.widget_manager)
        self.assertIsNotNone(coordinator.state_manager)
    
    def test_backward_compatibility_maintained(self):
        """Test that backward compatibility is maintained."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Verify legacy attributes are available
        self.assertTrue(hasattr(coordinator, 'settings_manager'))
        self.assertTrue(hasattr(coordinator, 'json_manager'))
        self.assertTrue(hasattr(coordinator, 'letter_determiner'))
        self.assertTrue(hasattr(coordinator, 'fade_manager'))
        self.assertTrue(hasattr(coordinator, 'thumbnail_finder'))
        self.assertTrue(hasattr(coordinator, 'sequence_level_evaluator'))
        self.assertTrue(hasattr(coordinator, 'sequence_properties_manager'))
        self.assertTrue(hasattr(coordinator, 'sequence_workbench'))
        self.assertTrue(hasattr(coordinator, 'pictograph_dataset'))
        self.assertTrue(hasattr(coordinator, 'pictograph_collector'))
        self.assertTrue(hasattr(coordinator, 'pictograph_cache'))
        self.assertTrue(hasattr(coordinator, 'construct_tab'))
        self.assertTrue(hasattr(coordinator, 'learn_tab'))
        self.assertTrue(hasattr(coordinator, 'settings_dialog'))
    
    def test_public_api_preserved(self):
        """Test that the public API is preserved."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Verify public methods are available
        self.assertTrue(hasattr(coordinator, 'initialize_components'))
        self.assertTrue(hasattr(coordinator, 'get_current_tab'))
        self.assertTrue(hasattr(coordinator, 'switch_to_tab'))
        self.assertTrue(hasattr(coordinator, 'get_tab_widget'))
        self.assertTrue(hasattr(coordinator, 'switch_to_stack_layout'))
        self.assertTrue(hasattr(coordinator, 'switch_to_full_widget_layout'))
        self.assertTrue(hasattr(coordinator, 'get_current_layout_mode'))
        self.assertTrue(hasattr(coordinator, 'get_widget'))
        self.assertTrue(hasattr(coordinator, 'show_settings_dialog'))
        self.assertTrue(hasattr(coordinator, 'show_full_screen_overlay'))
        self.assertTrue(hasattr(coordinator, 'enable_image_drag_drop'))
        self.assertTrue(hasattr(coordinator, 'disable_image_drag_drop'))
        self.assertTrue(hasattr(coordinator, 'cleanup'))
    
    def test_component_delegation(self):
        """Test that methods properly delegate to specialized components."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Mock the specialized components
        coordinator.layout_coordinator.switch_to_stack_layout = Mock()
        coordinator.layout_coordinator.switch_to_full_widget_layout = Mock()
        coordinator.layout_coordinator.get_current_layout_mode = Mock()
        coordinator.layout_coordinator.get_current_layout_mode.return_value.value = "stack"
        
        coordinator.widget_access_facade.get_widget = Mock()
        coordinator.widget_access_facade.get_tab_widget = Mock()
        coordinator.widget_access_facade.show_settings_dialog = Mock()
        coordinator.widget_access_facade.show_full_screen_overlay = Mock()
        
        coordinator.tab_manager.switch_to_tab = Mock()
        coordinator.state_manager.current_tab = "test_tab"
        
        # Test layout delegation
        coordinator.switch_to_stack_layout(2, 3)
        coordinator.layout_coordinator.switch_to_stack_layout.assert_called_with(2, 3)
        
        from PyQt6.QtWidgets import QWidget
        test_widget = QWidget()
        coordinator.switch_to_full_widget_layout(test_widget)
        coordinator.layout_coordinator.switch_to_full_widget_layout.assert_called_with(test_widget)
        
        layout_mode = coordinator.get_current_layout_mode()
        self.assertEqual(layout_mode, "stack")
        
        # Test widget access delegation
        coordinator.get_widget("test_widget")
        coordinator.widget_access_facade.get_widget.assert_called_with("test_widget")
        
        coordinator.get_tab_widget("test_tab")
        coordinator.widget_access_facade.get_tab_widget.assert_called_with("test_tab")
        
        coordinator.show_settings_dialog()
        coordinator.widget_access_facade.show_settings_dialog.assert_called_once()
        
        coordinator.show_full_screen_overlay("test_data")
        coordinator.widget_access_facade.show_full_screen_overlay.assert_called_with("test_data")
        
        # Test tab management delegation
        coordinator.switch_to_tab("new_tab")
        coordinator.tab_manager.switch_to_tab.assert_called_with("new_tab")
        
        current_tab = coordinator.get_current_tab()
        self.assertEqual(current_tab, "test_tab")
    
    def test_initialization_delegation(self):
        """Test that initialization properly delegates to ComponentInitializationManager."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Mock the initialization manager
        coordinator.initialization_manager.initialize_all_components = Mock()
        
        # Test initialization delegation
        coordinator.initialize_components()
        coordinator.initialization_manager.initialize_all_components.assert_called_once()
    
    def test_cleanup_integration(self):
        """Test that cleanup properly coordinates all components."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Mock cleanup methods
        coordinator.event_coordinator.disconnect_all_signals = Mock()
        coordinator.tab_manager.cleanup = Mock()
        coordinator.widget_manager.cleanup = Mock()
        coordinator.state_manager.cleanup = Mock()
        coordinator.image_drag_drop_handler.cleanup = Mock()
        
        # Test cleanup coordination
        coordinator.cleanup()
        
        # Verify all cleanup methods are called
        coordinator.event_coordinator.disconnect_all_signals.assert_called_once()
        coordinator.tab_manager.cleanup.assert_called_once()
        coordinator.widget_manager.cleanup.assert_called_once()
        coordinator.state_manager.cleanup.assert_called_once()
        coordinator.image_drag_drop_handler.cleanup.assert_called_once()
    
    def test_signals_preserved(self):
        """Test that signals are preserved and properly connected."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Verify signals exist
        self.assertTrue(hasattr(coordinator, 'tab_changed'))
        self.assertTrue(hasattr(coordinator, 'state_changed'))
        
        # Verify signals are PyQt signals
        from PyQt6.QtCore import pyqtSignal
        self.assertIsInstance(coordinator.tab_changed, pyqtSignal)
        self.assertIsInstance(coordinator.state_changed, pyqtSignal)
    
    def test_architecture_integrity(self):
        """Test that the new architecture maintains proper separation of concerns."""
        coordinator = MainWidgetCoordinator(self.main_window, self.splash_screen, self.app_context)
        
        # Verify each component has its specific responsibilities
        
        # ComponentInitializationManager should handle initialization
        self.assertTrue(hasattr(coordinator.initialization_manager, 'initialize_all_components'))
        
        # LayoutCoordinator should handle layout management
        self.assertTrue(hasattr(coordinator.layout_coordinator, 'switch_to_stack_layout'))
        self.assertTrue(hasattr(coordinator.layout_coordinator, 'switch_to_full_widget_layout'))
        
        # EventCoordinator should handle event management
        self.assertTrue(hasattr(coordinator.event_coordinator, 'connect_all_signals'))
        self.assertTrue(hasattr(coordinator.event_coordinator, 'disconnect_all_signals'))
        
        # LegacyCompatibilityProvider should handle backward compatibility
        self.assertTrue(hasattr(coordinator.legacy_compatibility_provider, 'inject_all_legacy_services'))
        
        # WidgetAccessFacade should handle widget access
        self.assertTrue(hasattr(coordinator.widget_access_facade, 'get_widget'))
        self.assertTrue(hasattr(coordinator.widget_access_facade, 'get_tab_widget'))


if __name__ == '__main__':
    unittest.main()
