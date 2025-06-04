"""
Factory for creating SequenceCardTab instances with proper dependency injection.
"""

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
import logging

from core.application_context import ApplicationContext
from main_window.main_widget.core.widget_manager import WidgetFactory

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab

logger = logging.getLogger(__name__)


class SequenceCardTabFactory(WidgetFactory):
    """Factory for creating SequenceCardTab instances with dependency injection."""

    @staticmethod
    def create(parent: QWidget, app_context: ApplicationContext) -> "SequenceCardTab":
        """
        Create a SequenceCardTab instance with proper dependency injection.

        Args:
            parent: Parent widget (MainWidgetCoordinator)
            app_context: Application context with dependencies

        Returns:
            A new SequenceCardTab instance
        """
        try:
            # Import here to avoid circular dependencies
            from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab

            # Get required services from app context
            settings_manager = app_context.settings_manager
            json_manager = app_context.json_manager

            # Create the sequence card tab with dependencies
            sequence_card_tab = SequenceCardTab(
                main_widget=parent,  # Pass coordinator as main_widget for compatibility
                settings_manager=settings_manager,
                json_manager=json_manager,
            )

            # Store references for backward compatibility
            sequence_card_tab.app_context = app_context

            logger.info("Created SequenceCardTab with dependency injection")
            return sequence_card_tab

        except ImportError as e:
            logger.error(f"Failed to import SequenceCardTab: {e}")
            # Create a placeholder widget if the real tab can't be imported
            return QWidget(parent)
        except Exception as e:
            import traceback

            logger.error(f"Failed to create SequenceCardTab: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
