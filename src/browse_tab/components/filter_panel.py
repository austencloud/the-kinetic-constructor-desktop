"""
Filter Panel Component - Clean Architecture Implementation.

Handles all filtering UI and logic with single responsibility principle.
Provides search functionality, filter controls, and filter state management.

Features:
- Search input with real-time filtering
- Filter criteria management (difficulty, length, author, etc.)
- Sort controls with multiple criteria
- Filter state persistence
- Performance optimized with debounced search
- Glassmorphism styling integration
- Dictionary image regeneration

Performance Targets:
- <50ms filter application
- <100ms search response
- Debounced input handling for smooth UX
"""

import logging
from typing import List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QFrame,
    QButtonGroup,
    QCheckBox,
    QMessageBox,
)
from PyQt6.QtCore import QTimer, pyqtSignal, QElapsedTimer
from PyQt6.QtGui import QFont

from ..core.interfaces import FilterCriteria, SortOrder, BrowseTabConfig

logger = logging.getLogger(__name__)


class FilterPanel(QWidget):
    """
    Filter panel component handling search and filtering functionality.

    Single Responsibility: Manage all filtering UI and state

    Features:
    - Real-time search with debouncing
    - Multiple filter criteria (difficulty, length, author, tags)
    - Sort controls (alphabetical, difficulty, date, length)
    - Filter state management and persistence
    - Performance optimized input handling
    - Dictionary image regeneration
    """

    # Signals for component communication
    search_changed = pyqtSignal(str)  # search_query
    filter_added = pyqtSignal(object)  # FilterCriteria
    filter_removed = pyqtSignal(object)  # FilterCriteria
    filters_cleared = pyqtSignal()
    sort_changed = pyqtSignal(str, object)  # sort_by, SortOrder
    regenerate_requested = pyqtSignal()  # NEW: Signal for regenerate button

    def __init__(
        self,
        config: BrowseTabConfig = None,
        filter_service=None,
        main_widget=None,
        parent: QWidget = None,
    ):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()
        self.filter_service = filter_service
        self.main_widget = main_widget  # NEW: Store main widget reference

        # State management
        self._active_filters: List[FilterCriteria] = []
        self._current_search_query = ""
        self._current_sort_by = "alphabetical"
        self._current_sort_order = SortOrder.ASC

        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._search_debounce_timer = QTimer()
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.timeout.connect(self._process_search)
        self._pending_search_query = ""

        # UI components
        self.search_input = None
        self.sort_combo = None
        self.sort_order_button = None
        self.filter_buttons = {}
        self.active_filter_labels = []
        self.regenerate_button = None  # NEW: Regenerate button

        self._setup_ui()
        self._setup_styling()
        self._connect_signals()

        logger.debug("FilterPanel component initialized")

    def _setup_ui(self):
        """Setup the filter panel UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Search section
        self._create_search_section(layout)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        layout.addWidget(separator1)

        # Sort section
        self._create_sort_section(layout)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        layout.addWidget(separator2)

        # Filter section
        self._create_filter_section(layout)

        # Spacer
        layout.addStretch()

        # Active filters section
        self._create_active_filters_section(layout)

    def _create_search_section(self, layout):
        """Create search input section."""
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(5)

        # Search label
        search_label = QLabel("Search")
        search_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        search_layout.addWidget(search_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search sequences...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setMaximumWidth(300)
        search_layout.addWidget(self.search_input)

        layout.addWidget(search_container)

    def _create_sort_section(self, layout):
        """Create sort controls section."""
        sort_container = QWidget()
        sort_layout = QVBoxLayout(sort_container)
        sort_layout.setContentsMargins(0, 0, 0, 0)
        sort_layout.setSpacing(5)

        # Sort label
        sort_label = QLabel("Sort")
        sort_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sort_layout.addWidget(sort_label)

        # Sort controls
        sort_controls = QHBoxLayout()
        sort_controls.setSpacing(5)

        # Sort criteria combo
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            ["Alphabetical", "Difficulty", "Date Added", "Length", "Author"]
        )
        self.sort_combo.setMinimumWidth(120)
        sort_controls.addWidget(self.sort_combo)

        # Sort order button
        self.sort_order_button = QPushButton("↑")
        self.sort_order_button.setFixedSize(30, 30)
        self.sort_order_button.setToolTip("Toggle sort order")
        sort_controls.addWidget(self.sort_order_button)

        sort_layout.addLayout(sort_controls)
        layout.addWidget(sort_container)

    def _create_filter_section(self, layout):
        """Create filter buttons section."""
        filter_container = QWidget()
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(5)

        # Filter label
        filter_label = QLabel("Filters")
        filter_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        filter_layout.addWidget(filter_label)

        # Filter buttons
        filter_buttons_layout = QHBoxLayout()
        filter_buttons_layout.setSpacing(5)

        # Create filter buttons
        filter_types = ["Difficulty", "Length", "Author", "Tags", "Favorites"]
        for filter_type in filter_types:
            button = QPushButton(filter_type)
            button.setCheckable(True)
            button.setMinimumWidth(80)
            self.filter_buttons[filter_type.lower()] = button
            filter_buttons_layout.addWidget(button)

        filter_layout.addLayout(filter_buttons_layout)

        # NEW: Add regenerate button section
        regenerate_layout = QHBoxLayout()
        regenerate_layout.setSpacing(5)

        # Regenerate button
        self.regenerate_button = QPushButton("🔄 Regenerate Dictionary Images")
        self.regenerate_button.setMinimumWidth(200)
        self.regenerate_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(231, 76, 60, 0.8);
                color: white;
                border: 1px solid rgba(231, 76, 60, 0.9);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(192, 57, 43, 0.9);
                border-color: rgba(192, 57, 43, 1.0);
            }
            QPushButton:pressed {
                background: rgba(169, 50, 38, 1.0);
            }
        """
        )
        self.regenerate_button.clicked.connect(self._on_regenerate_clicked)
        regenerate_layout.addWidget(self.regenerate_button)
        regenerate_layout.addStretch()

        filter_layout.addLayout(regenerate_layout)
        layout.addWidget(filter_container)

    def _create_active_filters_section(self, layout):
        """Create active filters display section."""
        active_container = QWidget()
        active_layout = QVBoxLayout(active_container)
        active_layout.setContentsMargins(0, 0, 0, 0)
        active_layout.setSpacing(5)

        # Active filters label
        active_label = QLabel("Active Filters")
        active_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        active_layout.addWidget(active_label)

        # Clear all button
        clear_button = QPushButton("Clear All")
        clear_button.setMaximumWidth(80)
        clear_button.clicked.connect(self._clear_all_filters)
        active_layout.addWidget(clear_button)

        layout.addWidget(active_container)

    def _setup_styling(self):
        """Apply glassmorphism styling to the filter panel."""
        try:
            from styles.glassmorphism_coordinator import GlassmorphismCoordinator

            coordinator = GlassmorphismCoordinator()

            # Apply glassmorphism to main panel
            self.setStyleSheet(
                """
                FilterPanel {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QLineEdit {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 8px;
                    color: white;
                }
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 6px 12px;
                    color: white;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
                QPushButton:checked {
                    background: rgba(100, 150, 255, 0.3);
                    border-color: rgba(100, 150, 255, 0.5);
                }
                QComboBox {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 6px;
                    color: white;
                }
                QLabel {
                    color: white;
                }
            """
            )

            # CRITICAL FIX: Remove blur effect that causes crashes and content to appear fuzzy
            # coordinator.add_blur_effect(self, 5)  # DISABLED - causes segfault

            logger.debug("Filter panel styling applied")

        except Exception as e:
            logger.warning(f"Failed to apply filter panel styling: {e}")

    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Search input with debouncing
        self.search_input.textChanged.connect(self._on_search_input_changed)

        # Sort controls
        self.sort_combo.currentTextChanged.connect(self._on_sort_criteria_changed)
        self.sort_order_button.clicked.connect(self._toggle_sort_order)

        # Filter buttons
        for filter_type, button in self.filter_buttons.items():
            button.toggled.connect(
                lambda checked, ft=filter_type: self._on_filter_toggled(ft, checked)
            )

        # NEW: Regenerate button signal already connected in _create_filter_section

    def _on_search_input_changed(self, text: str):
        """Handle search input changes with debouncing."""
        self._pending_search_query = text

        # Debounce search for smooth performance
        self._search_debounce_timer.stop()
        self._search_debounce_timer.start(300)  # 300ms debounce

    def _process_search(self):
        """Process the debounced search query."""
        self._performance_timer.start()

        query = self._pending_search_query.strip()
        if query != self._current_search_query:
            self._current_search_query = query
            self.search_changed.emit(query)

            elapsed = self._performance_timer.elapsed()
            logger.debug(f"Search processed in {elapsed}ms: '{query}'")

            # Performance target: <100ms search response
            if elapsed > 100:
                logger.warning(f"Search processing exceeded 100ms target: {elapsed}ms")

    def _on_sort_criteria_changed(self, criteria: str):
        """Handle sort criteria changes."""
        self._performance_timer.start()

        # Map display names to internal values
        criteria_map = {
            "Alphabetical": "alphabetical",
            "Difficulty": "difficulty",
            "Date Added": "date_added",
            "Length": "length",
            "Author": "author",
        }

        sort_by = criteria_map.get(criteria, "alphabetical")
        if sort_by != self._current_sort_by:
            self._current_sort_by = sort_by
            self.sort_changed.emit(sort_by, self._current_sort_order)

            elapsed = self._performance_timer.elapsed()
            logger.debug(f"Sort criteria changed in {elapsed}ms: {sort_by}")

    def _toggle_sort_order(self):
        """Toggle sort order between ascending and descending."""
        self._current_sort_order = (
            SortOrder.DESC
            if self._current_sort_order == SortOrder.ASC
            else SortOrder.ASC
        )

        # Update button text
        self.sort_order_button.setText(
            "↓" if self._current_sort_order == SortOrder.DESC else "↑"
        )

        # Emit sort change
        self.sort_changed.emit(self._current_sort_by, self._current_sort_order)

        logger.debug(f"Sort order toggled to: {self._current_sort_order}")

    def _on_filter_toggled(self, filter_type: str, checked: bool):
        """Handle filter button toggles."""
        self._performance_timer.start()

        if checked:
            # Add filter
            filter_criteria = FilterCriteria(
                filter_type=filter_type,
                value="",  # Default empty value, will be populated by filter service
                operator="equals",  # Default operator
            )
            self._active_filters.append(filter_criteria)
            self.filter_added.emit(filter_criteria)

        else:
            # Remove filter
            for filter_criteria in self._active_filters[:]:
                if filter_criteria.filter_type == filter_type:
                    self._active_filters.remove(filter_criteria)
                    self.filter_removed.emit(filter_criteria)
                    break

        elapsed = self._performance_timer.elapsed()
        logger.debug(f"Filter toggle processed in {elapsed}ms: {filter_type}={checked}")

        # Performance target: <50ms filter application
        if elapsed > 50:
            logger.warning(f"Filter toggle exceeded 50ms target: {elapsed}ms")

    def _clear_all_filters(self):
        """Clear all active filters."""
        self._active_filters.clear()

        # Uncheck all filter buttons
        for button in self.filter_buttons.values():
            button.setChecked(False)

        # Clear search
        self.search_input.clear()
        self._current_search_query = ""

        self.filters_cleared.emit()
        logger.debug("All filters cleared")

    def _on_regenerate_clicked(self):
        """Handle regenerate dictionary images button click."""
        try:
            # Confirm with user
            reply = QMessageBox.question(
                self,
                "Regenerate Dictionary Images",
                "This will regenerate all dictionary images using the proper ImageCreator.\n\n"
                "This process may take several minutes and will overwrite existing images.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Emit signal for coordinator to handle
                self.regenerate_requested.emit()

                # Alternatively, handle directly if main_widget is available
                if self.main_widget:
                    self._regenerate_dictionary_images_direct()
                else:
                    logger.warning("No main_widget available for direct regeneration")

        except Exception as e:
            logger.error(f"Error in regenerate button handler: {e}")
            QMessageBox.critical(
                self, "Regeneration Error", f"An error occurred:\n\n{str(e)}"
            )

    def _regenerate_dictionary_images_direct(self):
        """Directly trigger dictionary image regeneration using the working final regenerator."""
        try:
            logger.info("🔄 Dictionary image regeneration triggered from FilterPanel")

            # Use the working final regenerator that we created
            from tools.final_dictionary_regenerator import (
                regenerate_dictionary_images_final,
            )

            # Run the regeneration in a separate thread to avoid blocking the UI
            import threading

            def run_regeneration():
                try:
                    success = regenerate_dictionary_images_final(self.main_widget)

                    # Show completion message on the main thread
                    from PyQt6.QtCore import QTimer

                    def show_result():
                        if success:
                            QMessageBox.information(
                                self,
                                "Regeneration Complete",
                                "Dictionary regeneration completed successfully!\n\n"
                                "Check the console output for detailed statistics.\n"
                                "The browse tab will automatically refresh with new images.",
                            )
                        else:
                            QMessageBox.warning(
                                self,
                                "Regeneration Issues",
                                "Dictionary regeneration completed with some issues.\n\n"
                                "Check the console output for detailed error information.",
                            )

                    # Schedule the message box to show on the main thread
                    QTimer.singleShot(0, show_result)

                except Exception as e:
                    logger.error(f"Error in regeneration thread: {e}")

                    def show_error():
                        QMessageBox.critical(
                            self,
                            "Regeneration Error",
                            f"An error occurred during dictionary regeneration:\n\n{str(e)}",
                        )

                    QTimer.singleShot(0, show_error)

            # Start regeneration in background thread
            thread = threading.Thread(target=run_regeneration, daemon=True)
            thread.start()

            # Show immediate feedback
            QMessageBox.information(
                self,
                "Regeneration Started",
                "Dictionary image regeneration has started in the background.\n\n"
                "This may take several minutes. You will be notified when complete.\n"
                "Check the console for progress updates.",
            )

        except Exception as e:
            logger.error(f"Error during dictionary regeneration: {e}")
            QMessageBox.critical(
                self,
                "Regeneration Error",
                f"An error occurred during dictionary regeneration:\n\n{str(e)}",
            )

    # Public interface methods
    def get_active_filters(self) -> List[FilterCriteria]:
        """Get currently active filters."""
        return self._active_filters.copy()

    def get_search_query(self) -> str:
        """Get current search query."""
        return self._current_search_query

    def get_sort_criteria(self) -> tuple:
        """Get current sort criteria."""
        return self._current_sort_by, self._current_sort_order

    def set_filter_enabled(self, filter_type: str, enabled: bool):
        """Enable or disable a specific filter type."""
        if filter_type in self.filter_buttons:
            self.filter_buttons[filter_type].setChecked(enabled)

    def cleanup(self):
        """Cleanup resources."""
        try:
            self._search_debounce_timer.stop()
            logger.debug("FilterPanel cleanup completed")
        except Exception as e:
            logger.error(f"FilterPanel cleanup failed: {e}")
