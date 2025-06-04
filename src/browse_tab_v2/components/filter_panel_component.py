"""
Filter Panel Component - Modular Architecture

Extracted from browse_tab_view.py to provide focused search and filtering functionality.
Handles all filter-related operations including search, filter management, and sort controls.

Responsibilities:
- Search query management with debouncing
- Filter criteria management (add/remove/clear)
- Sort criteria management
- Integration with SmartFilterPanel UI component
- Signal coordination with parent view
"""

import logging
from typing import Optional, List, Dict, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from ..core.interfaces import FilterCriteria, SortOrder, SearchCriteria, BrowseTabConfig
from ..debug.window_resize_tracker import track_component, log_main_window_change
from .smart_filter_panel import SmartFilterPanel
from .animation_system import AnimationManager

logger = logging.getLogger(__name__)


class FilterPanelComponent(QWidget):
    """
    Modular filter panel component handling search and filtering functionality.
    
    This component encapsulates all filter-related operations and provides
    a clean interface for the main view to interact with filtering features.
    """
    
    # Signals for parent coordination
    search_changed = pyqtSignal(str)  # search_query
    filter_added = pyqtSignal(object)  # FilterCriteria
    filter_removed = pyqtSignal(object)  # FilterCriteria
    filters_cleared = pyqtSignal()
    sort_changed = pyqtSignal(str, object)  # sort_by, sort_order
    
    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)
        
        self.config = config or BrowseTabConfig()
        
        # State management
        self._active_filters: List[FilterCriteria] = []
        self._current_sort_by = "name"
        self._current_sort_order = SortOrder.ASC
        self._search_query = ""
        
        # UI components
        self.filter_panel: Optional[SmartFilterPanel] = None
        self.animation_manager: Optional[AnimationManager] = None
        
        # Search debouncing
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._emit_search_changed)
        
        # Performance tracking
        self._last_size = (0, 0)
        
        track_component("FilterPanelComponent_Initial", self, "Constructor start")
        log_main_window_change("FilterPanelComponent constructor start")
        
        self._setup_ui()
        self._connect_signals()
        
        track_component("FilterPanelComponent_Complete", self, "Constructor complete")
        log_main_window_change("FilterPanelComponent constructor complete")
        logger.info("FilterPanelComponent initialized")
    
    def _setup_ui(self):
        """Setup the filter panel UI with size isolation."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create filter container with responsive sizing
        filter_container = QFrame()
        filter_container.setFixedHeight(120)  # Keep fixed height for consistency
        filter_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Fixed,  # Fixed height for consistent filter area
        )
        
        filter_container_layout = QVBoxLayout(filter_container)
        filter_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create SmartFilterPanel
        track_component("FilterPanelComponent_BeforeSmartPanel", self, "Before creating SmartFilterPanel")
        log_main_window_change("Before creating SmartFilterPanel - CRITICAL POINT")
        
        self.filter_panel = SmartFilterPanel()
        filter_container_layout.addWidget(self.filter_panel)
        
        track_component("FilterPanelComponent_AfterSmartPanel", self, "After creating SmartFilterPanel")
        log_main_window_change("After creating SmartFilterPanel - CRITICAL POINT")
        
        layout.addWidget(filter_container)
        
        # Set responsive size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Fixed,  # Fixed height for consistent filter area
        )
        
        track_component("FilterPanelComponent_SizeIsolation", self, "Complete size isolation applied")
        log_main_window_change("After FilterPanelComponent size isolation applied")
    
    def _connect_signals(self):
        """Connect SmartFilterPanel signals to component signals."""
        if self.filter_panel:
            self.filter_panel.search_changed.connect(self._on_search_changed)
            self.filter_panel.filter_added.connect(self._on_filter_added)
            self.filter_panel.filter_removed.connect(self._on_filter_removed)
            self.filter_panel.filters_cleared.connect(self._on_filters_cleared)
            self.filter_panel.sort_changed.connect(self._on_sort_changed)
    
    def set_animation_manager(self, animation_manager: AnimationManager):
        """Set animation manager for smooth filter animations."""
        self.animation_manager = animation_manager
        if self.filter_panel:
            self.filter_panel.set_animation_manager(animation_manager)
    
    def _on_search_changed(self, query: str):
        """Handle search query changes with debouncing."""
        self._search_query = query
        logger.debug(f"Search changed: {query}")
        
        # Use QTimer to debounce search
        if hasattr(self, "_search_timer"):
            self._search_timer.stop()
        
        self._search_timer.start(300)  # 300ms debounce
    
    def _emit_search_changed(self):
        """Emit search changed signal after debouncing."""
        self.search_changed.emit(self._search_query)
    
    def _on_filter_added(self, filter_criteria: FilterCriteria):
        """Handle filter addition."""
        self._active_filters.append(filter_criteria)
        logger.info(f"Filter added: {filter_criteria}")
        self.filter_added.emit(filter_criteria)
    
    def _on_filter_removed(self, filter_criteria: FilterCriteria):
        """Handle filter removal."""
        if filter_criteria in self._active_filters:
            self._active_filters.remove(filter_criteria)
        logger.info(f"Filter removed: {filter_criteria}")
        self.filter_removed.emit(filter_criteria)
    
    def _on_filters_cleared(self):
        """Handle clearing all filters."""
        self._active_filters.clear()
        logger.info("All filters cleared")
        self.filters_cleared.emit()
    
    def _on_sort_changed(self, sort_by: str, sort_order: SortOrder):
        """Handle sort criteria changes."""
        self._current_sort_by = sort_by
        self._current_sort_order = sort_order
        logger.info(f"Sort changed: {sort_by} {sort_order}")
        self.sort_changed.emit(sort_by, sort_order)
    
    # Public interface methods
    def get_active_filters(self) -> List[FilterCriteria]:
        """Get currently active filters."""
        return self._active_filters.copy()
    
    def get_current_sort(self) -> tuple:
        """Get current sort criteria."""
        return (self._current_sort_by, self._current_sort_order)
    
    def get_search_query(self) -> str:
        """Get current search query."""
        return self._search_query
    
    def clear_all_filters(self):
        """Clear all filters programmatically."""
        if self.filter_panel:
            self.filter_panel._clear_all_filters()
    
    def add_quick_filter(self, filter_type: str):
        """Add a quick filter programmatically."""
        if self.filter_panel:
            self.filter_panel._add_quick_filter(filter_type)
    
    def sizeHint(self):
        """Provide size hint for responsive layout."""
        from PyQt6.QtCore import QSize
        return QSize(800, 120)  # Fixed height, expandable width
    
    def minimumSizeHint(self):
        """Provide minimum size hint."""
        from PyQt6.QtCore import QSize
        return QSize(400, 120)
    
    def hasHeightForWidth(self):
        """Disable height-for-width calculations."""
        return False
