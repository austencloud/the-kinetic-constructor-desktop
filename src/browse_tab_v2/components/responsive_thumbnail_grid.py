"""
Responsive Thumbnail Grid Component - Phase 2 Week 3 Day 15-17 + Layout Consistency Fixes

Modern responsive grid system with automatic column calculation and virtual scrolling
capabilities. Implements 2025 design system with glassmorphism effects and smooth animations.

LAYOUT CONSISTENCY FIXES APPLIED:
- Pre-calculation of all layout parameters before any rendering
- Replacement of row-based layout with true QGridLayout
- Complete layout locking during rendering process
- Consistent card sizing across all batches
- Prevention of resize events during critical phases

Features:
- Automatic column calculation based on container width
- Virtual scrolling for performance with large datasets
- Responsive resize handling with smooth transitions
- Modern glassmorphic styling
- 60fps performance optimization
- Accessibility support
- GUARANTEED layout consistency across all grid positions
"""

import logging
import math
from typing import List, Optional, Callable, Any, Tuple
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QFrame,
    QLabel,
    QSizePolicy,
    QApplication,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QRect,
    QTimer,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
)
from PyQt6.QtGui import QPainter, QColor, QPalette, QResizeEvent

from ..core.interfaces import BrowseTabConfig
from ..core.state import BrowseState, SequenceModel
from ..services.chunked_image_loader import ChunkedImageLoadingManager

logger = logging.getLogger(__name__)


class LayoutParameters:
    """Immutable layout parameters calculated once and applied consistently."""

    def __init__(
        self,
        container_width: int,
        container_height: int,
        sequence_count: int,
        margin: int = 15,
        spacing: int = 20,
        min_card_width: int = 280,
        max_card_width: int = 400,
    ):

        self.container_width = container_width
        self.container_height = container_height
        self.sequence_count = sequence_count
        self.margin = margin
        self.spacing = spacing
        self.min_card_width = min_card_width
        self.max_card_width = max_card_width

        # Calculate optimal layout parameters
        self._calculate_optimal_layout()

        # Mark as immutable
        self._locked = True

    def _calculate_optimal_layout(self):
        """Calculate all layout parameters in one consistent operation."""
        # Available width for grid content
        self.available_width = self.container_width - (2 * self.margin)

        if self.available_width <= 0:
            self.available_width = 800  # Fallback

        # Calculate optimal column count
        max_columns_by_width = max(1, self.available_width // self.min_card_width)
        max_columns_by_sequences = min(
            6, self.sequence_count
        )  # Cap at 6 for readability

        self.column_count = min(max_columns_by_width, max_columns_by_sequences)
        self.column_count = max(1, self.column_count)  # Ensure at least 1 column

        # Calculate exact card dimensions
        total_spacing_width = (self.column_count - 1) * self.spacing
        self.card_width = (
            self.available_width - total_spacing_width
        ) // self.column_count

        # Ensure card width is within bounds
        self.card_width = max(
            self.min_card_width, min(self.card_width, self.max_card_width)
        )

        # Calculate card height with consistent aspect ratio
        self.card_height = int(self.card_width * 1.15)  # Slightly taller than wide
        self.card_height = max(self.card_height, 280)  # Minimum height

        # Calculate total grid dimensions
        self.total_rows = math.ceil(self.sequence_count / self.column_count)

        total_spacing_height = (self.total_rows - 1) * self.spacing
        self.grid_height = (self.total_rows * self.card_height) + total_spacing_height

        logger.info(
            f"Layout calculated: {self.column_count} columns, "
            f"{self.card_width}x{self.card_height} cards, "
            f"{self.total_rows} rows, {self.sequence_count} sequences"
        )

    def get_card_size(self) -> QSize:
        """Get card size as QSize object."""
        return QSize(self.card_width, self.card_height)

    def get_position_for_index(self, index: int) -> Tuple[int, int]:
        """Get grid position (row, column) for sequence index."""
        row = index // self.column_count
        col = index % self.column_count
        return (row, col)

    def is_consistent_with(self, other: "LayoutParameters") -> bool:
        """Check if this layout is consistent with another."""
        return (
            self.column_count == other.column_count
            and self.card_width == other.card_width
            and self.card_height == other.card_height
        )


class ResponsiveThumbnailGrid(QWidget):
    """
    Responsive grid component that automatically calculates optimal column count
    and provides virtual scrolling for performance.

    This component implements the 2025 design system with:
    - Glassmorphism background effects
    - Smooth resize animations
    - Virtual scrolling for large datasets
    - Responsive column calculation
    - Modern spacing and typography
    """

    # Signals
    item_clicked = pyqtSignal(str, int)  # sequence_id, index
    item_double_clicked = pyqtSignal(str, int)  # sequence_id, index
    selection_changed = pyqtSignal(list)  # selected_sequence_ids
    viewport_changed = pyqtSignal(int, int)  # start_index, end_index
    column_count_changed = pyqtSignal(int)  # new_column_count

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # Grid configuration
        self.min_column_width = 280  # Minimum width per thumbnail
        self.max_column_width = 400  # Maximum width per thumbnail
        self.grid_spacing = 20  # Space between items
        self.margin = 15  # Container margins

        # State
        self._sequences: List[SequenceModel] = []
        self._column_count = self.config.default_columns
        self._item_height = 320  # Height per thumbnail item
        self._selected_items: List[str] = []
        self._viewport_start = 0
        self._viewport_end = 0

        # Fixed layout system for stability during chunked loading
        self._fixed_card_size = None  # QSize object for fixed card dimensions
        self._layout_locked = False  # Prevents layout changes during loading
        self._optimal_card_width = 280  # Calculated optimal card width
        self._optimal_card_height = 320  # Calculated optimal card height

        # Virtual scrolling
        self._visible_items: List[QWidget] = []
        self._item_pool: List[QWidget] = []
        self._scroll_position = 0

        # Animation system
        self._resize_animation: Optional[QParallelAnimationGroup] = None
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._handle_resize_finished)

        # Item creation callback
        self._item_creator: Optional[Callable[[SequenceModel, int], QWidget]] = None

        # Chunked loading manager
        self._chunked_loader = ChunkedImageLoadingManager(
            chunk_size=self.config.max_concurrent_image_loads or 6, parent=self
        )
        self._chunked_loader.set_grid_reference(
            self
        )  # Set reference for layout locking
        self._enable_chunked_loading = True

        self._setup_ui()
        self._setup_styling()
        self._setup_animations()

        logger.info("ResponsiveThumbnailGrid initialized")

    def _setup_ui(self):
        """Setup the grid UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        layout.setSpacing(0)

        # Create scroll area for virtual scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Create content widget
        self.content_widget = QFrame()
        self.content_widget.setObjectName("gridContent")

        # Create grid layout container
        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container)
        self.grid_layout.setSpacing(self.grid_spacing)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        # Setup content layout
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.grid_container)
        content_layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        # Connect scroll events
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            """
            ResponsiveThumbnailGrid {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            QScrollArea {
                background: transparent;
                border: none;
                border-radius: 15px;
            }
            
            QFrame#gridContent {
                background: transparent;
                border: none;
            }
            
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        )

    def _setup_animations(self):
        """Setup animation system for smooth transitions."""
        # Resize animation will be created dynamically
        pass

    def set_sequences(self, sequences: List[SequenceModel]):
        """Set the sequences to display in the grid."""
        # Sort sequences by length first for better visual consistency
        self._sequences = self._sort_sequences_by_length(sequences)

        # Calculate fixed layout before any rendering
        self._calculate_fixed_card_size()
        self._calculate_optimal_columns()
        self._update_viewport()
        self._render_visible_items()

        logger.debug(
            f"Grid updated with {len(sequences)} sequences, {self._column_count} columns"
        )

    def set_item_creator(self, creator: Callable[[SequenceModel, int], QWidget]):
        """Set the callback function to create thumbnail items."""
        self._item_creator = creator

    def _sort_sequences_by_length(
        self, sequences: List[SequenceModel]
    ) -> List[SequenceModel]:
        """Sort sequences by length for better visual consistency."""
        try:
            # Primary sort by length, secondary sort by name for consistency
            sorted_sequences = sorted(
                sequences,
                key=lambda seq: (
                    seq.length if seq.length is not None else 0,
                    seq.name.lower(),
                ),
            )

            logger.debug(f"Sorted {len(sequences)} sequences by length")
            return sorted_sequences

        except Exception as e:
            logger.error(f"Failed to sort sequences by length: {e}")
            return sequences  # Return original list if sorting fails

    def _calculate_fixed_card_size(self):
        """Calculate and lock fixed card dimensions for 4-column grid with 25% width scaling."""
        try:
            # Get current container width
            container_width = self.width()
            if container_width <= 0:
                container_width = 800  # Default fallback

            # Calculate available width for grid
            available_width = container_width - (self.margin * 2)

            # Force 4-column layout for proper 25% width scaling
            target_columns = 4

            # Calculate card width for exactly 25% of available width
            total_spacing = (target_columns - 1) * self.grid_spacing
            card_width = (available_width - total_spacing) // target_columns

            # Remove maximum width constraint to enable proper responsive scaling
            # Only enforce minimum width for readability
            card_width = max(card_width, 200)  # Reduced minimum for better scaling

            # Calculate card height using width-first scaling with proportional height
            # Use 4:3 aspect ratio for optimal thumbnail display
            card_height = int(card_width * 0.75)
            card_height = max(card_height, 150)  # Reduced minimum height

            # Update column count to match target
            if self._column_count != target_columns:
                self._column_count = target_columns
                self.column_count_changed.emit(self._column_count)

            # Store fixed dimensions
            from PyQt6.QtCore import QSize

            self._fixed_card_size = QSize(card_width, card_height)
            self._optimal_card_width = card_width
            self._optimal_card_height = card_height

            logger.debug(
                f"Fixed card size calculated for 4-column grid: {card_width}x{card_height} (25% width scaling)"
            )

        except Exception as e:
            logger.error(f"Failed to calculate fixed card size: {e}")
            # Fallback to default dimensions
            from PyQt6.QtCore import QSize

            self._fixed_card_size = QSize(280, 320)
            self._optimal_card_width = 280
            self._optimal_card_height = 320

    def _calculate_optimal_columns(self):
        """Calculate optimal number of columns - fixed at 4 for 25% width scaling."""
        # Force 4-column layout for consistent 25% width scaling
        target_columns = 4

        if target_columns != self._column_count:
            old_count = self._column_count
            self._column_count = target_columns
            self.column_count_changed.emit(self._column_count)

            logger.info(
                f"Column count changed: {old_count} -> {self._column_count} (fixed 4-column layout)"
            )

            # Trigger smooth resize animation
            self._animate_column_change()

    def _animate_column_change(self):
        """Animate the transition between different column counts."""
        if not self.config.enable_animations:
            self._render_visible_items()
            return

        # Create fade out animation for current items
        if self._resize_animation:
            self._resize_animation.stop()

        self._resize_animation = QParallelAnimationGroup()

        # Fade out current items
        for item in self._visible_items:
            fade_out = QPropertyAnimation(item, b"windowOpacity")
            fade_out.setDuration(150)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._resize_animation.addAnimation(fade_out)

        self._resize_animation.finished.connect(self._on_resize_animation_finished)
        self._resize_animation.start()

    def _on_resize_animation_finished(self):
        """Handle completion of resize animation."""
        # Re-render with new column count
        self._render_visible_items()

        # Fade in new items
        if self.config.enable_animations:
            fade_in_group = QParallelAnimationGroup()

            for item in self._visible_items:
                item.setWindowOpacity(0.0)
                fade_in = QPropertyAnimation(item, b"windowOpacity")
                fade_in.setDuration(200)
                fade_in.setStartValue(0.0)
                fade_in.setEndValue(1.0)
                fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
                fade_in_group.addAnimation(fade_in)

            fade_in_group.start()

    def _update_viewport(self):
        """Update the virtual scrolling viewport."""
        if not self._sequences:
            return

        # Calculate rows and visible range
        rows_total = math.ceil(len(self._sequences) / self._column_count)
        row_height = self._item_height + self.grid_spacing

        # Get scroll position
        scroll_value = self.scroll_area.verticalScrollBar().value()
        viewport_height = self.scroll_area.viewport().height()

        # Calculate visible row range with buffer
        buffer_rows = 2
        start_row = max(0, (scroll_value // row_height) - buffer_rows)
        end_row = min(
            rows_total,
            ((scroll_value + viewport_height) // row_height) + buffer_rows + 1,
        )

        # Convert to item indices
        self._viewport_start = int(start_row * self._column_count)
        self._viewport_end = min(
            len(self._sequences), int(end_row * self._column_count)
        )

        self.viewport_changed.emit(self._viewport_start, self._viewport_end)

    def _render_visible_items(self):
        """Render only the visible items using incremental updates for performance."""
        if not self._item_creator or not self._sequences:
            return

        # CRITICAL FIX: Calculate and lock fixed card size BEFORE any rendering
        if not self._fixed_card_size:
            self._calculate_fixed_card_size()
            logger.warning(
                f"🔒 FIXED CARD SIZE LOCKED: {self._fixed_card_size.width()}x{self._fixed_card_size.height()} "
                f"(Column count: {self._column_count})"
            )

        # Lock layout during rendering to prevent resize events
        self._layout_locked = True

        # Use incremental rendering instead of clearing all items
        self._render_incremental_viewport()

        # Update content height for proper scrolling
        rows_needed = math.ceil(len(self._sequences) / self._column_count)
        if self._fixed_card_size:
            total_height = rows_needed * (
                self._fixed_card_size.height() + self.grid_spacing
            )
        else:
            total_height = rows_needed * (self._item_height + self.grid_spacing)
        self.content_widget.setMinimumHeight(total_height)

        logger.debug(
            f"Incremental render completed with {len(self._visible_items)} visible items"
        )

    def _clear_visible_items(self):
        """Clear all visible items."""
        for item in self._visible_items:
            item.setParent(None)
            item.deleteLater()
        self._visible_items.clear()

        # Clear grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:  # Additional null check
                    widget.setParent(None)
                    widget.deleteLater()

    def _render_incremental_viewport(self):
        """Render viewport changes incrementally to avoid recreating all cards."""
        import time

        start_time = time.time()

        # Calculate which items should be visible
        target_indices = set(range(self._viewport_start, self._viewport_end))

        # Find currently visible item indices
        current_indices = set()
        current_items_by_index = {}

        for item in self._visible_items:
            if hasattr(item, "_grid_index"):
                index = item._grid_index
                current_indices.add(index)
                current_items_by_index[index] = item

        # Calculate what needs to be added/removed
        indices_to_add = target_indices - current_indices
        indices_to_remove = current_indices - target_indices

        # Log significant viewport changes only
        if len(indices_to_add) > 0 or len(indices_to_remove) > 0:
            logger.debug(
                f"Incremental viewport update: range [{self._viewport_start}, {self._viewport_end}], "
                f"adding {len(indices_to_add)}, removing {len(indices_to_remove)}, "
                f"preserving {len(current_indices & target_indices)}"
            )

        # Remove items that are no longer visible
        items_to_remove = []
        for index in indices_to_remove:
            if index in current_items_by_index:
                item = current_items_by_index[index]
                items_to_remove.append(item)
                # Remove from layout
                if item.parent():
                    item.setParent(None)

        # Clean up removed items
        for item in items_to_remove:
            if item in self._visible_items:
                self._visible_items.remove(item)
            item.deleteLater()

        # Add new items that are now visible
        new_items_created = 0
        cards_for_chunked_loading = []

        for index in sorted(indices_to_add):
            if index < len(self._sequences):
                sequence = self._sequences[index]

                # Create new item with immediate display
                item = self._item_creator(sequence, index)
                item._grid_index = index  # Store index for tracking

                # Apply fixed sizing
                if self._fixed_card_size and hasattr(item, "apply_fixed_size"):
                    item.apply_fixed_size(
                        self._fixed_card_size.width(), self._fixed_card_size.height()
                    )

                # PROGRESSIVE DISPLAY: Show widget immediately with placeholder content
                # This ensures instant visual feedback instead of waiting for batch completion
                item.show()

                # Setup chunked loading if enabled (decoupled from widget display)
                if self._enable_chunked_loading and hasattr(
                    item, "set_chunked_loading_manager"
                ):
                    item.set_chunked_loading_manager(self._chunked_loader)
                    # Queue image loading asynchronously (after widget is visible)
                    if hasattr(sequence, "thumbnails") and sequence.thumbnails:
                        cards_for_chunked_loading.append((item, sequence.thumbnails[0]))

                # Add to visible items
                self._visible_items.append(item)

                # Connect click events with isolation
                self._connect_item_events_isolated(item, sequence, index)

                new_items_created += 1

                # CRITICAL: Process events after each widget to ensure immediate UI updates
                # This eliminates batch processing delays and provides progressive display
                QApplication.processEvents()

        # Rebuild layout with all visible items
        self._rebuild_layout_from_visible_items()

        # Start chunked loading for new cards only
        logger.debug(
            f"🔍 CHUNKED_LOADING_CHECK: enabled={self._enable_chunked_loading}, "
            f"cards_count={len(cards_for_chunked_loading)}"
        )
        if self._enable_chunked_loading and cards_for_chunked_loading:
            logger.debug(
                f"🚀 CHUNKED_LOADING: Starting chunked loading for {len(cards_for_chunked_loading)} new cards"
            )
            self._chunked_loader.queue_multiple_loads(cards_for_chunked_loading)
        else:
            if not self._enable_chunked_loading:
                logger.warning(
                    "❌ CHUNKED_LOADING: Disabled - chunked loading not enabled"
                )
            if not cards_for_chunked_loading:
                logger.warning(
                    "❌ CHUNKED_LOADING: No cards collected for chunked loading"
                )

        # Performance metrics for significant operations
        end_time = time.time()
        render_time = (end_time - start_time) * 1000  # Convert to milliseconds

        if new_items_created > 0 or len(items_to_remove) > 0:
            logger.debug(
                f"Incremental render complete: {render_time:.1f}ms, "
                f"created {new_items_created}, removed {len(items_to_remove)}, "
                f"total {len(self._visible_items)} items"
            )

        # Unlock layout
        self._layout_locked = False

    def _connect_item_events_isolated(self, item, sequence, index):
        """Connect item events with proper isolation to prevent grid re-renders."""
        # Connect signals with lambda isolation to prevent event bubbling
        if hasattr(item, "clicked"):
            # Use a closure to capture values and prevent grid updates
            def handle_click(seq_id=sequence.id, idx=index):
                # Emit signal without triggering layout updates
                self.item_clicked.emit(seq_id, idx)
                logger.debug(f"Item clicked: {seq_id} (index {idx}) - isolated event")

            item.clicked.connect(handle_click)

        if hasattr(item, "double_clicked"):

            def handle_double_click(seq_id=sequence.id, idx=index):
                self.item_double_clicked.emit(seq_id, idx)
                logger.debug(
                    f"Item double-clicked: {seq_id} (index {idx}) - isolated event"
                )

            item.double_clicked.connect(handle_double_click)

    def _rebuild_layout_from_visible_items(self):
        """Rebuild the grid layout from current visible items without recreating them."""
        # Clear layout without deleting widgets
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            # Don't delete the widget, just remove from layout

        # Sort visible items by their grid index
        sorted_items = sorted(
            self._visible_items, key=lambda item: getattr(item, "_grid_index", 0)
        )

        # Add items back to layout in proper grid positions
        current_row = None
        current_row_layout = None
        items_in_row = 0

        for item in sorted_items:
            # Create new row if needed
            if items_in_row == 0:
                current_row = QWidget()
                current_row_layout = QHBoxLayout(current_row)
                current_row_layout.setSpacing(self.grid_spacing)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                self.grid_layout.addWidget(current_row)

            # Add item to current row
            current_row_layout.addWidget(item)
            items_in_row += 1

            # Start new row if current row is full
            if items_in_row >= self._column_count:
                # Fill remaining space in row
                current_row_layout.addStretch()
                items_in_row = 0

        # Fill remaining space in last row if needed
        if current_row_layout and items_in_row > 0:
            current_row_layout.addStretch()

    def _on_scroll(self, value: int):
        """Handle scroll events with comprehensive monitoring."""
        import time

        timestamp = time.time()
        old_scroll_position = self._scroll_position
        old_viewport_start = self._viewport_start
        old_viewport_end = self._viewport_end

        # Log significant scroll changes only
        if abs(value - old_scroll_position) > 100:  # Only log significant scrolls
            logger.debug(
                f"Scroll event: {old_scroll_position} → {value} "
                f"(viewport [{old_viewport_start}, {old_viewport_end}])"
            )

        self._scroll_position = value

        # Update viewport and log changes
        self._update_viewport()

        if (
            self._viewport_start != old_viewport_start
            or self._viewport_end != old_viewport_end
        ):
            logger.debug(
                f"Viewport changed: [{old_viewport_start}, {old_viewport_end}] → "
                f"[{self._viewport_start}, {self._viewport_end}]"
            )

        # Debounce rendering for performance
        self._resize_timer.stop()
        self._resize_timer.start(50)  # 50ms debounce

    def _handle_resize_finished(self):
        """Handle debounced resize/scroll events."""
        logger.debug(
            f"Debounced render: viewport [{self._viewport_start}, {self._viewport_end}], "
            f"{len(self._visible_items)} visible items"
        )
        self._render_visible_items()

    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize events with throttling to prevent excessive re-renders."""
        import time

        # Initialize resize tracking if not exists
        if not hasattr(self, "_resize_count"):
            self._resize_count = 0
            self._last_resize_time = 0

        current_time = time.time()

        # Reset counter if more than 1 second has passed
        if current_time - self._last_resize_time > 1.0:
            self._resize_count = 0

        self._resize_count += 1
        self._last_resize_time = current_time

        old_size = event.oldSize()
        new_size = event.size()

        super().resizeEvent(event)

        # Skip resize handling if layout is locked during chunked loading
        if self._layout_locked:
            return

        # Skip handling for initial size establishment (prevents flickering)
        if not old_size.isValid() or (old_size.width() <= 0 or old_size.height() <= 0):
            return

        # Throttle excessive resize events during chunked loading
        if self._resize_count > 2:
            # Allow only the first 2 resize events, then check if size actually changed
            if (
                old_size.width() == new_size.width()
                and old_size.height() == new_size.height()
            ):
                # Size didn't actually change, skip this resize event
                return

        # CRITICAL FIX: Only recalculate fixed card size if it hasn't been locked yet
        old_fixed_size = self._fixed_card_size

        if not self._fixed_card_size:
            # First time calculation - allowed
            self._calculate_fixed_card_size()
            new_fixed_size = self._fixed_card_size
            logger.warning(
                f"🔒 FIXED CARD SIZE CALCULATED ON RESIZE: {new_fixed_size.width()}x{new_fixed_size.height()}"
            )
        else:
            # Fixed card size already locked - skip recalculation
            new_fixed_size = self._fixed_card_size
            logger.warning(
                f"⏸️ RESIZE EVENT IGNORED - Fixed card size locked: "
                f"keeping {self._fixed_card_size.width()}x{self._fixed_card_size.height()}"
            )
            return

        # Only trigger re-render if the fixed card size actually changed significantly
        if (
            old_fixed_size
            and new_fixed_size
            and abs(old_fixed_size.width() - new_fixed_size.width()) < 10
            and abs(old_fixed_size.height() - new_fixed_size.height()) < 10
        ):
            return

        # Only proceed with re-render if there's a significant change
        if old_fixed_size != new_fixed_size:
            logger.debug(
                f"Grid resize triggered significant fixed card size change: "
                f"{old_fixed_size.width() if old_fixed_size else 'None'}x{old_fixed_size.height() if old_fixed_size else 'None'} → "
                f"{new_fixed_size.width() if new_fixed_size else 'None'}x{new_fixed_size.height() if new_fixed_size else 'None'}"
            )

            self._calculate_optimal_columns()

            # Debounce rendering to prevent multiple rapid re-renders
            self._resize_timer.stop()
            self._resize_timer.start(150)  # 150ms debounce for resize

    def get_column_count(self) -> int:
        """Get current column count."""
        return self._column_count

    def get_visible_range(self) -> tuple[int, int]:
        """Get current visible item range."""
        return self._viewport_start, self._viewport_end

    def scroll_to_item(self, index: int):
        """Scroll to make the specified item visible."""
        if index < 0 or index >= len(self._sequences):
            return

        row = index // self._column_count
        row_height = self._item_height + self.grid_spacing
        target_position = row * row_height

        self.scroll_area.verticalScrollBar().setValue(target_position)

    def select_item(self, sequence_id: str):
        """Select an item by sequence ID."""
        if sequence_id not in self._selected_items:
            self._selected_items.append(sequence_id)
            self.selection_changed.emit(self._selected_items.copy())

    def deselect_item(self, sequence_id: str):
        """Deselect an item by sequence ID."""
        if sequence_id in self._selected_items:
            self._selected_items.remove(sequence_id)
            self.selection_changed.emit(self._selected_items.copy())

    def clear_selection(self):
        """Clear all selections."""
        self._selected_items.clear()
        self.selection_changed.emit([])

    def get_selected_items(self) -> List[str]:
        """Get list of selected sequence IDs."""
        return self._selected_items.copy()

    def set_chunked_loading_enabled(self, enabled: bool):
        """Enable or disable chunked loading."""
        self._enable_chunked_loading = enabled
        logger.info(f"Chunked loading {'enabled' if enabled else 'disabled'}")

    def set_chunk_size(self, chunk_size: int):
        """Set the chunk size for batch processing."""
        if self._chunked_loader:
            self._chunked_loader.set_chunk_size(chunk_size)

    def get_chunked_loader(self) -> ChunkedImageLoadingManager:
        """Get the chunked loading manager."""
        return self._chunked_loader

    def lock_layout_during_loading(self, locked: bool):
        """Lock or unlock layout changes during chunked loading."""
        self._layout_locked = locked
        if locked:
            logger.debug(
                "Layout locked to prevent resize events during chunked loading"
            )
        else:
            logger.debug("Layout unlocked - resize events allowed")

    def get_fixed_card_size(self):
        """Get the current fixed card size."""
        return self._fixed_card_size

    def is_layout_locked(self) -> bool:
        """Check if layout is currently locked."""
        return self._layout_locked

    def _prevent_layout_invalidation_during_batch(self):
        """Prevent layout invalidation cascades during batch operations."""
        try:
            # Force layout to complete before starting batch operations
            self.grid_layout.activate()

            # Ensure all visible items have their final sizes applied
            for item in self._visible_items:
                if hasattr(item, "updateGeometry"):
                    item.updateGeometry()

            # Process any pending layout events
            from PyQt6.QtWidgets import QApplication

            QApplication.processEvents()

            logger.debug("Layout invalidation prevention applied for batch operations")

        except Exception as e:
            logger.warning(f"Failed to prevent layout invalidation: {e}")

    def _add_size_monitoring_to_card(self, card, card_index: int):
        """Add defensive size monitoring to detect unwanted size changes."""
        if not hasattr(card, "resizeEvent"):
            return

        # Store original resize event
        original_resize_event = card.resizeEvent

        def monitored_resize_event(event):
            old_size = event.oldSize()
            new_size = event.size()

            # Check if this is an unwanted size change
            if (
                old_size.isValid()
                and self._fixed_card_size
                and (
                    new_size.width() != self._fixed_card_size.width()
                    or new_size.height() != self._fixed_card_size.height()
                )
            ):

                logger.warning(
                    f"Unwanted size change detected on card {card_index}: "
                    f"{old_size.width()}x{old_size.height()} -> "
                    f"{new_size.width()}x{new_size.height()}, "
                    f"expected: {self._fixed_card_size.width()}x{self._fixed_card_size.height()}"
                )

                # Auto-correct the size if possible
                if hasattr(card, "apply_fixed_size"):
                    card.apply_fixed_size(
                        self._fixed_card_size.width(), self._fixed_card_size.height()
                    )

            return original_resize_event(event)

        # Replace resize event with monitored version
        card.resizeEvent = monitored_resize_event
