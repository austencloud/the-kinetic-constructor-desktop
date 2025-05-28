from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
import logging

from main_window.main_widget.browse_tab.browse_tab_filter_controller import (
    BrowseTabFilterController,
)
from main_window.main_widget.browse_tab.browse_tab_persistence_manager import (
    BrowseTabPersistenceManager,
)
from main_window.main_widget.metadata_extractor import MetaDataExtractor
from interfaces.settings_manager_interface import ISettingsManager
from interfaces.json_manager_interface import IJsonManager

from .sequence_picker.sequence_picker import SequencePicker
from .browse_tab_filter_manager import BrowseTabFilterManager
from .browse_tab_getter import BrowseTabGetter
from .browse_tab_ui_updater import BrowseTabUIUpdater
from .deletion_handler.browse_tab_deletion_handler import BrowseTabDeletionHandler
from .browse_tab_selection_handler import BrowseTabSelectionHandler
from .sequence_viewer.sequence_viewer import SequenceViewer
from .browse_tab_state import BrowseTabState
from .lazy_loading.browse_tab_lazy_loader import BrowseTabLazyLoader

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class BrowseTab(QWidget):
    def __init__(
        self,
        main_widget: "MainWidget",
        settings_manager: ISettingsManager,
        json_manager: IJsonManager,
    ) -> None:
        # Debug: Log the very start of browse tab creation
        import logging

        logger = logging.getLogger(__name__)
        logger.info("🚀 BrowseTab.__init__ called!")
        logger.info(f"main_widget: {main_widget}")
        logger.info(f"settings_manager: {settings_manager}")
        logger.info(f"json_manager: {json_manager}")

        super().__init__()
        logger.info("✅ super().__init__() completed")

        self.main_widget = main_widget
        logger.info("✅ main_widget assigned")

        self.main_widget.splash_screen.updater.update_progress("BrowseTab")
        logger.info("✅ splash screen updated")

        self.settings_manager = settings_manager
        self.json_manager = json_manager
        self.browse_settings = settings_manager.browse_settings
        self.state = BrowseTabState(self.browse_settings)
        self.metadata_extractor = MetaDataExtractor()

        self.ui_updater = BrowseTabUIUpdater(self)

        self.filter_manager = BrowseTabFilterManager(self)
        self.filter_controller = BrowseTabFilterController(self)

        # Debug: Log sequence picker creation
        import logging

        logger = logging.getLogger(__name__)
        logger.info("🎯 Creating SequencePicker in BrowseTab...")

        self.sequence_picker = SequencePicker(self)
        logger.info(f"✅ SequencePicker created: {self.sequence_picker}")

        logger.info("🎯 Creating SequenceViewer in BrowseTab...")
        self.sequence_viewer = SequenceViewer(self)
        logger.info(f"✅ SequenceViewer created: {self.sequence_viewer}")

        self._setup_browse_tab_layout()

        self.deletion_handler = BrowseTabDeletionHandler(self)
        self.selection_handler = BrowseTabSelectionHandler(self)
        self.get = BrowseTabGetter(self)

        self.persistence_manager = BrowseTabPersistenceManager(self)

        # Initialize lazy loading system
        self._lazy_loader: Optional[BrowseTabLazyLoader] = None
        self._lazy_loading_enabled = False
        self._initialize_lazy_loading()

        # FILTER RESPONSIVENESS FIX: Simple deferred initialization
        QTimer.singleShot(100, self._complete_initialization)

    def _setup_browse_tab_layout(self):
        from PyQt6.QtWidgets import QHBoxLayout, QStackedWidget

        # ARCHITECTURAL FIX: Create internal stack for filter_stack and sequence_picker
        # This eliminates the need for main widget to manage browse tab internals
        self.internal_left_stack = QStackedWidget()
        self.internal_left_stack.addWidget(
            self.sequence_picker.filter_stack
        )  # 0 - Filter selection
        self.internal_left_stack.addWidget(
            self.sequence_picker
        )  # 1 - Sequence list with control panel

        # Start with filter stack visible (filter selection mode)
        self.internal_left_stack.setCurrentIndex(0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            self.internal_left_stack, 2
        )  # 2/3 width (66.7%) - Internal stack instead of sequence_picker
        layout.addWidget(self.sequence_viewer, 1)  # 1/3 width (33.3%)

        self.setLayout(layout)

    def _initialize_lazy_loading(self) -> None:
        """Initialize the lazy loading system for the browse tab."""
        try:
            # Create lazy loader with grid configuration
            scroll_area = self.sequence_picker.scroll_widget.scroll_area
            self._lazy_loader = BrowseTabLazyLoader(
                scroll_area=scroll_area,
                grid_columns=3,  # Browse tab uses 3 columns
                buffer_rows=7,  # Load 7 rows ahead/behind viewport
            )

            # Enable lazy loading for the scroll widget
            self.sequence_picker.scroll_widget.enable_lazy_loading(self._lazy_loader)
            self._lazy_loading_enabled = True

            logger = logging.getLogger(__name__)
            logger.info("✅ Lazy loading system initialized for browse tab")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize lazy loading: {e}")
            self._lazy_loading_enabled = False

    def _ensure_filter_responsiveness(self):
        """
        Ensure filter buttons are responsive immediately upon tab display.

        This fixes the issue where first clicks on filter buttons are ignored.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("🔧 Ensuring filter button responsiveness...")

        try:
            # Force widget activation and focus
            self.setEnabled(True)
            self.activateWindow()

            # Ensure filter stack is properly initialized
            if hasattr(self, "sequence_picker") and hasattr(
                self.sequence_picker, "filter_stack"
            ):
                filter_stack = self.sequence_picker.filter_stack
                filter_stack.setEnabled(True)
                filter_stack.activateWindow()

                # Force update of all filter widgets
                self._activate_filter_widgets(filter_stack)

            # Ensure internal stack is properly set up
            if hasattr(self, "internal_left_stack"):
                self.internal_left_stack.setEnabled(True)
                # Start with filter stack visible for immediate responsiveness
                self.internal_left_stack.setCurrentIndex(0)

            logger.info("✅ Filter button responsiveness ensured")

        except Exception as e:
            logger.warning(f"Error ensuring filter responsiveness: {e}")

    def _activate_filter_widgets(self, parent_widget):
        """
        Recursively activate all filter widgets to ensure event handling works.
        """
        import logging
        from PyQt6.QtWidgets import QWidget

        logger = logging.getLogger(__name__)

        try:
            # Activate the parent widget
            if isinstance(parent_widget, QWidget):
                parent_widget.setEnabled(True)
                parent_widget.update()

                # Process any pending events
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()

            # Recursively activate child widgets
            for child in parent_widget.findChildren(QWidget):
                if hasattr(child, "clicked"):  # It's likely a button
                    child.setEnabled(True)
                    child.update()
                    child.repaint()

                    # Force focus capability
                    child.setFocusPolicy(child.focusPolicy())

                    logger.debug(f"Activated filter widget: {child.__class__.__name__}")

        except Exception as e:
            logger.debug(f"Error activating filter widgets: {e}")

    def _complete_initialization(self):
        """
        Complete the browse tab initialization with simple responsiveness fix.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Apply saved browse state
            self.persistence_manager.apply_saved_browse_state()

            # Simple activation to ensure filter buttons work
            self._simple_activation()

            # CRITICAL FIX: Check if browse tab is the current tab and trigger thumbnail loading
            try:
                current_tab = self.settings_manager.global_settings.get_current_tab()
                if current_tab == "browse":
                    logger.info(
                        "🎯 Browse tab is current tab during initialization - triggering thumbnail loading"
                    )
                    # Delay thumbnail loading to ensure UI is ready
                    QTimer.singleShot(200, self._ensure_all_visible_thumbnails_loaded)
            except Exception as e:
                logger.debug(f"Error checking current tab during initialization: {e}")

            logger.info("✅ Browse tab initialization completed")

        except Exception as e:
            logger.warning(f"Error completing initialization: {e}")
            # Fallback: just apply saved state without activation
            try:
                self.persistence_manager.apply_saved_browse_state()
            except:
                pass

    def _simple_activation(self):
        """
        Simple, safe activation to ensure filter buttons work.
        """
        try:
            # Just ensure the browse tab is enabled and updated
            self.setEnabled(True)
            self.update()

            # Process events to ensure everything is ready
            from PyQt6.QtWidgets import QApplication

            QApplication.processEvents()

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error in simple activation: {e}")

    def showEvent(self, event):
        """
        Handle the show event with thumbnail initialization and responsiveness fix.
        """
        super().showEvent(event)

        try:
            # Simple activation when tab becomes visible
            self._simple_activation()

            # Fix thumbnail initialization race condition
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(100, self._ensure_all_visible_thumbnails_loaded)

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error in browse tab showEvent: {e}")

    def _ensure_all_visible_thumbnails_loaded(self):
        """
        Ensure all visible thumbnails are properly loaded to fix initialization race condition.
        """
        try:
            scroll_widget = self.sequence_picker.scroll_widget

            # Get all currently visible thumbnail boxes
            visible_thumbnails = []
            for word, thumbnail_box in scroll_widget.thumbnail_boxes.items():
                if self._is_thumbnail_visible(thumbnail_box):
                    visible_thumbnails.append(thumbnail_box)

            # Trigger async loading for visible thumbnails
            for thumbnail_box in visible_thumbnails:
                # Trigger async thumbnail update (no cache)
                self.ui_updater.thumbnail_updater.update_thumbnail_image_async(
                    thumbnail_box
                )

            import logging

            logger = logging.getLogger(__name__)
            logger.debug(
                f"Triggered loading for {len(visible_thumbnails)} visible thumbnails"
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error ensuring visible thumbnails loaded: {e}")

    def _is_thumbnail_visible(self, thumbnail_box) -> bool:
        """
        Check if a thumbnail box is currently visible in the viewport.
        """
        try:
            scroll_widget = self.sequence_picker.scroll_widget
            scroll_area = scroll_widget.scroll_area

            # Get the thumbnail's position relative to the scroll area
            thumbnail_global_pos = thumbnail_box.mapToGlobal(
                thumbnail_box.rect().topLeft()
            )
            scroll_area_global_pos = scroll_area.mapToGlobal(
                scroll_area.rect().topLeft()
            )

            # Calculate relative position
            relative_pos = thumbnail_global_pos - scroll_area_global_pos

            # Check if thumbnail is within visible area
            visible_rect = scroll_area.viewport().rect()
            thumbnail_rect = thumbnail_box.rect()
            thumbnail_rect.moveTopLeft(relative_pos)

            return visible_rect.intersects(thumbnail_rect)

        except Exception:
            # If we can't determine visibility, assume it's visible
            return True

    def force_reload_all_thumbnails(self):
        """Force reload all visible thumbnails - simplified without cache."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info("🔄 Force reloading all visible thumbnails...")

            scroll_widget = self.sequence_picker.scroll_widget
            reloaded_count = 0

            for word, thumbnail_box in scroll_widget.thumbnail_boxes.items():
                if self._is_thumbnail_visible(thumbnail_box):
                    # Force thumbnail reload (no cache)
                    thumbnail_box.image_label.update_thumbnail_async(
                        thumbnail_box.state.current_index
                    )
                    reloaded_count += 1

            logger.info(f"✅ Force reloaded {reloaded_count} visible thumbnails")

        except Exception as e:
            logger.error(f"❌ Force reload error: {e}")

    def enable_lazy_loading(self) -> bool:
        """
        Enable lazy loading for the browse tab.

        Returns:
            True if lazy loading was enabled successfully
        """
        try:
            if not self._lazy_loader:
                self._initialize_lazy_loading()

            if self._lazy_loader:
                self.sequence_picker.scroll_widget.enable_lazy_loading(
                    self._lazy_loader
                )
                self._lazy_loading_enabled = True

                logger = logging.getLogger(__name__)
                logger.info("✅ Lazy loading enabled for browse tab")
                return True

            return False

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to enable lazy loading: {e}")
            return False

    def disable_lazy_loading(self) -> None:
        """Disable lazy loading for the browse tab."""
        try:
            if self._lazy_loader:
                self.sequence_picker.scroll_widget.disable_lazy_loading()
                self._lazy_loading_enabled = False

                logger = logging.getLogger(__name__)
                logger.info("✅ Lazy loading disabled for browse tab")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to disable lazy loading: {e}")

    def get_lazy_loading_stats(self) -> dict:
        """Get comprehensive lazy loading statistics."""
        try:
            if not self._lazy_loader:
                return {"lazy_loading_enabled": False, "error": "No lazy loader"}

            return {
                "lazy_loading_enabled": self._lazy_loading_enabled,
                "browse_tab_stats": self._lazy_loader.get_stats(),
                "scroll_widget_stats": self.sequence_picker.scroll_widget.get_lazy_loading_stats(),
            }

        except Exception as e:
            return {"lazy_loading_enabled": False, "error": str(e)}

    @property
    def is_lazy_loading_enabled(self) -> bool:
        """Check if lazy loading is currently enabled."""
        return self._lazy_loading_enabled
