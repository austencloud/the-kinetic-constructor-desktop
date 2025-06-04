"""
Demonstration UI for browse tab v2 foundation architecture.

This provides a minimal but functional UI that showcases the Phase 1
foundation architecture working with real data and reactive state management.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QProgressBar,
    QGroupBox,
    QScrollArea,
    QFrame,
    QSplitter,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPalette

from ..viewmodels.browse_tab_viewmodel import BrowseTabViewModel
from ..core.interfaces import BrowseTabConfig, FilterType, LoadingState
from ..core.state import BrowseState

logger = logging.getLogger(__name__)


class DemoBrowseTabView(QWidget):
    """
    Demonstration UI for browse tab v2 foundation architecture.

    This minimal UI showcases:
    - Reactive state management
    - Async data loading
    - Filter and search operations
    - Performance monitoring
    - Service coordination
    """

    def __init__(self, viewmodel: BrowseTabViewModel, config: BrowseTabConfig):
        super().__init__()

        self.viewmodel = viewmodel
        self.config = config

        # Subscribe to state changes
        self.viewmodel.state_changed.connect(self._on_state_changed)
        self.viewmodel.loading_started.connect(self._on_loading_started)
        self.viewmodel.loading_finished.connect(self._on_loading_finished)
        self.viewmodel.error_occurred.connect(self._on_error_occurred)

        # UI components
        self.status_label = None
        self.sequence_count_label = None
        self.search_input = None
        self.filter_combo = None
        self.state_display = None
        self.performance_display = None
        self.sequence_list = None
        self.progress_bar = None

        self._setup_ui()
        self._setup_styling()

        # Auto-refresh timer for performance stats
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_performance_stats)
        self.refresh_timer.start(2000)  # Update every 2 seconds

        logger.info("DemoBrowseTabView initialized")

    def _setup_ui(self):
        """Setup the demonstration UI layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title and status
        title_layout = QHBoxLayout()

        title_label = QLabel("Browse Tab v2 - Foundation Architecture Demo")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)

        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)

        layout.addLayout(title_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Controls and State
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Data and Performance
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

        # Control buttons
        button_layout = QHBoxLayout()

        load_btn = QPushButton("Load Sequences")
        load_btn.clicked.connect(self._load_sequences)

        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_filters)

        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self._refresh_performance_stats)

        button_layout.addWidget(load_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Search and Filter Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        controls_layout.addLayout(search_layout)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            [
                "None",
                "Difficulty: 1",
                "Difficulty: 2",
                "Difficulty: 3",
                "Difficulty: 4",
                "Difficulty: 5",
                "Favorites Only",
                "Length: < 8",
                "Length: >= 8",
            ]
        )
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        controls_layout.addLayout(filter_layout)

        layout.addWidget(controls_group)

        # State Display
        state_group = QGroupBox("Reactive State")
        state_layout = QVBoxLayout(state_group)

        self.state_display = QTextEdit()
        self.state_display.setMaximumHeight(200)
        self.state_display.setFont(QFont("Consolas", 9))
        state_layout.addWidget(self.state_display)

        layout.addWidget(state_group)

        # Sequence Count
        count_group = QGroupBox("Data Summary")
        count_layout = QVBoxLayout(count_group)

        self.sequence_count_label = QLabel("Sequences: 0 total, 0 filtered")
        count_layout.addWidget(self.sequence_count_label)

        layout.addWidget(count_group)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right data panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Tab widget for different views
        tab_widget = QTabWidget()

        # Sequences tab
        sequences_tab = QWidget()
        sequences_layout = QVBoxLayout(sequences_tab)

        self.sequence_list = QTextEdit()
        self.sequence_list.setFont(QFont("Consolas", 9))
        sequences_layout.addWidget(self.sequence_list)

        tab_widget.addTab(sequences_tab, "Sequences")

        # Performance tab
        performance_tab = QWidget()
        performance_layout = QVBoxLayout(performance_tab)

        self.performance_display = QTextEdit()
        self.performance_display.setFont(QFont("Consolas", 9))
        performance_layout.addWidget(self.performance_display)

        tab_widget.addTab(performance_tab, "Performance")

        layout.addWidget(tab_widget)
        return panel

    def _setup_styling(self):
        """Apply modern styling to the demo UI."""
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLineEdit, QComboBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: white;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background: #4CAF50;
                color: white;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background: #45a049;
            }
            
            QPushButton:pressed {
                background: #3d8b40;
            }
            
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: #f9f9f9;
            }
            
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background: #4CAF50;
                border-radius: 3px;
            }
        """
        )

    @pyqtSlot(object)
    def _on_state_changed(self, state: BrowseState):
        """Handle state changes from the ViewModel."""
        try:
            # Update status
            if state.loading_state == LoadingState.LOADING:
                self.status_label.setText("Loading...")
                self.status_label.setStyleSheet("color: #ff9800; font-style: italic;")
            elif state.loading_state == LoadingState.ERROR:
                self.status_label.setText("Error")
                self.status_label.setStyleSheet("color: #f44336; font-style: italic;")
            else:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet("color: #4CAF50; font-style: italic;")

            # Update sequence counts
            total_count = len(state.sequences)
            filtered_count = len(state.filtered_sequences)
            self.sequence_count_label.setText(
                f"Sequences: {total_count} total, {filtered_count} filtered"
            )

            # Update state display
            state_info = {
                "loading_state": state.loading_state.value,
                "total_sequences": total_count,
                "filtered_sequences": filtered_count,
                "active_filters": len(state.active_filters),
                "search_query": (
                    state.search_criteria.query if state.search_criteria else ""
                ),
                "selected_sequence": state.selected_sequence_id,
                "grid_columns": state.grid_columns,
                "cache_hit_rate": f"{state.cache_hit_rate:.1f}%",
                "last_load_time": f"{state.last_load_time:.3f}s",
                "state_version": state.version,
            }

            state_text = "Current State:\n" + "\n".join(
                f"  {key}: {value}" for key, value in state_info.items()
            )
            self.state_display.setText(state_text)

            # Update sequence list (show first 20 filtered sequences)
            if state.filtered_sequences:
                sequence_text = "Filtered Sequences:\n\n"
                for i, seq in enumerate(state.filtered_sequences[:20]):
                    sequence_text += f"{i+1:2d}. {seq.name} (Diff: {seq.difficulty}, Len: {seq.length})\n"

                if len(state.filtered_sequences) > 20:
                    sequence_text += (
                        f"\n... and {len(state.filtered_sequences) - 20} more"
                    )

                self.sequence_list.setText(sequence_text)
            else:
                self.sequence_list.setText("No sequences to display")

        except Exception as e:
            logger.error(f"Error updating UI from state: {e}")

    @pyqtSlot(str)
    def _on_loading_started(self, operation: str):
        """Handle loading started."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        logger.info(f"Loading started: {operation}")

    @pyqtSlot(str, bool)
    def _on_loading_finished(self, operation: str, success: bool):
        """Handle loading finished."""
        self.progress_bar.setVisible(False)
        if success:
            logger.info(f"Loading completed: {operation}")
        else:
            logger.error(f"Loading failed: {operation}")

    @pyqtSlot(str, str)
    def _on_error_occurred(self, operation: str, error: str):
        """Handle errors."""
        self.status_label.setText(f"Error: {operation}")
        self.status_label.setStyleSheet("color: #f44336; font-style: italic;")
        logger.error(f"Error in {operation}: {error}")

    def _on_search_changed(self, text: str):
        """Handle search input changes."""
        if text.strip():
            self.viewmodel.search_sequences(text)
        else:
            # Clear search
            self.viewmodel.search_sequences("")

    def _on_filter_changed(self, filter_text: str):
        """Handle filter selection changes."""
        # For now, defer async operations to avoid event loop issues
        logger.info(f"Filter changed to: {filter_text} - deferred to Phase 2")

    async def _apply_filter(self, filter_text: str):
        """Apply the selected filter."""
        try:
            if filter_text == "None":
                await self.viewmodel.clear_all_filters()
            elif filter_text.startswith("Difficulty:"):
                difficulty = int(filter_text.split(":")[1].strip())
                from ..core.interfaces import FilterCriteria

                criteria = FilterCriteria(
                    filter_type=FilterType.DIFFICULTY,
                    value=difficulty,
                    operator="equals",
                )
                await self.viewmodel.apply_filter(criteria)
            elif filter_text == "Favorites Only":
                from ..core.interfaces import FilterCriteria

                criteria = FilterCriteria(
                    filter_type=FilterType.FAVORITES, value=True, operator="equals"
                )
                await self.viewmodel.apply_filter(criteria)
            elif filter_text.startswith("Length:"):
                if "< 8" in filter_text:
                    from ..core.interfaces import FilterCriteria

                    criteria = FilterCriteria(
                        filter_type=FilterType.LENGTH, value=8, operator="less_than"
                    )
                    await self.viewmodel.apply_filter(criteria)
                elif ">= 8" in filter_text:
                    from ..core.interfaces import FilterCriteria

                    criteria = FilterCriteria(
                        filter_type=FilterType.LENGTH, value=8, operator="greater_than"
                    )
                    await self.viewmodel.apply_filter(criteria)
        except Exception as e:
            logger.error(f"Error applying filter: {e}")

    def _load_sequences(self):
        """Load sequences asynchronously."""
        # For now, defer async operations to avoid event loop issues
        logger.info("Load sequences called - deferred to Phase 2")

    def _clear_filters(self):
        """Clear all filters."""
        # For now, defer async operations to avoid event loop issues
        logger.info("Clear filters called - deferred to Phase 2")
        self.search_input.clear()
        self.filter_combo.setCurrentIndex(0)

    def _refresh_performance_stats(self):
        """Refresh performance statistics display."""
        # For now, skip async operations to avoid event loop issues
        self._update_performance_display_sync()

    def _update_performance_display_sync(self):
        """Update the performance display synchronously."""
        try:
            # For now, show basic static information
            performance_text = "Performance Statistics (Phase 1 Foundation):\n\n"

            # Current state info
            state = self.viewmodel.state_manager.get_current_state()
            if state:
                performance_text += "Current State:\n"
                performance_text += f"  Total Sequences: {len(state.sequences)}\n"
                performance_text += (
                    f"  Filtered Sequences: {len(state.filtered_sequences)}\n"
                )
                performance_text += f"  Active Filters: {len(state.active_filters)}\n"
                performance_text += f"  Loading State: {state.loading_state.value}\n"
                performance_text += f"  Cache Hit Rate: {state.cache_hit_rate:.1f}%\n"
                performance_text += f"  State Version: {state.version}\n\n"

            # Architecture info
            performance_text += "Architecture Features:\n"
            performance_text += "  ✓ Reactive State Management\n"
            performance_text += "  ✓ MVVM Pattern\n"
            performance_text += "  ✓ Service Layer Architecture\n"
            performance_text += "  ✓ Dependency Injection\n"
            performance_text += "  ✓ Multi-layer Caching\n"
            performance_text += "  ✓ Performance Monitoring\n\n"

            performance_text += "Note: Full async performance stats will be\n"
            performance_text += (
                "available in Phase 2 with proper event loop integration."
            )

            self.performance_display.setText(performance_text)

        except Exception as e:
            logger.error(f"Error updating performance display: {e}")
            self.performance_display.setText(f"Error updating stats: {e}")

    async def _update_performance_display(self):
        """Update the performance display."""
        try:
            stats = await self.viewmodel.get_performance_stats()

            performance_text = "Performance Statistics:\n\n"

            # Current state stats
            if "current_state" in stats:
                current = stats["current_state"]
                performance_text += "Current State:\n"
                performance_text += (
                    f"  Total Sequences: {current.get('total_sequences', 0)}\n"
                )
                performance_text += (
                    f"  Filtered Sequences: {current.get('filtered_sequences', 0)}\n"
                )
                performance_text += (
                    f"  Active Filters: {current.get('active_filters', 0)}\n"
                )
                performance_text += (
                    f"  Loading State: {current.get('loading_state', 'unknown')}\n"
                )
                performance_text += (
                    f"  Cache Hit Rate: {current.get('cache_hit_rate', 0):.1f}%\n\n"
                )

            # Service stats
            for service_name, service_stats in stats.items():
                if service_name != "current_state" and isinstance(service_stats, dict):
                    performance_text += f"{service_name.replace('_', ' ').title()}:\n"
                    for key, value in service_stats.items():
                        if isinstance(value, float):
                            performance_text += f"  {key}: {value:.3f}\n"
                        else:
                            performance_text += f"  {key}: {value}\n"
                    performance_text += "\n"

            self.performance_display.setText(performance_text)

        except Exception as e:
            logger.error(f"Error updating performance display: {e}")

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.refresh_timer.stop()
            logger.info("DemoBrowseTabView cleanup completed")
        except Exception as e:
            logger.error(f"DemoBrowseTabView cleanup failed: {e}")
