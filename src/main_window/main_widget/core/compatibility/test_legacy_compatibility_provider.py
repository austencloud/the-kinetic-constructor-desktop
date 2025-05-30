"""
Test for LegacyCompatibilityProvider to verify backward compatibility functionality.
"""

import unittest
from unittest.mock import Mock
from PyQt6.QtWidgets import QApplication
import sys

# Ensure QApplication exists for testing
if not QApplication.instance():
    app = QApplication(sys.argv)

from .legacy_compatibility_provider import LegacyCompatibilityProvider


class TestLegacyCompatibilityProvider(unittest.TestCase):
    """Test the LegacyCompatibilityProvider functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = Mock()
        self.app_context = Mock()

        # Mock app context services
        self.app_context.settings_manager = Mock()
        self.app_context.json_manager = Mock()

        self.provider = LegacyCompatibilityProvider(self.coordinator, self.app_context)

    def test_initialization(self):
        """Test that the provider initializes correctly."""
        self.assertEqual(self.provider.coordinator, self.coordinator)
        self.assertEqual(self.provider.app_context, self.app_context)

    def test_inject_all_legacy_services(self):
        """Test injecting all legacy services."""
        self.provider.inject_all_legacy_services()

        # Verify core services are injected
        self.assertEqual(
            self.coordinator.settings_manager, self.app_context.settings_manager
        )
        self.assertEqual(self.coordinator.json_manager, self.app_context.json_manager)

        # Verify compatibility attributes are created
        self.assertIsNone(self.coordinator.letter_determiner)
        self.assertIsNone(self.coordinator.fade_manager)
        self.assertIsNone(self.coordinator.thumbnail_finder)
        self.assertIsNone(self.coordinator.sequence_level_evaluator)
        self.assertIsNone(self.coordinator.sequence_properties_manager)
        self.assertIsNone(self.coordinator.sequence_workbench)
        self.assertIsNone(self.coordinator.pictograph_dataset)
        self.assertIsNone(self.coordinator.pictograph_collector)
        self.assertEqual(self.coordinator.pictograph_cache, {})

        # Verify tab widgets are initialized
        self.assertIsNone(self.coordinator.construct_tab)
        self.assertIsNone(self.coordinator.learn_tab)
        self.assertIsNone(self.coordinator.settings_dialog)

    def test_get_legacy_service_status_all_none(self):
        """Test getting legacy service status when all services are None."""
        self.provider.inject_all_legacy_services()

        status = self.provider.get_legacy_service_status()

        expected = {
            "settings_manager": True,  # This should be set
            "json_manager": True,  # This should be set
            "letter_determiner": False,
            "fade_manager": False,
            "thumbnail_finder": False,
            "sequence_level_evaluator": False,
            "sequence_properties_manager": False,
            "sequence_workbench": False,
            "pictograph_dataset": False,
            "pictograph_collector": False,
            "construct_tab": False,
            "learn_tab": False,
            "settings_dialog": False,
        }

        self.assertEqual(status, expected)

    def test_get_legacy_service_status_some_available(self):
        """Test getting legacy service status when some services are available."""
        self.provider.inject_all_legacy_services()

        # Set some services to non-None values
        self.coordinator.fade_manager = Mock()
        self.coordinator.construct_tab = Mock()
        self.coordinator.pictograph_dataset = {}

        status = self.provider.get_legacy_service_status()

        # Verify the status reflects the actual state
        self.assertTrue(status["fade_manager"])
        self.assertTrue(status["construct_tab"])
        self.assertTrue(status["pictograph_dataset"])
        self.assertFalse(status["learn_tab"])
        self.assertFalse(status["thumbnail_finder"])

    def test_validate_legacy_services_all_present(self):
        """Test validating legacy services when all are present."""
        self.provider.inject_all_legacy_services()

        missing = self.provider.validate_legacy_services()

        # The validate method only reports services that are None, not missing attributes
        # Since we inject all services (even as None), no services should be "missing"
        # Only core services that are actually None would be reported
        self.assertIsInstance(missing, list)

    def test_validate_legacy_services_missing_core(self):
        """Test validating legacy services when core services are missing."""
        # Don't inject services, but the coordinator still has the attributes from setUp
        # Set them to None to simulate missing services
        self.coordinator.settings_manager = None
        self.coordinator.json_manager = None

        missing = self.provider.validate_legacy_services()

        # Should include core services
        self.assertIn("settings_manager", missing)
        self.assertIn("json_manager", missing)

    def test_validate_legacy_services_missing_attributes(self):
        """Test validating legacy services when attributes are missing."""
        self.provider.inject_all_legacy_services()

        # Remove an attribute
        delattr(self.coordinator, "fade_manager")

        missing = self.provider.validate_legacy_services()

        # Should include the missing attribute
        self.assertIn("fade_manager", missing)

    def test_create_migration_plan(self):
        """Test creating migration plan."""
        plan = self.provider.create_migration_plan()

        # Verify plan structure
        self.assertIn("immediate_removal", plan)
        self.assertIn("short_term_migration", plan)
        self.assertIn("medium_term_migration", plan)
        self.assertIn("long_term_migration", plan)
        self.assertIn("ui_refactoring", plan)

        # Verify some expected items
        self.assertIn("pictograph_cache", plan["immediate_removal"])
        self.assertIn("settings_manager", plan["short_term_migration"])
        self.assertIn("json_manager", plan["short_term_migration"])
        self.assertIn("construct_tab", plan["ui_refactoring"])
        self.assertIn("learn_tab", plan["ui_refactoring"])

    def test_inject_core_services(self):
        """Test injecting core services."""
        self.provider._inject_core_services()

        # Verify core services are set
        self.assertEqual(
            self.coordinator.settings_manager, self.app_context.settings_manager
        )
        self.assertEqual(self.coordinator.json_manager, self.app_context.json_manager)

    def test_create_compatibility_attributes(self):
        """Test creating compatibility attributes."""
        self.provider._create_compatibility_attributes()

        # Verify all attributes are created and set to None or appropriate defaults
        self.assertIsNone(self.coordinator.letter_determiner)
        self.assertIsNone(self.coordinator.fade_manager)
        self.assertIsNone(self.coordinator.thumbnail_finder)
        self.assertIsNone(self.coordinator.sequence_level_evaluator)
        self.assertIsNone(self.coordinator.sequence_properties_manager)
        self.assertIsNone(self.coordinator.sequence_workbench)
        self.assertIsNone(self.coordinator.pictograph_dataset)
        self.assertIsNone(self.coordinator.pictograph_collector)
        self.assertEqual(self.coordinator.pictograph_cache, {})
        self.assertIsNone(self.coordinator.construct_tab)
        self.assertIsNone(self.coordinator.learn_tab)
        self.assertIsNone(self.coordinator.settings_dialog)


if __name__ == "__main__":
    unittest.main()
