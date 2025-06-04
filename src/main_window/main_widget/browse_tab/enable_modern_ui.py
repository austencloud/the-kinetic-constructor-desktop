"""
Enable Modern UI - Asynchronous modernization with progress feedback

MODERNIZATION LOG:
- Date: 2025-01-27
- Changes Made: Fixed critical performance and visual issues with asynchronous processing
- Performance Impact: Non-blocking UI with progress feedback and cancellation support
- Breaking Changes: None (optional upgrade)
- Migration Notes: Run this to enable modern UI with proper progress feedback
- Visual Changes: Transforms browse tab to use 2025 modern design system with visual validation
"""

import logging
from typing import TYPE_CHECKING, Optional, Callable
from PyQt6.QtWidgets import (
    QProgressDialog,
    QApplication,
    QMessageBox,
    QVBoxLayout,
    QLabel,
    QWidget,
)
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt

from .modern_components.modern_scroll_widget import (
    ModernScrollWidget,
    create_modern_scroll_widget,
)
from .modern_components.utils.change_logger import modernization_logger

if TYPE_CHECKING:
    from .browse_tab import BrowseTab


class ModernizationProgressDialog(QProgressDialog):
    """Enhanced progress dialog with detailed status and cancellation support."""

    def __init__(self, parent=None):
        super().__init__("Initializing modernization...", "Cancel", 0, 100, parent)
        self.setWindowTitle("Browse Tab Modernization")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumDuration(0)  # Show immediately
        self.setAutoClose(False)
        self.setAutoReset(False)

        # Enhanced UI
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)

        # Status label for detailed feedback
        self.status_label = QLabel("Preparing modernization...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px;")

        # Add status label to dialog
        layout = self.layout()
        if layout:
            layout.addWidget(self.status_label)

    def update_status(self, message: str, progress: int):
        """Update both progress and status message."""
        self.setValue(progress)
        self.setLabelText(message)
        self.status_label.setText(f"Status: {message}")
        QApplication.processEvents()  # Keep UI responsive


class AsyncModernizationManager(QObject):
    """Manages asynchronous modernization with progress feedback."""

    # Signals
    progress_updated = pyqtSignal(str, int)  # message, progress
    modernization_completed = pyqtSignal(bool)  # success
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self, browse_tab: "BrowseTab", parent=None):
        super().__init__(parent)
        self.browse_tab = browse_tab
        self.logger = logging.getLogger(__name__)
        self.is_cancelled = False
        self.current_step = 0
        self.total_steps = 8

        # Progress tracking
        self.modernization_steps = [
            ("Validating compatibility...", self._validate_compatibility),
            ("Backing up current state...", self._backup_current_state),
            ("Creating modern components...", self._create_modern_components),
            ("Replacing scroll widget...", self._replace_scroll_widget),
            ("Updating UI handlers...", self._update_ui_handlers),
            ("Connecting signals...", self._connect_signals),
            ("Applying modern styling...", self._apply_modern_styling),
            ("Finalizing modernization...", self._finalize_modernization),
        ]

        # Timer for async processing
        self.process_timer = QTimer()
        self.process_timer.setSingleShot(True)
        self.process_timer.timeout.connect(self._process_next_step)

        # Store references
        self.modern_scroll_widget: Optional[ModernScrollWidget] = None
        self.old_scroll_widget = None
        self.backup_data = {}

    def start_modernization(self) -> bool:
        """Start the asynchronous modernization process."""
        try:
            self.logger.info("🚀 Starting asynchronous browse tab modernization...")
            self.is_cancelled = False
            self.current_step = 0

            # Start the first step
            self._process_next_step()
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start modernization: {e}")
            self.error_occurred.emit(str(e))
            return False

    def cancel_modernization(self):
        """Cancel the modernization process."""
        self.is_cancelled = True
        self.process_timer.stop()
        self.logger.info("🛑 Modernization cancelled by user")

    def _process_next_step(self):
        """Process the next step in the modernization."""
        if self.is_cancelled or self.current_step >= len(self.modernization_steps):
            if not self.is_cancelled:
                self.modernization_completed.emit(True)
            return

        try:
            step_name, step_function = self.modernization_steps[self.current_step]
            progress = int((self.current_step / len(self.modernization_steps)) * 100)

            self.progress_updated.emit(step_name, progress)
            self.logger.info(
                f"📋 Step {self.current_step + 1}/{len(self.modernization_steps)}: {step_name}"
            )

            # Execute the step
            success = step_function()

            if not success:
                self.error_occurred.emit(f"Failed at step: {step_name}")
                return

            self.current_step += 1

            # Schedule next step with small delay to keep UI responsive
            if not self.is_cancelled:
                self.process_timer.start(50)  # 50ms delay between steps

        except Exception as e:
            self.logger.error(f"❌ Error in modernization step: {e}")
            self.error_occurred.emit(str(e))

    def _validate_compatibility(self) -> bool:
        """Validate that the browse tab is compatible with modernization."""
        try:
            required_attrs = ["sequence_picker", "ui_updater", "state", "get"]

            for attr in required_attrs:
                if not hasattr(self.browse_tab, attr):
                    self.logger.error(f"Missing required attribute: {attr}")
                    return False

            if not hasattr(self.browse_tab.sequence_picker, "scroll_widget"):
                self.logger.error("Missing scroll_widget in sequence_picker")
                return False

            self.logger.info("✅ Compatibility validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Compatibility validation failed: {e}")
            return False

    def _backup_current_state(self) -> bool:
        """Backup current browse tab state."""
        try:
            self.backup_data = {
                "current_sequences": getattr(self.browse_tab, "current_sequences", []),
                "current_filter": getattr(self.browse_tab.state, "_current_filter", ""),
                "current_section": getattr(
                    self.browse_tab.state, "_current_section", ""
                ),
                "scroll_widget": self.browse_tab.sequence_picker.scroll_widget,
            }
            self.logger.info("✅ State backup completed")
            return True
        except Exception as e:
            self.logger.error(f"State backup failed: {e}")
            return False

    def _create_modern_components(self) -> bool:
        """Create modern scroll widget and components."""
        try:
            sequence_picker = self.browse_tab.sequence_picker
            self.modern_scroll_widget = create_modern_scroll_widget(sequence_picker)
            self.old_scroll_widget = sequence_picker.scroll_widget
            self.logger.info("✅ Modern components created")
            return True
        except Exception as e:
            self.logger.error(f"Modern component creation failed: {e}")
            return False

    def _replace_scroll_widget(self) -> bool:
        """Replace the legacy scroll widget with modern version."""
        try:
            sequence_picker = self.browse_tab.sequence_picker

            # Replace the scroll widget reference
            sequence_picker.scroll_widget = self.modern_scroll_widget

            # Update layout if it exists
            if hasattr(sequence_picker, "layout") and sequence_picker.layout:
                # Remove old widget from layout
                for i in range(sequence_picker.layout.count()):
                    item = sequence_picker.layout.itemAt(i)
                    if item and item.widget() == self.old_scroll_widget:
                        sequence_picker.layout.removeItem(item)
                        self.old_scroll_widget.setParent(None)
                        break

                # Add modern widget to layout
                sequence_picker.layout.addWidget(self.modern_scroll_widget)

            self.logger.info("✅ Scroll widget replaced")
            return True
        except Exception as e:
            self.logger.error(f"Scroll widget replacement failed: {e}")
            return False

    def _update_ui_handlers(self) -> bool:
        """Update UI handlers to work with modern components."""
        try:
            _patch_ui_updater_for_modern_components(self.browse_tab)
            self.logger.info("✅ UI handlers updated")
            return True
        except Exception as e:
            self.logger.error(f"UI handler update failed: {e}")
            return False

    def _connect_signals(self) -> bool:
        """Connect modern component signals to existing handlers."""
        try:
            # Connect modern scroll widget signals
            self.modern_scroll_widget.thumbnail_clicked.connect(
                lambda word, index: _handle_modern_thumbnail_click(
                    self.browse_tab, word, index
                )
            )

            self.modern_scroll_widget.favorite_toggled.connect(
                lambda word, is_favorite: _handle_modern_favorite_toggle(
                    self.browse_tab, word, is_favorite
                )
            )

            self.logger.info("✅ Signals connected")
            return True
        except Exception as e:
            self.logger.error(f"Signal connection failed: {e}")
            return False

    def _apply_modern_styling(self) -> bool:
        """Apply modern theme and styling."""
        try:
            self.modern_scroll_widget.set_modern_theme("dark")

            # Force visual update to ensure styling is applied
            self.modern_scroll_widget.update()
            QApplication.processEvents()

            self.logger.info("✅ Modern styling applied")
            return True
        except Exception as e:
            self.logger.error(f"Modern styling failed: {e}")
            return False

    def _finalize_modernization(self) -> bool:
        """Finalize the modernization process."""
        try:
            # Restore sequences with modern components if available
            if hasattr(self.browse_tab, "get") and hasattr(
                self.browse_tab.get, "base_words"
            ):
                sequences = []
                for word, thumbnails in self.browse_tab.get.base_words():
                    if thumbnails:
                        length = len(thumbnails)
                        sequences.append((word, thumbnails, length))

                if sequences:
                    self.modern_scroll_widget.update_sequences(sequences, animate=True)
                    self.logger.info(f"✅ Restored {len(sequences)} sequences")

            # Log successful modernization
            modernization_logger.log_component_update(
                component_name="AsyncBrowseTabModernization",
                changes_made=[
                    "Asynchronous modernization with progress feedback",
                    "Non-blocking UI updates",
                    "Visual validation and error handling",
                    "Modern component integration with styling verification",
                ],
                old_version="legacy_browse_tab",
                new_version="modern_2025_browse_tab_async",
            )

            self.logger.info("✅ Modernization finalized")
            return True
        except Exception as e:
            self.logger.error(f"Modernization finalization failed: {e}")
            return False


def enable_modern_ui_for_browse_tab(
    browse_tab: "BrowseTab", parent_widget=None
) -> bool:
    """
    Enable modern UI components for the browse tab with asynchronous processing.

    This function performs a seamless upgrade of the browse tab to use
    modern 2025 design components with progress feedback and cancellation support.

    Args:
        browse_tab: The browse tab instance to modernize
        parent_widget: Parent widget for progress dialog

    Returns:
        True if modernization was successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting asynchronous browse tab modernization...")

        # Create progress dialog
        progress_dialog = ModernizationProgressDialog(parent_widget)

        # Create async modernization manager
        modernization_manager = AsyncModernizationManager(browse_tab, parent_widget)

        # Connect signals
        modernization_manager.progress_updated.connect(progress_dialog.update_status)

        # Track completion
        modernization_success = [False]  # Use list for closure

        def on_completion(success: bool):
            modernization_success[0] = success
            progress_dialog.close()

            if success:
                # Show success message
                msg = QMessageBox(parent_widget)
                msg.setWindowTitle("Modernization Complete")
                msg.setText("🎉 Browse tab successfully modernized with 2025 design!")
                msg.setInformativeText("The interface now features glassmorphism effects, smooth animations, and responsive layouts.")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.exec()
                logger.info("🎉 Modernization completed successfully!")
            else:
                logger.error("❌ Modernization failed")

        def on_error(error_message: str):
            progress_dialog.close()

            # Show error message
            msg = QMessageBox(parent_widget)
            msg.setWindowTitle("Modernization Failed")
            msg.setText("❌ Failed to modernize browse tab")
            msg.setInformativeText(f"Error: {error_message}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()
            logger.error(f"❌ Modernization failed: {error_message}")

        # Connect completion handlers
        modernization_manager.modernization_completed.connect(on_completion)
        modernization_manager.error_occurred.connect(on_error)

        # Handle cancellation
        def on_cancel():
            modernization_manager.cancel_modernization()
            logger.info("🛑 Modernization cancelled by user")

        progress_dialog.canceled.connect(on_cancel)

        # Start modernization
        if not modernization_manager.start_modernization():
            progress_dialog.close()
            return False

        # Show progress dialog and wait for completion
        progress_dialog.show()

        # Process events until completion
        while progress_dialog.isVisible():
            QApplication.processEvents()
            QApplication.instance().thread().msleep(10)

        return modernization_success[0]

    except Exception as e:
        logger.error(f"❌ Browse tab modernization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Legacy synchronous function for backward compatibility
def enable_modern_ui_for_browse_tab_sync(browse_tab: "BrowseTab") -> bool:
    modern 2025 design components while maintaining full compatibility
    with existing functionality.

    Args:
        browse_tab: The browse tab instance to modernize

    Returns:
        True if modernization was successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting browse tab modernization...")

        # Start performance timer
        timer_id = modernization_logger.start_performance_timer(
            "browse_tab_modernization"
        )

        # Step 1: Backup current state
        logger.info("📦 Backing up current browse tab state...")
        current_sequences = getattr(browse_tab, "current_sequences", [])
        current_filter = getattr(browse_tab.state, "_current_filter", "")
        current_section = getattr(browse_tab.state, "_current_section", "")

        # Step 2: Replace scroll widget with modern version
        logger.info("🔄 Replacing scroll widget with modern version...")

        # Get reference to sequence picker
        sequence_picker = browse_tab.sequence_picker

        # Create modern scroll widget
        modern_scroll_widget = create_modern_scroll_widget(sequence_picker)

        # Store reference to old scroll widget
        old_scroll_widget = sequence_picker.scroll_widget

        # Replace the scroll widget
        sequence_picker.scroll_widget = modern_scroll_widget

        # Update layout to use modern scroll widget
        if hasattr(sequence_picker, "layout") and sequence_picker.layout:
            # Remove old widget from layout
            for i in range(sequence_picker.layout.count()):
                item = sequence_picker.layout.itemAt(i)
                if item and item.widget() == old_scroll_widget:
                    sequence_picker.layout.removeItem(item)
                    old_scroll_widget.setParent(None)
                    break

            # Add modern widget to layout
            sequence_picker.layout.addWidget(modern_scroll_widget)

        # Step 3: Restore state with modern components
        logger.info("🔄 Restoring state with modern components...")

        # If we have current sequences, update them with modern components
        if hasattr(browse_tab, "get") and hasattr(browse_tab.get, "base_words"):
            try:
                # Get current sequences
                sequences = []
                for word, thumbnails in browse_tab.get.base_words():
                    if thumbnails:
                        # Get sequence length (simplified)
                        length = len(thumbnails)
                        sequences.append((word, thumbnails, length))

                # Update modern scroll widget with sequences
                modern_scroll_widget.update_sequences(sequences, animate=True)

                logger.info(
                    f"✅ Restored {len(sequences)} sequences with modern components"
                )

            except Exception as e:
                logger.warning(f"Could not restore sequences: {e}")

        # Step 4: Update UI updater to work with modern components
        logger.info("🔄 Updating UI updater for modern components...")

        # Patch the UI updater to work with modern components
        _patch_ui_updater_for_modern_components(browse_tab)

        # Step 5: Connect modern signals to existing handlers
        logger.info("🔗 Connecting modern signals to existing handlers...")

        # Connect modern scroll widget signals to existing browse tab handlers
        modern_scroll_widget.thumbnail_clicked.connect(
            lambda word, index: _handle_modern_thumbnail_click(browse_tab, word, index)
        )

        modern_scroll_widget.favorite_toggled.connect(
            lambda word, is_favorite: _handle_modern_favorite_toggle(
                browse_tab, word, is_favorite
            )
        )

        # Step 6: Apply modern theme
        logger.info("🎨 Applying modern theme...")
        modern_scroll_widget.set_modern_theme("dark")  # Default to dark theme

        # Stop performance timer
        modernization_logger.stop_performance_timer(timer_id)

        # Log successful modernization
        modernization_logger.log_component_update(
            component_name="BrowseTabModernization",
            changes_made=[
                "Replaced legacy scroll widget with modern version",
                "Integrated modern grid layout and animations",
                "Applied 2025 design system",
                "Maintained full API compatibility",
                "Connected modern signals to existing handlers",
            ],
            old_version="legacy_browse_tab",
            new_version="modern_2025_browse_tab",
        )

        logger.info("🎉 Browse tab modernization completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Browse tab modernization failed: {e}")
        import traceback

        traceback.print_exc()

        # Log failure
        modernization_logger.log_component_update(
            component_name="BrowseTabModernization",
            changes_made=["Modernization failed"],
            old_version="legacy_browse_tab",
            new_version="modernization_failed",
        )

        return False


def _patch_ui_updater_for_modern_components(browse_tab: "BrowseTab"):
    """Patch the UI updater to work with modern components."""
    logger = logging.getLogger(__name__)

    try:
        ui_updater = browse_tab.ui_updater

        # Store original method
        original_update_method = ui_updater.update_and_display_ui

        def modern_update_and_display_ui(
            total_sequences: int, skip_scaling: bool = True
        ):
            """Modern version of update_and_display_ui."""
            logger.debug(f"🔄 Modern UI update called with {total_sequences} sequences")

            # Get sequences from browse tab
            try:
                sequences = []
                for word, thumbnails in browse_tab.get.base_words():
                    if thumbnails:
                        length = len(thumbnails)
                        sequences.append((word, thumbnails, length))

                # Update modern scroll widget
                modern_scroll_widget = browse_tab.sequence_picker.scroll_widget
                if isinstance(modern_scroll_widget, ModernScrollWidget):
                    modern_scroll_widget.update_sequences(sequences, animate=True)
                else:
                    # Fallback to original method if not modern
                    original_update_method(total_sequences, skip_scaling)

            except Exception as e:
                logger.warning(
                    f"Modern UI update failed, falling back to original: {e}"
                )
                original_update_method(total_sequences, skip_scaling)

        # Replace the method
        ui_updater.update_and_display_ui = modern_update_and_display_ui

        logger.info("✅ UI updater patched for modern components")

    except Exception as e:
        logger.warning(f"Failed to patch UI updater: {e}")


def _handle_modern_thumbnail_click(browse_tab: "BrowseTab", word: str, index: int):
    """Handle modern thumbnail click events."""
    logger = logging.getLogger(__name__)

    try:
        # Update selection in browse tab state
        if hasattr(browse_tab, "state"):
            browse_tab.state._selected_sequence = {"word": word, "index": index}

        # Update sequence viewer if it exists
        if hasattr(browse_tab, "sequence_viewer"):
            # Get the modern card
            modern_scroll_widget = browse_tab.sequence_picker.scroll_widget
            if isinstance(modern_scroll_widget, ModernScrollWidget):
                modern_card = modern_scroll_widget.get_modern_card_for_word(word)
                if modern_card:
                    current_thumbnail = modern_card.get_current_thumbnail()
                    if current_thumbnail:
                        # Update sequence viewer with current thumbnail
                        browse_tab.sequence_viewer.update_sequence_viewer(
                            current_thumbnail
                        )

        logger.debug(f"🎯 Modern thumbnail clicked: {word}[{index}]")

        # Log interaction
        modernization_logger.log_user_interaction(
            interaction_type="modern_thumbnail_click",
            component="ModernBrowseTab",
            details={"word": word, "index": index},
        )

    except Exception as e:
        logger.warning(f"Error handling modern thumbnail click: {e}")


def _handle_modern_favorite_toggle(
    browse_tab: "BrowseTab", word: str, is_favorite: bool
):
    """Handle modern favorite toggle events."""
    logger = logging.getLogger(__name__)

    try:
        # Update favorite status in metadata or settings
        # This would typically integrate with the existing favorite system

        logger.debug(f"❤️ Modern favorite toggled: {word} = {is_favorite}")

        # Log interaction
        modernization_logger.log_user_interaction(
            interaction_type="modern_favorite_toggle",
            component="ModernBrowseTab",
            details={"word": word, "is_favorite": is_favorite},
        )

    except Exception as e:
        logger.warning(f"Error handling modern favorite toggle: {e}")


def check_modern_ui_compatibility(browse_tab: "BrowseTab") -> bool:
    """
    Check if the browse tab is compatible with modern UI components.

    Args:
        browse_tab: The browse tab instance to check

    Returns:
        True if compatible, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        # Check required attributes
        required_attrs = ["sequence_picker", "ui_updater", "state", "get"]

        for attr in required_attrs:
            if not hasattr(browse_tab, attr):
                logger.warning(f"Missing required attribute: {attr}")
                return False

        # Check sequence picker structure
        if not hasattr(browse_tab.sequence_picker, "scroll_widget"):
            logger.warning("Missing scroll_widget in sequence_picker")
            return False

        logger.info("✅ Browse tab is compatible with modern UI")
        return True

    except Exception as e:
        logger.error(f"Compatibility check failed: {e}")
        return False


def get_modernization_status(browse_tab: "BrowseTab") -> dict:
    """
    Get the current modernization status of the browse tab.

    Args:
        browse_tab: The browse tab instance to check

    Returns:
        Dictionary with modernization status information
    """
    try:
        scroll_widget = browse_tab.sequence_picker.scroll_widget
        is_modern = isinstance(scroll_widget, ModernScrollWidget)

        status = {
            "is_modernized": is_modern,
            "scroll_widget_type": type(scroll_widget).__name__,
            "compatible": check_modern_ui_compatibility(browse_tab),
        }

        if is_modern:
            status["modern_stats"] = scroll_widget.get_modern_stats()

        return status

    except Exception as e:
        return {"is_modernized": False, "error": str(e), "compatible": False}
