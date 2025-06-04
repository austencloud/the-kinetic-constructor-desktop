"""
Smart Filter Panel Component - Phase 2 Week 3 Day 20-21

Modern filter panel with search auto-complete, filter chips, and sort controls.
Implements 2025 design system with glassmorphism and smooth animations.

Features:
- Real-time search with auto-complete suggestions
- Interactive filter chips with easy removal
- Sort controls with multiple criteria
- Modern glassmorphic styling
- Smooth animations and transitions
- Accessibility support
"""

import logging
from typing import List, Dict, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QCompleter,
    QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import (
    Qt,
    QStringListModel,
    QTimer,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
)
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from ..core.interfaces import FilterCriteria, FilterType, SortOrder, SearchCriteria
from ..core.state import BrowseState
from ..debug.window_resize_tracker import (
    set_phase,
    track_component,
    log_main_window_change,
)

logger = logging.getLogger(__name__)


class FilterChip(QWidget):
    """Individual filter chip with remove functionality."""

    remove_requested = pyqtSignal(object)  # FilterCriteria

    def __init__(self, filter_criteria: FilterCriteria, parent: QWidget = None):
        super().__init__(parent)

        self.filter_criteria = filter_criteria
        self._setup_ui()
        self._setup_styling()

    def _setup_ui(self):
        """Setup chip UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(8)

        # Filter label
        label_text = self._format_filter_text()
        self.label = QLabel(label_text)
        self.label.setFont(QFont("Segoe UI", 9))

        # Remove button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.clicked.connect(
            lambda: self.remove_requested.emit(self.filter_criteria)
        )

        layout.addWidget(self.label)
        layout.addWidget(self.remove_btn)

        self.setFixedHeight(28)

    def _setup_styling(self):
        """Apply chip styling."""
        self.setStyleSheet(
            """
            FilterChip {
                background: rgba(76, 175, 80, 0.2);
                border: 1px solid rgba(76, 175, 80, 0.4);
                border-radius: 14px;
            }
            
            FilterChip:hover {
                background: rgba(76, 175, 80, 0.3);
                border: 1px solid rgba(76, 175, 80, 0.6);
            }
            
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }
            
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.8);
                font-weight: bold;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
                color: rgba(255, 255, 255, 1.0);
            }
        """
        )

    def _format_filter_text(self) -> str:
        """Format filter criteria for display."""
        filter_type = self.filter_criteria.filter_type
        value = self.filter_criteria.value
        operator = self.filter_criteria.operator

        if filter_type == FilterType.DIFFICULTY:
            return f"Difficulty {operator} {value}"
        elif filter_type == FilterType.LENGTH:
            return f"Length {operator} {value}"
        elif filter_type == FilterType.CATEGORY:
            return f"Category: {value}"
        elif filter_type == FilterType.FAVORITES:
            return "Favorites Only"
        else:
            return f"{filter_type.value}: {value}"


class SmartFilterPanel(QWidget):
    """
    Smart filter panel with search, filters, and sorting capabilities.

    Features:
    - Real-time search with auto-complete
    - Interactive filter chips
    - Sort controls with multiple criteria
    - Modern glassmorphic design
    - Smooth animations
    """

    # Signals
    search_changed = pyqtSignal(str)  # search_query
    filter_added = pyqtSignal(object)  # FilterCriteria
    filter_removed = pyqtSignal(object)  # FilterCriteria
    filters_cleared = pyqtSignal()
    sort_changed = pyqtSignal(str, object)  # sort_by, sort_order

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # State
        self._active_filters: List[FilterCriteria] = []
        self._search_suggestions: List[str] = []
        self._current_sort_by = "name"
        self._current_sort_order = SortOrder.ASC

        # UI components
        self.search_input: Optional[QLineEdit] = None
        self.search_completer: Optional[QCompleter] = None
        self.filter_chips_container: Optional[QWidget] = None
        self.filter_chips_layout: Optional[QHBoxLayout] = None
        self.sort_combo: Optional[QComboBox] = None
        self.sort_order_btn: Optional[QPushButton] = None

        # Animation system
        self._expand_animation: Optional[QPropertyAnimation] = None
        self._slide_animation: Optional[QPropertyAnimation] = None
        self._chip_animations: Dict[FilterChip, QPropertyAnimation] = {}
        self._animation_manager = None  # Will be set by parent

        # Debounce timer for search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._emit_search_changed)

        # Resize tracking
        self._last_size = (0, 0)

        set_phase("SmartFilterPanel_Creation")
        track_component("SmartFilterPanel_Initial", self, "Constructor start")
        log_main_window_change("SmartFilterPanel constructor start - CRITICAL POINT")

        self._setup_ui()

        track_component("SmartFilterPanel_AfterUI", self, "After UI setup")
        log_main_window_change("SmartFilterPanel after UI setup - CRITICAL POINT")

        self._setup_styling()
        self._setup_search_completer()

        track_component("SmartFilterPanel_Complete", self, "Constructor complete")
        log_main_window_change("SmartFilterPanel constructor complete - CRITICAL POINT")
        logger.info("SmartFilterPanel initialized")

    def _setup_ui(self):
        """Setup the filter panel UI."""
        set_phase("SmartFilterPanel_UI_Setup")
        log_main_window_change("Before SmartFilterPanel UI setup")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)  # Reduced margins
        layout.setSpacing(8)  # Reduced spacing to prevent overlap

        track_component("SmartFilterPanel_LayoutCreated", self, "Layout created")
        log_main_window_change("After SmartFilterPanel layout created")

        # Search section
        search_section = self._create_search_section()
        layout.addWidget(search_section)

        track_component("SmartFilterPanel_SearchAdded", self, "Search section added")
        log_main_window_change("After search section added")

        # Filter chips section
        chips_section = self._create_filter_chips_section()
        layout.addWidget(chips_section)

        track_component("SmartFilterPanel_ChipsAdded", self, "Chips section added")
        log_main_window_change("After chips section added")

        # Sort and controls section
        controls_section = self._create_controls_section()
        layout.addWidget(controls_section)

        track_component(
            "SmartFilterPanel_ControlsAdded", self, "Controls section added"
        )
        log_main_window_change("After controls section added")

        # CRITICAL FIX: Remove ALL height constraints to prevent window expansion
        # Let the panel size itself naturally based on content without any size forcing
        # This prevents layout propagation that causes main window expansion

        track_component(
            "SmartFilterPanel_BeforeSizeConstraints", self, "Before size constraints"
        )
        log_main_window_change(
            "Before SmartFilterPanel size constraints - CRITICAL POINT"
        )

        # CRITICAL: Do NOT set any height constraints - let it size naturally
        # self.setMaximumHeight(175)  # REMOVED - this was causing the 82px expansion!

        track_component(
            "SmartFilterPanel_NoHeightConstraints", self, "No height constraints set"
        )
        log_main_window_change(
            "SmartFilterPanel no height constraints - CRITICAL POINT"
        )

        # RESPONSIVE FIX: Use proportional sizing with proper size policies
        from PyQt6.QtWidgets import QSizePolicy

        # Set responsive size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Fixed,  # Fixed height for consistent filter area
        )

        # Keep fixed height for consistent filter panel height
        self.setFixedHeight(120)

        # Use default layout constraint for responsive behavior
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetDefaultConstraint)

        track_component(
            "SmartFilterPanel_SizeIsolation", self, "Complete size isolation applied"
        )
        log_main_window_change(
            "After SmartFilterPanel complete size isolation - CRITICAL POINT"
        )

        track_component(
            "SmartFilterPanel_AfterSizePolicy", self, "After size policy set"
        )
        log_main_window_change(
            "After SmartFilterPanel size policy set - CRITICAL POINT"
        )

    def _create_search_section(self) -> QWidget:
        """Create the search input section."""
        section = QFrame()
        section.setObjectName("searchSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)  # Reduced spacing to prevent overlap

        # Search label
        search_label = QLabel("Search Sequences")
        search_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        # Remove fixed height to prevent layout issues
        # search_label.setFixedHeight(14)  # REMOVED - let it size naturally
        layout.addWidget(search_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search sequences...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        # Remove fixed height to prevent layout issues
        # self.search_input.setFixedHeight(30)  # REMOVED - let it size naturally
        layout.addWidget(self.search_input)

        # Let section size naturally to prevent window expansion
        # section.setFixedHeight(48)  # Removed to prevent layout propagation

        return section

    def _create_filter_chips_section(self) -> QWidget:
        """Create the filter chips display section."""
        section = QFrame()
        section.setObjectName("chipsSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)  # Reduced spacing

        # Chips header
        chips_header = QHBoxLayout()
        chips_label = QLabel("Active Filters")
        chips_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        # Remove fixed height to prevent layout issues
        # chips_label.setFixedHeight(14)  # REMOVED - let it size naturally

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self._clear_all_filters)
        # Remove fixed height to prevent layout issues
        # clear_btn.setFixedHeight(20)  # REMOVED - let it size naturally

        chips_header.addWidget(chips_label)
        chips_header.addStretch()
        chips_header.addWidget(clear_btn)

        layout.addLayout(chips_header)

        # Chips container with scroll - let it size naturally
        chips_scroll = QScrollArea()
        chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Remove fixed height to prevent layout issues
        # chips_scroll.setFixedHeight(32)  # REMOVED - let it size naturally

        self.filter_chips_container = QWidget()
        self.filter_chips_layout = QHBoxLayout(self.filter_chips_container)
        self.filter_chips_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_chips_layout.setSpacing(8)
        self.filter_chips_layout.addStretch()

        chips_scroll.setWidget(self.filter_chips_container)
        layout.addWidget(chips_scroll)

        # Let section size naturally to prevent window expansion
        # section.setFixedHeight(58)  # Removed to prevent layout propagation

        return section

    def _create_controls_section(self) -> QWidget:
        """Create the sort and filter controls section."""
        section = QFrame()
        section.setObjectName("controlsSection")
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)  # Reduced spacing to prevent overlap

        # Sort controls
        sort_label = QLabel("Sort by:")
        sort_label.setFont(QFont("Segoe UI", 9))  # Reduced font size

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(
            [
                "Name",
                "Difficulty",
                "Length",
                "Date Created",
                "Date Modified",
                "Favorites",
            ]
        )
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        # Remove fixed height to prevent layout issues
        # self.sort_combo.setFixedHeight(28)  # REMOVED - let it size naturally

        self.sort_order_btn = QPushButton("↑ Ascending")
        self.sort_order_btn.setObjectName("sortOrderButton")
        self.sort_order_btn.clicked.connect(self._toggle_sort_order)
        # Remove fixed height to prevent layout issues
        # self.sort_order_btn.setFixedHeight(28)  # REMOVED - let it size naturally

        # Quick filter buttons
        quick_filters_label = QLabel("Quick Filters:")
        quick_filters_label.setFont(QFont("Segoe UI", 9))  # Reduced font size

        favorites_btn = QPushButton("Favorites")
        favorites_btn.setObjectName("quickFilterButton")
        favorites_btn.clicked.connect(lambda: self._add_quick_filter("favorites"))
        # Remove fixed height to prevent layout issues
        # favorites_btn.setFixedHeight(28)  # REMOVED - let it size naturally

        high_diff_btn = QPushButton("High Difficulty")
        high_diff_btn.setObjectName("quickFilterButton")
        high_diff_btn.clicked.connect(lambda: self._add_quick_filter("high_difficulty"))
        # Remove fixed height to prevent layout issues
        # high_diff_btn.setFixedHeight(28)  # REMOVED - let it size naturally

        layout.addWidget(sort_label)
        layout.addWidget(self.sort_combo)
        layout.addWidget(self.sort_order_btn)
        layout.addSpacerItem(
            QSpacerItem(15, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        )
        layout.addWidget(quick_filters_label)
        layout.addWidget(favorites_btn)
        layout.addWidget(high_diff_btn)
        layout.addStretch()

        # Let section size naturally to prevent window expansion
        # section.setFixedHeight(36)  # Removed to prevent layout propagation

        return section

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            """
            SmartFilterPanel {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
            }
            
            QFrame#searchSection, QFrame#chipsSection, QFrame#controlsSection {
                background: transparent;
                border: none;
            }
            
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }
            
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 18px;
                padding: 8px 16px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
            }
            
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(76, 175, 80, 0.6);
            }
            
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
            
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 6px 12px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                min-width: 120px;
            }
            
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
                height: 0px;
            }
            
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 6px 16px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
                color: rgba(255, 255, 255, 1.0);
            }
            
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
            
            QPushButton#clearButton {
                background: rgba(255, 107, 107, 0.2);
                border: 1px solid rgba(255, 107, 107, 0.4);
                color: rgba(255, 255, 255, 0.9);
            }
            
            QPushButton#clearButton:hover {
                background: rgba(255, 107, 107, 0.3);
                border: 1px solid rgba(255, 107, 107, 0.6);
            }
            
            QPushButton#sortOrderButton {
                min-width: 100px;
            }
            
            QPushButton#quickFilterButton {
                background: rgba(76, 175, 80, 0.2);
                border: 1px solid rgba(76, 175, 80, 0.4);
            }
            
            QPushButton#quickFilterButton:hover {
                background: rgba(76, 175, 80, 0.3);
                border: 1px solid rgba(76, 175, 80, 0.6);
            }
            
            QScrollArea {
                background: transparent;
                border: none;
            }
            
            QScrollBar:horizontal {
                background: rgba(255, 255, 255, 0.1);
                height: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """
        )

    def _setup_search_completer(self):
        """Setup auto-complete for search input."""
        self.search_completer = QCompleter()
        self.search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_input.setCompleter(self.search_completer)

    def _on_search_text_changed(self, text: str):
        """Handle search text changes with debouncing."""
        self._search_timer.stop()
        self._search_timer.start(300)  # 300ms debounce

    def _emit_search_changed(self):
        """Emit search changed signal after debounce."""
        search_text = self.search_input.text().strip()
        self.search_changed.emit(search_text)

    def _on_sort_changed(self, sort_text: str):
        """Handle sort criteria changes."""
        sort_mapping = {
            "Name": "name",
            "Difficulty": "difficulty",
            "Length": "length",
            "Date Created": "date_created",
            "Date Modified": "date_modified",
            "Favorites": "is_favorite",
        }

        self._current_sort_by = sort_mapping.get(sort_text, "name")
        self.sort_changed.emit(self._current_sort_by, self._current_sort_order)

    def _toggle_sort_order(self):
        """Toggle sort order between ascending and descending."""
        if self._current_sort_order == SortOrder.ASC:
            self._current_sort_order = SortOrder.DESC
            self.sort_order_btn.setText("↓ Descending")
        else:
            self._current_sort_order = SortOrder.ASC
            self.sort_order_btn.setText("↑ Ascending")

        self.sort_changed.emit(self._current_sort_by, self._current_sort_order)

    def _add_quick_filter(self, filter_type: str):
        """Add a quick filter."""
        if filter_type == "favorites":
            criteria = FilterCriteria(
                filter_type=FilterType.FAVORITES, value=True, operator="equals"
            )
        elif filter_type == "high_difficulty":
            criteria = FilterCriteria(
                filter_type=FilterType.DIFFICULTY,
                value=4,
                operator="greater_than_or_equal",
            )
        else:
            return

        self.add_filter(criteria)

    def add_filter(self, filter_criteria: FilterCriteria):
        """Add a filter criteria."""
        # Check if filter already exists
        for existing_filter in self._active_filters:
            if (
                existing_filter.filter_type == filter_criteria.filter_type
                and existing_filter.value == filter_criteria.value
                and existing_filter.operator == filter_criteria.operator
            ):
                return  # Filter already exists

        self._active_filters.append(filter_criteria)
        self._add_filter_chip(filter_criteria)
        self.filter_added.emit(filter_criteria)

    def _add_filter_chip(self, filter_criteria: FilterCriteria):
        """Add a visual filter chip."""
        chip = FilterChip(filter_criteria)
        chip.remove_requested.connect(self.remove_filter)

        # Insert before the stretch
        self.filter_chips_layout.insertWidget(
            self.filter_chips_layout.count() - 1, chip
        )

    def remove_filter(self, filter_criteria: FilterCriteria):
        """Remove a filter criteria."""
        if filter_criteria in self._active_filters:
            self._active_filters.remove(filter_criteria)
            self._remove_filter_chip(filter_criteria)
            self.filter_removed.emit(filter_criteria)

    def _remove_filter_chip(self, filter_criteria: FilterCriteria):
        """Remove the visual filter chip."""
        for i in range(self.filter_chips_layout.count()):
            item = self.filter_chips_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if (
                    isinstance(widget, FilterChip)
                    and widget.filter_criteria == filter_criteria
                ):
                    widget.setParent(None)
                    widget.deleteLater()
                    break

    def _clear_all_filters(self):
        """Clear all active filters."""
        self._active_filters.clear()

        # Remove all filter chips
        while self.filter_chips_layout.count() > 1:  # Keep the stretch
            item = self.filter_chips_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()

        self.filters_cleared.emit()

    def set_search_suggestions(self, suggestions: List[str]):
        """Set auto-complete suggestions for search."""
        self._search_suggestions = suggestions
        model = QStringListModel(suggestions)
        self.search_completer.setModel(model)

    def get_active_filters(self) -> List[FilterCriteria]:
        """Get list of active filters."""
        return self._active_filters.copy()

    def get_search_query(self) -> str:
        """Get current search query."""
        return self.search_input.text().strip()

    def get_sort_criteria(self) -> tuple[str, SortOrder]:
        """Get current sort criteria."""
        return self._current_sort_by, self._current_sort_order

    def clear_search(self):
        """Clear the search input."""
        self.search_input.clear()

    def set_search_query(self, query: str):
        """Set the search query programmatically."""
        self.search_input.setText(query)

    # ===== ANIMATION METHODS =====

    def set_animation_manager(self, animation_manager):
        """Set the animation manager for smooth effects."""
        self._animation_manager = animation_manager

    def _animate_chip_addition(self, chip: FilterChip):
        """Animate filter chip addition with slide-in effect."""
        if self._animation_manager:
            # Create slide-in animation
            slide_id = self._animation_manager.create_scale_animation(
                chip, "scale_in", duration=200
            )
            fade_id = self._animation_manager.create_fade_animation(
                chip, "fade_in", duration=200
            )

            # Create coordinated group
            group_id = self._animation_manager.create_coordinated_animation_group(
                f"chip_add_{id(chip)}", [slide_id, fade_id]
            )

            self._animation_manager.start_animation_group(group_id)

    def _animate_chip_removal(self, chip: FilterChip, callback=None):
        """Animate filter chip removal with slide-out effect."""
        if self._animation_manager:
            # Create slide-out animation
            slide_id = self._animation_manager.create_scale_animation(
                chip, "scale_out", duration=150
            )
            fade_id = self._animation_manager.create_fade_animation(
                chip, "fade_out", duration=150
            )

            # Create coordinated group
            group_id = self._animation_manager.create_coordinated_animation_group(
                f"chip_remove_{id(chip)}", [slide_id, fade_id]
            )

            # Connect to callback when animation finishes
            if callback:
                self._animation_manager.animation_group_finished.connect(
                    lambda group: callback() if group == group_id else None
                )

            self._animation_manager.start_animation_group(group_id)
        else:
            # Fallback without animation
            if callback:
                callback()

    def _animate_search_focus(self):
        """Animate search input focus with glow effect."""
        if self._animation_manager and self.search_input:
            glow_id = self._animation_manager.create_glassmorphic_glow_animation(
                self.search_input, intensity=0.3, duration=250
            )
            self._animation_manager.start_animation(glow_id)
