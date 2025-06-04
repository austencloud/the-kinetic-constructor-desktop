"""
Factory for creating BrowseTab instances with proper dependency injection.

UPDATED: Now uses Browse Tab v2 with modern architecture while maintaining
compatibility with the existing application interface.
"""

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
import logging

from core.application_context import ApplicationContext
from main_window.main_widget.core.widget_manager import WidgetFactory

if TYPE_CHECKING:
    from browse_tab_v2.integration.browse_tab_adapter import BrowseTabV2Adapter

logger = logging.getLogger(__name__)


class BrowseTabFactory(WidgetFactory):
    """Factory for creating BrowseTab instances with dependency injection."""

    @staticmethod
    def create(
        parent: QWidget, app_context: ApplicationContext
    ) -> "BrowseTabV2Adapter":
        """
        Create a BrowseTab v2 instance with proper dependency injection.

        Args:
            parent: Parent widget (MainWidgetCoordinator)
            app_context: Application context with dependencies

        Returns:
            A new BrowseTabV2Adapter instance (compatible with old BrowseTab interface)
        """
        logger.info("🏭 BrowseTabFactory.create() called - Creating Browse Tab v2!")
        logger.info(f"parent: {parent}")
        logger.info(f"app_context: {app_context}")

        try:
            # Import the new browse tab v2 adapter
            from browse_tab_v2.integration.browse_tab_adapter import BrowseTabV2Adapter

            # Extract dependencies from app_context
            settings_manager = app_context.settings_manager
            json_manager = app_context.json_manager

            logger.info("Creating Browse Tab v2 with modern architecture...")
            logger.info(f"Settings manager: {settings_manager}")
            logger.info(f"JSON manager: {json_manager}")

            # Configuration will be handled internally by the adapter

            # Create the browse tab v2 adapter with proper dependencies
            browse_tab_v2 = BrowseTabV2Adapter(
                json_manager=json_manager,
                settings_manager=settings_manager,
                parent=parent,
            )

            # Store references for backward compatibility
            browse_tab_v2.app_context = app_context

            # Add compatibility attributes for existing code that expects them
            browse_tab_v2.sequence_viewer = (
                BrowseTabFactory._create_sequence_viewer_placeholder()
            )

            logger.info("✅ Created Browse Tab v2 with modern architecture!")
            logger.info("Features enabled:")
            logger.info("  • Reactive state management")
            logger.info("  • Async data loading")
            logger.info("  • Multi-layer caching")
            logger.info("  • Performance monitoring")
            logger.info("  • MVVM architecture")

            return browse_tab_v2

        except ImportError as e:
            logger.error(f"Failed to import Browse Tab v2: {e}")
            logger.error("Falling back to placeholder widget")
            # Create a placeholder widget if the new tab can't be imported
            placeholder = QWidget(parent)
            placeholder.setStyleSheet(
                """
                QWidget {
                    background-color: #f0f0f0;
                    border: 2px dashed #ccc;
                }
            """
            )
            from PyQt6.QtWidgets import QVBoxLayout, QLabel

            layout = QVBoxLayout(placeholder)
            label = QLabel("Browse Tab v2 failed to load\nCheck console for errors")
            label.setStyleSheet("color: #666; font-size: 14px; text-align: center;")
            layout.addWidget(label)
            return placeholder
        except Exception as e:
            logger.error(f"Failed to create Browse Tab v2: {e}")
            import traceback

            traceback.print_exc()
            raise

    @staticmethod
    def _create_sequence_viewer_placeholder():
        """
        Create a placeholder sequence viewer for backward compatibility.

        The old browse tab had a sequence_viewer attribute that was used
        in the main widget layout. This creates a compatible placeholder.
        """
        from PyQt6.QtWidgets import QLabel

        # Create a simple placeholder widget
        placeholder = QLabel("Sequence Viewer (Browse Tab v2)")
        placeholder.setStyleSheet(
            """
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }
        """
        )

        # Add a note about the new architecture
        placeholder.setToolTip(
            "This is a placeholder for the old sequence viewer.\n"
            "In Browse Tab v2, sequence viewing is integrated into the main view."
        )

        logger.info("Created sequence viewer placeholder for compatibility")
        return placeholder
