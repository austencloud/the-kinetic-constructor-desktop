"""
Consistent Responsive Thumbnail Grid - Layout Consistency Fixes

This component implements the layout consistency fixes identified in the guide:
- Pre-calculation of all layout parameters before any rendering
- Replacement of row-based layout with true QGridLayout
- Complete layout locking during rendering process
- Consistent card sizing across all batches
- Prevention of resize events during critical phases

Key improvements over ResponsiveThumbnailGrid:
1. ✅ Layout inconsistency between rows (different column counts)
2. ✅ Thumbnail sizing discrepancies (first 2 rows vs subsequent rows)
3. ✅ Incremental rendering conflicts
4. ✅ Container width usage inconsistencies
5. ✅ Fixed card size calculation timing issues
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

from ..core.state import SequenceModel
from ..core.interfaces import BrowseTabConfig

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


class ConsistentResponsiveThumbnailGrid(QWidget):
    """
    Layout-consistent responsive grid that guarantees uniform appearance.

    Key improvements:
    - Pre-calculates all layout parameters before any rendering
    - Uses QGridLayout for guaranteed grid consistency
    - Locks layout during entire rendering process
    - Applies consistent sizing to all cards regardless of creation timing
    """

    # Signals
    item_clicked = pyqtSignal(str, int)  # sequence_id, index
    item_double_clicked = pyqtSignal(str, int)  # sequence_id, index
    selection_changed = pyqtSignal(list)  # selected_sequence_ids
    viewport_changed = pyqtSignal(int, int)  # start_index, end_index
    column_count_changed = pyqtSignal(int)  # new_column_count

    def __init__(self, config=None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or self._default_config()

        # Layout parameters - calculated once and locked
        self._layout_params: Optional[LayoutParameters] = None
        self._layout_locked = False
        self._rendering_in_progress = False

        # State
        self._sequences: List = []
        self._selected_items: List[str] = []

        # Virtual scrolling
        self._visible_items: List[QWidget] = []
        self._viewport_start = 0
        self._viewport_end = 0

        # Item creation callback
        self._item_creator: Optional[Callable] = None

        # Chunked loading manager
        self._chunked_loader = None

        # Resize throttling
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._handle_resize_finished)

        self._setup_ui()
        self._setup_styling()

        logger.info("ConsistentResponsiveThumbnailGrid initialized")

    def _default_config(self):
        """Provide default configuration."""

        class DefaultConfig:
            enable_animations = True
            max_concurrent_image_loads = 6

        return DefaultConfig()

    def _setup_ui(self):
        """Setup the grid UI structure with true grid layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
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

        # Create content widget with true grid layout
        self.content_widget = QFrame()
        self.content_widget.setObjectName("gridContent")

        # CRITICAL FIX: Use QGridLayout instead of row-based approach
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(20)  # Consistent spacing
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        # Connect scroll events
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            """
            ConsistentResponsiveThumbnailGrid {
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
        """
        )

    def set_sequences(self, sequences: List):
        """Set sequences with guaranteed layout consistency."""
        if self._rendering_in_progress:
            logger.warning("Cannot set sequences while rendering is in progress")
            return

        self._sequences = sequences
        logger.info(f"Setting {len(sequences)} sequences")

        # CRITICAL FIX: Pre-calculate all layout parameters before any rendering
        self._precalculate_layout_parameters()

        # Clear existing items
        self._clear_all_items()

        # Lock layout for entire rendering process
        self._lock_layout_for_rendering()

        try:
            # Render all items with consistent parameters
            self._render_all_items_consistently()

            # Update viewport
            self._update_viewport()

        finally:
            # Always unlock layout when done
            self._unlock_layout_after_rendering()

        logger.info(
            f"Grid updated with {len(sequences)} sequences, "
            f"{self._layout_params.column_count} columns"
        )

    def _precalculate_layout_parameters(self):
        """Pre-calculate all layout parameters before any rendering."""
        container_width = self.width()
        container_height = self.height()

        # Use reasonable defaults if widget not yet sized
        if container_width <= 0:
            container_width = 1200
        if container_height <= 0:
            container_height = 800

        # Calculate parameters once
        self._layout_params = LayoutParameters(
            container_width=container_width,
            container_height=container_height,
            sequence_count=len(self._sequences),
            margin=15,
            spacing=20,
            min_card_width=280,
            max_card_width=400,
        )

        logger.info(
            f"Layout parameters calculated: "
            f"{self._layout_params.column_count} columns, "
            f"cards {self._layout_params.card_width}x{self._layout_params.card_height}"
        )

    def _lock_layout_for_rendering(self):
        """Lock layout to prevent any changes during rendering."""
        self._layout_locked = True
        self._rendering_in_progress = True

        # Lock chunked loader if available
        if self._chunked_loader and hasattr(self._chunked_loader, "set_grid_reference"):
            self._chunked_loader.set_grid_reference(self)

        logger.debug("Layout locked for consistent rendering")

    def _unlock_layout_after_rendering(self):
        """Unlock layout after rendering is complete."""
        self._layout_locked = False
        self._rendering_in_progress = False

        logger.debug("Layout unlocked after rendering")

    def _clear_all_items(self):
        """Clear all existing items from grid."""
        # Clear visible items list
        for item in self._visible_items:
            item.setParent(None)
            item.deleteLater()
        self._visible_items.clear()

        # Clear grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

    def _render_all_items_consistently(self):
        """Render all items with guaranteed consistency."""
        if not self._item_creator or not self._sequences or not self._layout_params:
            return

        logger.info(f"Rendering {len(self._sequences)} items consistently")

        cards_for_chunked_loading = []

        # Create all cards with identical parameters
        for index, sequence in enumerate(self._sequences):
            # Create card with consistent sizing
            card = self._create_consistent_card(sequence, index)

            # Calculate grid position
            row, col = self._layout_params.get_position_for_index(index)

            # Add to grid layout at exact position
            self.grid_layout.addWidget(card, row, col)

            # Add to visible items
            self._visible_items.append(card)

            # Connect events
            self._connect_item_events_isolated(card, sequence, index)

            # Collect for chunked loading
            if hasattr(sequence, "thumbnails") and sequence.thumbnails:
                cards_for_chunked_loading.append((card, sequence.thumbnails[0]))

        # Set fixed content size
        total_width = (
            self._layout_params.column_count * self._layout_params.card_width
            + (self._layout_params.column_count - 1) * 20
        )
        self.content_widget.setFixedSize(total_width, self._layout_params.grid_height)

        # Start chunked loading if enabled
        if self._chunked_loader and cards_for_chunked_loading:
            logger.info(
                f"Starting chunked loading for {len(cards_for_chunked_loading)} cards"
            )
            if hasattr(self._chunked_loader, "queue_multiple_loads"):
                self._chunked_loader.queue_multiple_loads(cards_for_chunked_loading)

        logger.info(f"Consistent rendering complete: {len(self._visible_items)} items")

    def _create_consistent_card(self, sequence, index: int):
        """Create a card with guaranteed consistent sizing."""
        # Create card using the item creator
        card = self._item_creator(sequence, index)

        # Store index for tracking
        card._grid_index = index

        # Apply fixed sizing immediately and consistently
        card_size = self._layout_params.get_card_size()

        # Apply multiple size constraints for maximum stability
        if hasattr(card, "apply_fixed_size"):
            card.apply_fixed_size(card_size.width(), card_size.height())
        else:
            # Fallback sizing
            card.setFixedSize(card_size)
            card.setMinimumSize(card_size)
            card.setMaximumSize(card_size)
            card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Set chunked loading manager if available
        if self._chunked_loader and hasattr(card, "set_chunked_loading_manager"):
            card.set_chunked_loading_manager(self._chunked_loader)

        logger.debug(
            f"Created consistent card {index}: {card_size.width()}x{card_size.height()}"
        )

        return card

    def _connect_item_events_isolated(self, item, sequence, index):
        """Connect item events with proper isolation."""
        if hasattr(item, "clicked"):

            def handle_click(seq_id=sequence.id, idx=index):
                self.item_clicked.emit(seq_id, idx)

            item.clicked.connect(handle_click)

        if hasattr(item, "double_clicked"):

            def handle_double_click(seq_id=sequence.id, idx=index):
                self.item_double_clicked.emit(seq_id, idx)

            item.double_clicked.connect(handle_double_click)

    def _update_viewport(self):
        """Update the virtual scrolling viewport."""
        if not self._sequences or not self._layout_params:
            return

        # Calculate visible range
        scroll_value = self.scroll_area.verticalScrollBar().value()
        viewport_height = self.scroll_area.viewport().height()

        row_height = self._layout_params.card_height + 20  # Including spacing

        # Calculate visible row range
        start_row = max(0, scroll_value // row_height)
        end_row = min(
            self._layout_params.total_rows,
            (scroll_value + viewport_height) // row_height + 1,
        )

        # Convert to item indices
        self._viewport_start = int(start_row * self._layout_params.column_count)
        self._viewport_end = min(
            len(self._sequences), int(end_row * self._layout_params.column_count)
        )

        self.viewport_changed.emit(self._viewport_start, self._viewport_end)

    def _on_scroll(self, value: int):
        """Handle scroll events with throttling."""
        # Debounce viewport updates
        self._resize_timer.stop()
        self._resize_timer.start(50)

    def _handle_resize_finished(self):
        """Handle debounced resize/scroll events."""
        self._update_viewport()

    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize events with layout consistency protection."""
        super().resizeEvent(event)

        # Skip resize handling if layout is locked
        if self._layout_locked or self._rendering_in_progress:
            logger.debug("Resize event ignored - layout is locked")
            return

        old_size = event.oldSize()
        new_size = event.size()

        # Skip initial size establishment
        if not old_size.isValid() or old_size.width() <= 0:
            return

        # Check if this is a significant size change
        width_change = abs(new_size.width() - old_size.width())
        if width_change < 50:  # Ignore minor size changes
            return

        logger.info(
            f"Significant resize detected: "
            f"{old_size.width()}x{old_size.height()} -> "
            f"{new_size.width()}x{new_size.height()}"
        )

        # Recalculate layout if we have sequences
        if self._sequences:
            # Check if new layout would be significantly different
            new_params = LayoutParameters(
                container_width=new_size.width(),
                container_height=new_size.height(),
                sequence_count=len(self._sequences),
            )

            if not self._layout_params or not self._layout_params.is_consistent_with(
                new_params
            ):

                logger.info("Layout parameters changed significantly, re-rendering")

                # Trigger complete re-render with new parameters
                self.set_sequences(self._sequences)

    def set_item_creator(self, creator: Callable):
        """Set the callback function to create thumbnail items."""
        self._item_creator = creator

    def set_chunked_loading_enabled(self, enabled: bool):
        """Enable or disable chunked loading."""
        if enabled and not self._chunked_loader:
            # Import and create chunked loader
            try:
                from ..services.chunked_image_loader import ChunkedImageLoadingManager

                self._chunked_loader = ChunkedImageLoadingManager(
                    chunk_size=self.config.max_concurrent_image_loads or 6, parent=self
                )
                logger.info("Chunked loading enabled")
            except ImportError:
                logger.warning("Could not import ChunkedImageLoadingManager")
        elif not enabled:
            self._chunked_loader = None
            logger.info("Chunked loading disabled")

    def get_column_count(self) -> int:
        """Get current column count."""
        return self._layout_params.column_count if self._layout_params else 3

    def get_visible_range(self) -> tuple[int, int]:
        """Get current visible item range."""
        return self._viewport_start, self._viewport_end

    def scroll_to_item(self, index: int):
        """Scroll to make the specified item visible."""
        if index < 0 or index >= len(self._sequences) or not self._layout_params:
            return

        row, _ = self._layout_params.get_position_for_index(index)
        row_height = self._layout_params.card_height + 20
        target_position = row * row_height

        self.scroll_area.verticalScrollBar().setValue(target_position)

    def lock_layout_during_loading(self, locked: bool):
        """Lock or unlock layout changes during chunked loading."""
        if locked:
            self._layout_locked = True
            logger.debug("Layout locked for chunked loading")
        else:
            # Only unlock if we're not in the middle of rendering
            if not self._rendering_in_progress:
                self._layout_locked = False
                logger.debug("Layout unlocked after chunked loading")

    def is_layout_locked(self) -> bool:
        """Check if layout is currently locked."""
        return self._layout_locked or self._rendering_in_progress

    def get_fixed_card_size(self):
        """Get the current fixed card size."""
        return (
            self._layout_params.get_card_size()
            if self._layout_params
            else QSize(280, 320)
        )
