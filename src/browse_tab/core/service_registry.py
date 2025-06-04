"""
Service registry for dependency injection in browse tab v2.

This module provides a centralized service registry for managing
dependencies and service lifecycle.
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional, Callable
from dataclasses import dataclass
import inspect

from .interfaces import (
    ISequenceService,
    IFilterService,
    ICacheService,
    IImageLoader,
    IStateManager,
    IPerformanceMonitor,
    BrowseTabConfig,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed."""

    service_type: Type
    implementation_type: Type
    singleton: bool = True
    factory: Optional[Callable] = None
    dependencies: Optional[Dict[str, str]] = None


class ServiceRegistry:
    """
    Centralized service registry for dependency injection.

    Provides:
    - Service registration and resolution
    - Dependency injection
    - Singleton management
    - Service lifecycle management
    """

    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        self._config: Optional[BrowseTabConfig] = None

        logger.info("ServiceRegistry initialized")

    def configure(self, config: BrowseTabConfig) -> None:
        """Configure the service registry with application config."""
        self._config = config
        logger.info("ServiceRegistry configured")

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        dependencies: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a singleton service."""
        service_name = service_type.__name__

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            singleton=True,
            dependencies=dependencies,
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered singleton service: {service_name}")

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        dependencies: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a transient service (new instance each time)."""
        service_name = service_type.__name__

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            singleton=False,
            dependencies=dependencies,
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered transient service: {service_name}")

    def register_factory(
        self, service_type: Type[T], factory: Callable[[], T], singleton: bool = True
    ) -> None:
        """Register a service with a custom factory function."""
        service_name = service_type.__name__

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=service_type,
            singleton=singleton,
            factory=factory,
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered factory service: {service_name}")

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register an existing instance as a singleton."""
        service_name = service_type.__name__
        self._instances[service_name] = instance

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=type(instance),
            singleton=True,
        )

        self._services[service_name] = descriptor
        logger.debug(f"Registered instance service: {service_name}")

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance."""
        service_name = service_type.__name__

        # Check if already instantiated (for singletons)
        if service_name in self._instances:
            return self._instances[service_name]

        # Check if service is registered
        if service_name not in self._services:
            raise ValueError(f"Service not registered: {service_name}")

        descriptor = self._services[service_name]

        try:
            # Create instance
            if descriptor.factory:
                instance = descriptor.factory()
            else:
                instance = self._create_instance(descriptor)

            # Store singleton instances
            if descriptor.singleton:
                self._instances[service_name] = instance

            logger.debug(f"Resolved service: {service_name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to resolve service {service_name}: {e}")
            raise

    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resolve a service instance, returning None if not found."""
        try:
            return self.resolve(service_type)
        except ValueError:
            return None

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type.__name__ in self._services

    def get_registered_services(self) -> Dict[str, ServiceDescriptor]:
        """Get all registered services."""
        return self._services.copy()

    def clear(self) -> None:
        """Clear all services and instances."""
        self._services.clear()
        self._instances.clear()
        logger.info("ServiceRegistry cleared")

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance of a service."""
        implementation_type = descriptor.implementation_type

        # Get constructor parameters
        constructor = implementation_type.__init__
        sig = inspect.signature(constructor)

        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Check if parameter has a type annotation
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation

                # Special handling for config
                if param_type == BrowseTabConfig or param_name == "config":
                    if self._config:
                        kwargs[param_name] = self._config
                    continue

                # Try to resolve dependency
                try:
                    dependency = self.resolve(param_type)
                    kwargs[param_name] = dependency
                except ValueError:
                    # Check if parameter has a default value
                    if param.default != inspect.Parameter.empty:
                        continue
                    else:
                        logger.warning(
                            f"Could not resolve dependency {param_type} for {implementation_type}"
                        )

        # Create instance
        return implementation_type(**kwargs)


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


def configure_services(config: BrowseTabConfig) -> ServiceRegistry:
    """Configure services with default implementations."""
    registry = get_service_registry()
    registry.configure(config)

    # Import service implementations
    from ..services.sequence_service import SequenceService
    from ..services.filter_service import FilterService
    from ..services.cache_service import CacheService
    from ..services.qt_native_image_loader import QtNativeImageLoader
    from ..core.state import StateManager

    # Register core services with proper dependencies
    registry.register_singleton(ISequenceService, SequenceService)
    registry.register_singleton(IFilterService, FilterService)

    # Use global cache service if available (for startup optimization)
    def create_cache_service():
        from ..services.cache_service import get_global_cache_service, CacheService

        global_cache = get_global_cache_service()
        if global_cache is not None:
            logger.info("Using global cache service with pre-cached thumbnails")
            return global_cache
        else:
            logger.info("Creating new cache service (no global cache available)")
            return CacheService(config)

    registry.register_factory(ICacheService, create_cache_service)

    # Register image loader with explicit dependency
    def create_image_loader():
        cache_service = registry.resolve(ICacheService)
        return QtNativeImageLoader(cache_service=cache_service, config=config)

    registry.register_factory(IImageLoader, create_image_loader)
    registry.register_singleton(IStateManager, StateManager)

    logger.info("Default services configured")
    return registry


def resolve_service(service_type: Type[T]) -> T:
    """Convenience function to resolve a service."""
    return get_service_registry().resolve(service_type)


def register_service(
    service_type: Type[T], implementation_type: Type[T], singleton: bool = True
) -> None:
    """Convenience function to register a service."""
    registry = get_service_registry()
    if singleton:
        registry.register_singleton(service_type, implementation_type)
    else:
        registry.register_transient(service_type, implementation_type)


class ServiceScope:
    """Context manager for service scoping."""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._original_instances = {}

    def __enter__(self):
        # Save current instances
        self._original_instances = self.registry._instances.copy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original instances
        self.registry._instances = self._original_instances


# Decorators for dependency injection


def inject(service_type: Type[T]) -> Callable:
    """Decorator to inject a service into a method."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            service = resolve_service(service_type)
            return func(service, *args, **kwargs)

        return wrapper

    return decorator


def auto_inject(func):
    """Decorator to automatically inject services based on type annotations."""
    sig = inspect.signature(func)

    def wrapper(*args, **kwargs):
        # Resolve dependencies based on type annotations
        for param_name, param in sig.parameters.items():
            if param_name not in kwargs and param.annotation != inspect.Parameter.empty:
                try:
                    service = resolve_service(param.annotation)
                    kwargs[param_name] = service
                except ValueError:
                    # Service not registered, skip
                    pass

        return func(*args, **kwargs)

    return wrapper
