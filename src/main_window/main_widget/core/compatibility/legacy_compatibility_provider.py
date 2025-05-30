"""
Legacy Compatibility Provider - Handles all backward compatibility service injection.

This provider isolates all legacy compatibility code from the main architecture
following the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.application_context import ApplicationContext
    from ..main_widget_coordinator import MainWidgetCoordinator

class LegacyCompatibilityProvider:
    """
    Handles all backward compatibility service injection.
    
    Responsibilities:
    - Inject legacy services and attributes
    - Maintain compatibility interfaces
    - Isolate legacy code from new architecture
    - Provide migration path for legacy dependencies
    """
    
    def __init__(self, coordinator: "MainWidgetCoordinator", app_context: "ApplicationContext"):
        self.coordinator = coordinator
        self.app_context = app_context
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("LegacyCompatibilityProvider initialized")
    
    def inject_all_legacy_services(self) -> None:
        """
        Inject all legacy services into the coordinator for backward compatibility.
        
        Many legacy components expect to access services through main_widget attributes.
        This method provides those services to maintain compatibility.
        """
        self.logger.debug("Injecting all legacy services")
        
        self._inject_core_services()
        self._create_compatibility_attributes()
        
        self.logger.debug("All legacy services injected")
    
    def _inject_core_services(self) -> None:
        """Inject core services that are immediately available."""
        # Core services
        self.coordinator.settings_manager = self.app_context.settings_manager
        self.coordinator.json_manager = self.app_context.json_manager
        
        self.logger.debug("Core services injected")
    
    def _create_compatibility_attributes(self) -> None:
        """Create compatibility attributes that will be set later during initialization."""
        # Additional services will be set later in initialize_components()
        # after the dependency injection system is fully ready
        self.coordinator.letter_determiner = None
        self.coordinator.fade_manager = None
        self.coordinator.thumbnail_finder = None
        self.coordinator.sequence_level_evaluator = None
        self.coordinator.sequence_properties_manager = None
        self.coordinator.sequence_workbench = None
        self.coordinator.pictograph_dataset = None
        self.coordinator.pictograph_collector = None
        self.coordinator.pictograph_cache = {}  # Initialize empty cache for backward compatibility
        
        # Tab widgets for backward compatibility
        self.coordinator.construct_tab = None
        self.coordinator.learn_tab = None
        self.coordinator.settings_dialog = None
        
        self.logger.debug("Compatibility attributes created")
    
    def get_legacy_service_status(self) -> dict:
        """
        Get status of legacy services for debugging.
        
        Returns:
            Dictionary with legacy service availability
        """
        return {
            "settings_manager": self.coordinator.settings_manager is not None,
            "json_manager": self.coordinator.json_manager is not None,
            "letter_determiner": self.coordinator.letter_determiner is not None,
            "fade_manager": self.coordinator.fade_manager is not None,
            "thumbnail_finder": self.coordinator.thumbnail_finder is not None,
            "sequence_level_evaluator": self.coordinator.sequence_level_evaluator is not None,
            "sequence_properties_manager": self.coordinator.sequence_properties_manager is not None,
            "sequence_workbench": self.coordinator.sequence_workbench is not None,
            "pictograph_dataset": self.coordinator.pictograph_dataset is not None,
            "pictograph_collector": self.coordinator.pictograph_collector is not None,
            "construct_tab": self.coordinator.construct_tab is not None,
            "learn_tab": self.coordinator.learn_tab is not None,
            "settings_dialog": self.coordinator.settings_dialog is not None,
        }
    
    def validate_legacy_services(self) -> list:
        """
        Validate that all expected legacy services are available.
        
        Returns:
            List of missing services
        """
        missing_services = []
        
        # Check core services
        if not self.coordinator.settings_manager:
            missing_services.append("settings_manager")
        if not self.coordinator.json_manager:
            missing_services.append("json_manager")
        
        # Check optional services (these may be None during early initialization)
        optional_services = [
            "letter_determiner", "fade_manager", "thumbnail_finder",
            "sequence_level_evaluator", "sequence_properties_manager",
            "sequence_workbench", "pictograph_dataset", "pictograph_collector",
            "construct_tab", "learn_tab", "settings_dialog"
        ]
        
        for service_name in optional_services:
            if not hasattr(self.coordinator, service_name):
                missing_services.append(service_name)
        
        if missing_services:
            self.logger.warning(f"Missing legacy services: {missing_services}")
        else:
            self.logger.debug("All legacy services are available")
        
        return missing_services
    
    def create_migration_plan(self) -> dict:
        """
        Create a migration plan for moving away from legacy dependencies.
        
        Returns:
            Dictionary with migration recommendations
        """
        return {
            "immediate_removal": [
                "pictograph_cache"  # Can be replaced with proper cache management
            ],
            "short_term_migration": [
                "settings_manager",  # Move to dependency injection
                "json_manager",      # Move to dependency injection
            ],
            "medium_term_migration": [
                "fade_manager",      # Integrate into widget management
                "thumbnail_finder",  # Move to service layer
                "sequence_level_evaluator",  # Move to service layer
            ],
            "long_term_migration": [
                "letter_determiner",  # Already in dependency injection
                "sequence_properties_manager",  # Move to service layer
                "pictograph_dataset",  # Move to data layer
                "pictograph_collector",  # Move to service layer
            ],
            "ui_refactoring": [
                "construct_tab",     # Direct widget access should be avoided
                "learn_tab",         # Direct widget access should be avoided
                "settings_dialog",   # Direct widget access should be avoided
                "sequence_workbench" # Direct widget access should be avoided
            ]
        }
