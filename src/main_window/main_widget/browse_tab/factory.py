"""
Factory for creating BrowseTab instances with proper dependency injection.
"""

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
import logging

from core.application_context import ApplicationContext
from main_window.main_widget.core.widget_manager import WidgetFactory

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab

logger = logging.getLogger(__name__)


class BrowseTabFactory(WidgetFactory):
    """Factory for creating BrowseTab instances with dependency injection."""

    @staticmethod
    def create(parent: QWidget, app_context: ApplicationContext) -> "BrowseTab":
        """
        Create a BrowseTab instance with proper dependency injection.

        Args:
            parent: Parent widget (MainWidgetCoordinator)
            app_context: Application context with dependencies

        Returns:
            A new BrowseTab instance
        """
        logger.info("🏭 BrowseTabFactory.create() called!")
        logger.info(f"parent: {parent}")
        logger.info(f"app_context: {app_context}")

        try:
            # Import here to avoid circular dependencies
            from main_window.main_widget.browse_tab.browse_tab import BrowseTab

            # Get required services from app context
            settings_manager = app_context.settings_manager
            json_manager = app_context.json_manager

            # Get required widgets from parent coordinator
            coordinator = parent  # parent is MainWidgetCoordinator

            # Get font_color_updater widget
            font_color_updater = coordinator.widget_manager.get_widget(
                "font_color_updater"
            )

            # Inject font_color_updater into coordinator for backward compatibility
            coordinator.font_color_updater = font_color_updater

            # Create the browse tab with dependencies
            browse_tab = BrowseTab(
                main_widget=coordinator,  # Pass coordinator as main_widget for compatibility
                settings_manager=settings_manager,
                json_manager=json_manager,
            )

            # Store references for backward compatibility
            browse_tab.app_context = app_context

            logger.info("Created BrowseTab with dependency injection")
            return browse_tab

        except ImportError as e:
            logger.error(f"Failed to import BrowseTab: {e}")
            # Create a placeholder widget if the real tab can't be imported
            return QWidget(parent)
        except Exception as e:
            logger.error(f"Failed to create BrowseTab: {e}")
            raise
