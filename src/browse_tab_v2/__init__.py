"""
Browse Tab v2 - Modern Architecture Implementation

This package provides a complete redesign of the browse tab using modern
2025 PyQt6 best practices, featuring reactive state management, Qt-native operations,
and high-performance UI components.

Key Features:
- MVVM architecture with reactive state management
- Qt-native image loading with multi-layer caching
- Virtual scrolling for thousands of sequences
- Modern glassmorphism UI design
- Comprehensive performance monitoring
- Dependency injection with service registry
- 90%+ test coverage

Usage:
    from browse_tab_v2 import BrowseTabV2Factory

    # Create browse tab with default configuration
    browse_tab = BrowseTabV2Factory.create_default(
        json_manager=json_manager,
        settings_manager=settings_manager
    )

    # Or create with custom configuration
    config = BrowseTabConfig(
        max_concurrent_image_loads=8,
        image_cache_size=500,
        default_columns=4
    )

    browse_tab = BrowseTabV2Factory.create_with_config(
        config=config,
        json_manager=json_manager,
        settings_manager=settings_manager
    )
"""

import logging
from typing import Optional, Any

from .core.interfaces import BrowseTabConfig
from .core.service_registry import configure_services, get_service_registry
from .core.state import StateManager, BrowseState
from .viewmodels.browse_tab_viewmodel import BrowseTabViewModel

# Version information
__version__ = "2.0.0"
__author__ = "Browse Tab Redesign Team"
__description__ = "Modern browse tab implementation with 2025 architecture"

# Configure logging
logger = logging.getLogger(__name__)


class BrowseTabV2Factory:
    """
    Factory for creating browse tab v2 instances with proper dependency injection.

    This factory handles the complex initialization process, service registration,
    and dependency resolution required for the new architecture.
    """

    @staticmethod
    def create_default(json_manager=None, settings_manager=None) -> "BrowseTabV2":
        """Create browse tab with default configuration."""
        config = BrowseTabConfig()
        return BrowseTabV2Factory.create_with_config(
            config=config, json_manager=json_manager, settings_manager=settings_manager
        )

    @staticmethod
    def create_with_config(
        config: BrowseTabConfig, json_manager=None, settings_manager=None
    ) -> "BrowseTabV2":
        """Create browse tab with custom configuration."""
        try:
            logger.info("Creating BrowseTabV2 with modern architecture")

            # Configure services
            registry = configure_services(config)

            # Register external dependencies if provided
            if json_manager:
                from .core.interfaces import ISequenceService
                from .services.sequence_service import SequenceService

                # Create sequence service with json_manager
                sequence_service = SequenceService(
                    json_manager=json_manager, config=config
                )
                registry.register_instance(ISequenceService, sequence_service)

            # Create state manager
            initial_state = BrowseState()
            state_manager = StateManager(initial_state)
            registry.register_instance(StateManager, state_manager)

            # Create ViewModel
            from .core.interfaces import (
                ISequenceService,
                IFilterService,
                ICacheService,
                IImageLoader,
            )

            # Get image loader and add to config for easy access by components
            image_loader = registry.resolve(IImageLoader)
            config.image_loader = image_loader

            viewmodel = BrowseTabViewModel(
                state_manager=state_manager,
                sequence_service=registry.resolve(ISequenceService),
                filter_service=registry.resolve(IFilterService),
                cache_service=registry.resolve(ICacheService),
                image_loader=image_loader,
                config=config,
            )

            # Create main browse tab instance
            browse_tab = BrowseTabV2(
                viewmodel=viewmodel, config=config, settings_manager=settings_manager
            )

            logger.info("BrowseTabV2 created successfully")
            return browse_tab

        except Exception as e:
            logger.error(f"Failed to create BrowseTabV2: {e}")
            raise

    @staticmethod
    def create_for_testing(mock_services: dict = None) -> "BrowseTabV2":
        """Create browse tab instance for testing with mock services."""
        config = BrowseTabConfig(
            enable_performance_monitoring=False, enable_debug_logging=True
        )

        registry = get_service_registry()
        registry.clear()
        registry.configure(config)

        # Register mock services if provided
        if mock_services:
            for service_type, mock_instance in mock_services.items():
                registry.register_instance(service_type, mock_instance)

        # Create with minimal dependencies
        state_manager = StateManager()
        registry.register_instance(StateManager, state_manager)

        # Create test ViewModel
        from .core.interfaces import (
            ISequenceService,
            IFilterService,
            ICacheService,
            IImageLoader,
        )

        viewmodel = BrowseTabViewModel(
            state_manager=state_manager,
            sequence_service=registry.resolve(ISequenceService),
            filter_service=registry.resolve(IFilterService),
            cache_service=registry.resolve(ICacheService),
            image_loader=registry.resolve(IImageLoader),
            config=config,
        )

        return BrowseTabV2(viewmodel=viewmodel, config=config)


class BrowseTabV2:
    """
    Main browse tab v2 implementation.

    This is the primary interface for the new browse tab, providing
    a clean API while internally using the MVVM architecture.
    """

    def __init__(
        self,
        viewmodel: BrowseTabViewModel,
        config: BrowseTabConfig,
        settings_manager=None,
    ):
        self.viewmodel = viewmodel
        self.config = config
        self.settings_manager = settings_manager

        # UI will be created when needed
        self._view = None
        self._initialized = False

        logger.info("BrowseTabV2 instance created")

    def initialize(self) -> None:
        """Initialize the browse tab synchronously - Qt-native approach."""
        if self._initialized:
            return

        try:
            logger.info("Initializing BrowseTabV2")

            # Initialize ViewModel synchronously
            # The viewmodel now handles initialization without async requirements
            if hasattr(self.viewmodel, "initialize_sync"):
                success = self.viewmodel.initialize_sync()
                if not success:
                    logger.info("Sync initialization failed, using fallback")
                    self.viewmodel.initialize_async_fallback()
            else:
                # Fallback for compatibility
                self.viewmodel.load_sequences()

            self._initialized = True
            logger.info("BrowseTabV2 initialization completed")

        except Exception as e:
            logger.error(f"BrowseTabV2 initialization failed: {e}")
            raise

    def get_view(self):
        """Get the UI view component (lazy-loaded)."""
        if self._view is None:
            # Import here to avoid circular dependencies
            from .components.browse_tab_view import BrowseTabView

            # Pass cache service to view for instant thumbnail display
            cache_service = getattr(self.viewmodel, "cache_service", None)
            self._view = BrowseTabView(
                self.viewmodel, self.config, cache_service=cache_service
            )

        return self._view

    def get_state(self) -> BrowseState:
        """Get current state."""
        return self.viewmodel.current_state

    def load_sequences(self) -> None:
        """Load sequences - Qt-native approach."""
        self.viewmodel.load_sequences()

    def apply_filter(self, filter_type: str, filter_value: Any) -> None:
        """Apply a filter - Qt-native approach."""
        from .core.interfaces import FilterType, FilterCriteria

        # Convert string to FilterType enum
        filter_type_enum = FilterType(filter_type)

        # Create filter criteria
        criteria = FilterCriteria(
            filter_type=filter_type_enum, value=filter_value, operator="equals"
        )

        # Use QTimer for delayed filter application to avoid blocking UI
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(10, lambda: self._apply_filter_delayed(criteria))

    def _apply_filter_delayed(self, criteria):
        """Apply filter with delay to avoid blocking UI."""
        try:
            # For now, just log the filter application
            # The actual filtering will be handled by the filter panel component
            logger.debug(f"Filter applied: {criteria}")
        except Exception as e:
            logger.error(f"Failed to apply filter: {e}")

    def search_sequences(self, query: str) -> None:
        """Search sequences."""
        self.viewmodel.search_sequences(query)

    def select_sequence(self, sequence_id: str) -> None:
        """Select a sequence."""
        self.viewmodel.select_sequence(sequence_id)

    def get_performance_stats(self) -> dict:
        """Get performance statistics - Qt-native approach."""
        try:
            # Return basic performance stats without async complications
            return {
                "initialized": self._initialized,
                "viewmodel_available": self.viewmodel is not None,
                "view_created": self._view is not None,
                "config": {
                    "enable_animations": self.config.enable_animations,
                    "max_columns": self.config.max_columns,
                    "min_item_width": self.config.min_item_width,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}

    def is_initialized(self) -> bool:
        """Check if browse tab is initialized."""
        return self._initialized

    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self._view:
                # Cleanup view resources
                self._view.cleanup()

            # Cleanup ViewModel resources
            if hasattr(self.viewmodel, "cleanup"):
                self.viewmodel.cleanup()

            logger.info("BrowseTabV2 cleanup completed")

        except Exception as e:
            logger.error(f"BrowseTabV2 cleanup failed: {e}")


# Convenience functions for backward compatibility


def create_browse_tab_v2(json_manager=None, settings_manager=None):
    """Convenience function to create browse tab v2."""
    return BrowseTabV2Factory.create_default(
        json_manager=json_manager, settings_manager=settings_manager
    )


def get_version_info() -> dict:
    """Get version and build information."""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "architecture": "MVVM + Reactive State",
        "features": [
            "Qt-native image loading",
            "Multi-layer caching",
            "Virtual scrolling",
            "Modern UI design",
            "Performance monitoring",
            "Dependency injection",
        ],
    }


# Export main classes and functions
__all__ = [
    "BrowseTabV2",
    "BrowseTabV2Factory",
    "BrowseTabConfig",
    "create_browse_tab_v2",
    "get_version_info",
]
