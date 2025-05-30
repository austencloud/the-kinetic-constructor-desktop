"""
Migration adapters to help transition from AppContext singleton to dependency injection.

These adapters provide backward compatibility while gradually migrating to the new system.
"""

from typing import TYPE_CHECKING, Optional, Any
import logging

from .application_context import ApplicationContext

if TYPE_CHECKING:
    from interfaces.settings_manager_interface import ISettingsManager
    from interfaces.json_manager_interface import IJsonManager
    from objects.arrow.arrow import Arrow

logger = logging.getLogger(__name__)


class AppContextAdapter:
    """
    Adapter that provides the old AppContext interface using dependency injection.

    This allows existing code to continue working while we gradually migrate
    to the new dependency injection system.

    Usage:
        # Old code:
        settings = AppContext.settings_manager()

        # New code with adapter:
        adapter = AppContextAdapter(app_context)
        settings = adapter.settings_manager()
    """

    def __init__(self, app_context: ApplicationContext):
        """
        Initialize the adapter with an application context.

        Args:
            app_context: The new application context with dependency injection
        """
        self._app_context = app_context
        self._selected_arrow: Optional["Arrow"] = None

    @classmethod
    def settings_manager(cls) -> "ISettingsManager":
        """
        Get the settings manager (legacy interface).

        Note: This requires a global adapter instance to be set.
        """
        if not hasattr(cls, "_global_adapter") or cls._global_adapter is None:
            # Try to resolve from dependency container directly as fallback
            try:
                from core.dependency_container import get_container
                from interfaces.settings_manager_interface import ISettingsManager

                container = get_container()
                return container.safe_resolve(ISettingsManager, None)
            except Exception:
                # Return None instead of raising exception during initialization
                import logging

                logger = logging.getLogger(__name__)
                logger.warning("AppContextAdapter not initialized yet - returning None")
                return None

        try:
            return cls._global_adapter._app_context.settings_manager
        except Exception as e:
            # Handle circular dependency gracefully
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Circular dependency detected in settings_manager access: {e}"
            )
            return None

    @classmethod
    def json_manager(cls) -> "IJsonManager":
        """
        Get the JSON manager (legacy interface).

        Note: This requires a global adapter instance to be set.
        """
        if not hasattr(cls, "_global_adapter") or cls._global_adapter is None:
            # Try to resolve from dependency container directly as fallback
            try:
                from core.dependency_container import get_container
                from interfaces.json_manager_interface import IJsonManager

                container = get_container()
                return container.safe_resolve(IJsonManager, None)
            except Exception:
                # Return None instead of raising exception during initialization
                import logging

                logger = logging.getLogger(__name__)
                logger.warning("AppContextAdapter not initialized yet - returning None")
                return None

        try:
            return cls._global_adapter._app_context.json_manager
        except Exception as e:
            # Handle circular dependency gracefully
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Circular dependency detected in json_manager access: {e}")
            return None

    @classmethod
    def selected_arrow(cls) -> Optional["Arrow"]:
        """
        Get the selected arrow (legacy interface).

        Note: This requires a global adapter instance to be set.
        """
        if not hasattr(cls, "_global_adapter") or cls._global_adapter is None:
            return None

        return cls._global_adapter._selected_arrow

    @classmethod
    def set_selected_arrow(cls, arrow: Optional["Arrow"]) -> None:
        """
        Set the selected arrow (legacy interface).

        Note: This requires a global adapter instance to be set.
        """
        if not hasattr(cls, "_global_adapter") or cls._global_adapter is None:
            logger.warning(
                "AppContextAdapter not initialized. Cannot set selected arrow."
            )
            return

        cls._global_adapter._selected_arrow = arrow
        cls._global_adapter._app_context.selected_arrow = arrow

    @classmethod
    def set_global_adapter(cls, adapter: "AppContextAdapter") -> None:
        """
        Set the global adapter instance for legacy compatibility.

        Args:
            adapter: The adapter instance to use globally
        """
        cls._global_adapter = adapter
        logger.info("Global AppContextAdapter set for legacy compatibility")

    @classmethod
    def clear_global_adapter(cls) -> None:
        """Clear the global adapter instance."""
        if hasattr(cls, "_global_adapter"):
            cls._global_adapter = None
        logger.info("Global AppContextAdapter cleared")

    # Instance methods for direct use
    def get_settings_manager(self) -> "ISettingsManager":
        """Get the settings manager through dependency injection."""
        return self._app_context.settings_manager

    def get_json_manager(self) -> "IJsonManager":
        """Get the JSON manager through dependency injection."""
        return self._app_context.json_manager

    def get_selected_arrow(self) -> Optional["Arrow"]:
        """Get the currently selected arrow."""
        return self._selected_arrow

    def set_arrow(self, arrow: Optional["Arrow"]) -> None:
        """Set the currently selected arrow."""
        self._selected_arrow = arrow
        self._app_context.selected_arrow = arrow

    def get_service(self, service_type: type) -> Any:
        """
        Get any service from the dependency container.

        Args:
            service_type: The type/interface of the service to resolve

        Returns:
            The resolved service instance
        """
        return self._app_context.get_service(service_type)


class ComponentMigrationHelper:
    """
    Helper class to migrate individual components to use dependency injection.

    This provides utilities to gradually migrate components without breaking
    existing functionality.
    """

    def __init__(self, app_context: ApplicationContext):
        """
        Initialize the migration helper.

        Args:
            app_context: The application context with dependency injection
        """
        self.app_context = app_context

    def migrate_component(
        self, component: Any, component_name: str = "Unknown"
    ) -> None:
        """
        Migrate a component to use dependency injection.

        This method attempts to inject dependencies into a component
        using various common patterns.

        Args:
            component: The component to migrate
            component_name: Name of the component for logging
        """
        try:
            # Try to set app_context if the component supports it
            if hasattr(component, "set_app_context"):
                component.set_app_context(self.app_context)
                logger.info(f"Injected app_context into {component_name}")

            # Try to set individual dependencies
            if hasattr(component, "settings_manager"):
                component.settings_manager = self.app_context.settings_manager
                logger.debug(f"Injected settings_manager into {component_name}")

            if hasattr(component, "json_manager"):
                component.json_manager = self.app_context.json_manager
                logger.debug(f"Injected json_manager into {component_name}")

            # Try to call a dependency injection method if it exists
            if hasattr(component, "inject_dependencies"):
                component.inject_dependencies(self.app_context)
                logger.info(f"Called inject_dependencies on {component_name}")

            logger.info(f"Successfully migrated component: {component_name}")

        except Exception as e:
            logger.error(f"Failed to migrate component {component_name}: {e}")

    def create_legacy_wrapper(self, component: Any) -> Any:
        """
        Create a wrapper around a component that provides legacy compatibility.

        Args:
            component: The component to wrap

        Returns:
            A wrapper that provides both old and new interfaces
        """

        class LegacyWrapper:
            def __init__(self, wrapped_component, app_context):
                self._component = wrapped_component
                self._app_context = app_context

            def __getattr__(self, name):
                # Delegate to the wrapped component
                return getattr(self._component, name)

            # Provide legacy methods
            def get_settings_manager(self):
                return self._app_context.settings_manager

            def get_json_manager(self):
                return self._app_context.json_manager

        return LegacyWrapper(component, self.app_context)


def setup_legacy_compatibility(app_context: ApplicationContext) -> AppContextAdapter:
    """
    Set up legacy compatibility for existing code.

    This function creates and configures the global adapter that allows
    existing code using AppContext.settings_manager() to continue working.

    Args:
        app_context: The new application context

    Returns:
        The configured adapter
    """
    adapter = AppContextAdapter(app_context)
    AppContextAdapter.set_global_adapter(adapter)

    logger.info("Legacy compatibility set up successfully")
    return adapter


def teardown_legacy_compatibility() -> None:
    """
    Tear down legacy compatibility.

    This should be called when the application is shutting down
    or when legacy compatibility is no longer needed.
    """
    AppContextAdapter.clear_global_adapter()
    logger.info("Legacy compatibility torn down")
