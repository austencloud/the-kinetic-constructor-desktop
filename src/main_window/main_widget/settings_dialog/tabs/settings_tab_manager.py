"""
Settings tab manager for the modern settings dialog.

Handles tab creation, organization, and management.
"""

from typing import TYPE_CHECKING, Dict, List
from PyQt6.QtWidgets import QWidget, QStackedWidget, QListWidget
import logging

if TYPE_CHECKING:
    from src.core.application_context import ApplicationContext
    from ..core.settings_state_manager import SettingsStateManager

logger = logging.getLogger(__name__)


class SettingsTabImportError(Exception):
    """
    Exception raised when settings tabs fail to import or create.

    This exception is used to provide clear error messages when the settings
    dialog cannot be properly initialized due to missing or broken tab implementations.
    """

    pass


class SettingsTabManager:
    """
    Manages settings dialog tabs with strict error handling.

    Responsibilities:
    - Create tab widgets
    - Organize tab order
    - Populate sidebar and content area
    - Fail fast on import errors (no silent fallbacks)
    """

    def __init__(
        self,
        settings_manager,
        state_manager: "SettingsStateManager",
        app_context: "ApplicationContext" = None,
        parent_dialog=None,
    ):
        self.settings_manager = settings_manager
        self.state_manager = state_manager
        self.app_context = app_context
        self.parent_dialog = parent_dialog

        # Tab configuration
        self.tab_order = [
            "General",
            "Prop Type",
            "Visibility",
            "Beat Layout",
            "Image Export",
            "Codex Exporter",
        ]

        self.tabs: Dict[str, QWidget] = {}

        # Validate all tabs can be imported before proceeding
        self._validate_all_tabs_available()

    def _validate_all_tabs_available(self):
        """
        Validate that all required tabs can be imported.

        This method performs early validation to ensure all tab implementations
        are available before attempting to create the settings dialog.

        Raises:
            SettingsTabImportError: If any required tab cannot be imported
        """
        try:
            logger.debug("Validating all settings tabs are available...")

            # Test import all required tab implementations
            from ..ui.prop_type.prop_type_tab import PropTypeTab
            from ..ui.visibility.visibility_tab import VisibilityTab
            from ..ui.beat_layout.beat_layout_tab import BeatLayoutTab
            from ..ui.image_export.image_export_tab import ImageExportTab
            from ..ui.codex_exporter.codex_exporter_tab import CodexExporterTab
            from ..ui.general.general_tab import GeneralTab

            logger.debug("✅ All settings tabs validated successfully")

        except ImportError as e:
            error_msg = f"Critical settings tab import failure: {e}"
            logger.error(error_msg)
            logger.error("The application cannot start with missing settings tabs.")
            logger.error(
                "Please check that all settings tab files are present and properly implemented."
            )
            raise SettingsTabImportError(error_msg) from e

    def create_tabs(
        self, sidebar: QListWidget, content_area: QStackedWidget
    ) -> Dict[str, QWidget]:
        """
        Create all tab widgets and populate sidebar and content area.

        This method will fail fast if any tab cannot be created properly.

        Args:
            sidebar: The sidebar list widget
            content_area: The stacked widget for tab content

        Returns:
            Dictionary of created tab widgets

        Raises:
            SettingsTabImportError: If any tab fails to import or create
        """
        try:
            logger.info("Creating settings dialog tabs...")

            # Create all tab widgets (will raise exception on failure)
            self.tabs = self._create_all_tabs()

            # Populate sidebar and content area
            self._populate_sidebar_and_content(sidebar, content_area)

            logger.info(f"Successfully created {len(self.tabs)} tab widgets")
            return self.tabs

        except Exception as e:
            error_msg = f"Critical error creating settings tabs: {e}"
            logger.error(error_msg)
            raise SettingsTabImportError(error_msg) from e

    def _create_all_tabs(self) -> Dict[str, QWidget]:
        """
        Create all tab widget instances with strict error handling.

        Returns:
            Dictionary of created tab widgets

        Raises:
            SettingsTabImportError: If any tab fails to import or create
        """
        try:
            # Import all tab implementations (will fail fast on import errors)
            from ..ui.prop_type.prop_type_tab import PropTypeTab
            from ..ui.visibility.visibility_tab import VisibilityTab
            from ..ui.beat_layout.beat_layout_tab import BeatLayoutTab
            from ..ui.image_export.image_export_tab import ImageExportTab
            from ..ui.codex_exporter.codex_exporter_tab import CodexExporterTab
            from ..ui.general.general_tab import GeneralTab

            logger.debug("All tab imports successful")

            # Create tab instances (will fail fast on creation errors)
            tabs = {
                "General": GeneralTab(
                    self.settings_manager, self.state_manager, self.parent_dialog
                ),
                "Prop Type": PropTypeTab(self.parent_dialog),
                "Visibility": VisibilityTab(self.parent_dialog),
                "Beat Layout": BeatLayoutTab(self.parent_dialog),
                "Image Export": ImageExportTab(self.parent_dialog),
                "Codex Exporter": CodexExporterTab(self.parent_dialog),
            }

            logger.debug("All tab instances created successfully")
            return tabs

        except ImportError as e:
            error_msg = f"Failed to import settings tab: {e}"
            logger.error(error_msg)
            raise SettingsTabImportError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create settings tab instance: {e}"
            logger.error(error_msg)
            raise SettingsTabImportError(error_msg) from e

    def _populate_sidebar_and_content(
        self, sidebar: QListWidget, content_area: QStackedWidget
    ):
        """Populate the sidebar and content area with tabs."""
        for tab_name in self.tab_order:
            if tab_name in self.tabs:
                tab_widget = self.tabs[tab_name]
                logger.debug(f"Adding tab: {tab_name}")

                # Add to sidebar
                sidebar.addItem(tab_name)

                # Add to content area
                content_area.addWidget(tab_widget)

        logger.debug(f"Sidebar has {sidebar.count()} items")
        logger.debug(f"Content area has {content_area.count()} widgets")

        # Set default selection
        if sidebar.count() > 0:
            sidebar.setCurrentRow(0)
            content_area.setCurrentIndex(0)
            logger.debug("Set default selection to first tab")

    def get_tab_order(self) -> List[str]:
        """Get the tab order list."""
        return self.tab_order.copy()

    def get_tab(self, tab_name: str) -> QWidget:
        """Get a specific tab widget."""
        return self.tabs.get(tab_name)

    def refresh_all_tabs(self):
        """Refresh all tab contents from current settings."""
        try:
            for tab_name, tab_widget in self.tabs.items():
                if hasattr(tab_widget, "refresh_settings"):
                    tab_widget.refresh_settings()
        except Exception as e:
            logger.error(f"Error refreshing tabs: {e}")
