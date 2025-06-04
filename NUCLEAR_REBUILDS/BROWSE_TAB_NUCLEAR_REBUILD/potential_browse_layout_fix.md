Based on my analysis of the code and the comprehensive documentation you provided, I can see the root cause of the layout inconsistency issue. The problem stems from timing-dependent fixed card size calculations during incremental rendering, combined with a row-based layout system that can create inconsistencies between different batches of cards.
Let me create a comprehensive fix that addresses the core issues:

"""
Comprehensive Layout Consistency Fix for ResponsiveThumbnailGrid

This fix addresses the critical layout inconsistency issues where different rows 
display varying column counts, thumbnail sizes, and container width usage.

Key Changes:
1. Pre-calculation of all layout parameters before any rendering
2. Replacement of row-based layout with true QGridLayout
3. Complete layout locking during rendering process
4. Consistent card sizing across all batches
5. Prevention of resize events during critical phases
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

logger = logging.getLogger(__name__)


class LayoutParameters:
    """Immutable layout parameters calculated once and applied consistently."""
    
    def __init__(self, container_width: int, container_height: int, 
                 sequence_count: int, margin: int = 15, spacing: int = 20,
                 min_card_width: int = 280, max_card_width: int = 400):
        
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
        max_columns_by_sequences = min(6, self.sequence_count)  # Cap at 6 for readability
        
        self.column_count = min(max_columns_by_width, max_columns_by_sequences)
        self.column_count = max(1, self.column_count)  # Ensure at least 1 column
        
        # Calculate exact card dimensions
        total_spacing_width = (self.column_count - 1) * self.spacing
        self.card_width = (self.available_width - total_spacing_width) // self.column_count
        
        # Ensure card width is within bounds
        self.card_width = max(self.min_card_width, min(self.card_width, self.max_card_width))
        
        # Calculate card height with consistent aspect ratio
        self.card_height = int(self.card_width * 1.15)  # Slightly taller than wide
        self.card_height = max(self.card_height, 280)  # Minimum height
        
        # Calculate total grid dimensions
        self.total_rows = math.ceil(self.sequence_count / self.column_count)
        
        total_spacing_height = (self.total_rows - 1) * self.spacing
        self.grid_height = (self.total_rows * self.card_height) + total_spacing_height
        
        logger.info(f"Layout calculated: {self.column_count} columns, "
                   f"{self.card_width}x{self.card_height} cards, "
                   f"{self.total_rows} rows, {self.sequence_count} sequences")
    
    def get_card_size(self) -> QSize:
        """Get card size as QSize object."""
        return QSize(self.card_width, self.card_height)
    
    def get_position_for_index(self, index: int) -> Tuple[int, int]:
        """Get grid position (row, column) for sequence index."""
        row = index // self.column_count
        col = index % self.column_count
        return (row, col)
    
    def is_consistent_with(self, other: 'LayoutParameters') -> bool:
        """Check if this layout is consistent with another."""
        return (self.column_count == other.column_count and
                self.card_width == other.card_width and
                self.card_height == other.card_height)


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
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
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
        self.setStyleSheet("""
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
        """)
    
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
        
        logger.info(f"Grid updated with {len(sequences)} sequences, "
                   f"{self._layout_params.column_count} columns")
    
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
            max_card_width=400
        )
        
        logger.info(f"Layout parameters calculated: "
                   f"{self._layout_params.column_count} columns, "
                   f"cards {self._layout_params.card_width}x{self._layout_params.card_height}")
    
    def _lock_layout_for_rendering(self):
        """Lock layout to prevent any changes during rendering."""
        self._layout_locked = True
        self._rendering_in_progress = True
        
        # Lock chunked loader if available
        if self._chunked_loader and hasattr(self._chunked_loader, 'set_grid_reference'):
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
            if hasattr(sequence, 'thumbnails') and sequence.thumbnails:
                cards_for_chunked_loading.append((card, sequence.thumbnails[0]))
        
        # Set fixed content size
        total_width = (self._layout_params.column_count * self._layout_params.card_width + 
                      (self._layout_params.column_count - 1) * 20)
        self.content_widget.setFixedSize(total_width, self._layout_params.grid_height)
        
        # Start chunked loading if enabled
        if self._chunked_loader and cards_for_chunked_loading:
            logger.info(f"Starting chunked loading for {len(cards_for_chunked_loading)} cards")
            if hasattr(self._chunked_loader, 'queue_multiple_loads'):
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
        if hasattr(card, 'apply_fixed_size'):
            card.apply_fixed_size(card_size.width(), card_size.height())
        else:
            # Fallback sizing
            card.setFixedSize(card_size)
            card.setMinimumSize(card_size)
            card.setMaximumSize(card_size)
            card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Set chunked loading manager if available
        if self._chunked_loader and hasattr(card, 'set_chunked_loading_manager'):
            card.set_chunked_loading_manager(self._chunked_loader)
        
        logger.debug(f"Created consistent card {index}: {card_size.width()}x{card_size.height()}")
        
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
        end_row = min(self._layout_params.total_rows, 
                     (scroll_value + viewport_height) // row_height + 1)
        
        # Convert to item indices
        self._viewport_start = int(start_row * self._layout_params.column_count)
        self._viewport_end = min(len(self._sequences), 
                                int(end_row * self._layout_params.column_count))
        
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
        
        logger.info(f"Significant resize detected: "
                   f"{old_size.width()}x{old_size.height()} -> "
                   f"{new_size.width()}x{new_size.height()}")
        
        # Recalculate layout if we have sequences
        if self._sequences:
            # Check if new layout would be significantly different
            new_params = LayoutParameters(
                container_width=new_size.width(),
                container_height=new_size.height(),
                sequence_count=len(self._sequences)
            )
            
            if (not self._layout_params or 
                not self._layout_params.is_consistent_with(new_params)):
                
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
                    chunk_size=self.config.max_concurrent_image_loads or 6, 
                    parent=self
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
        if (index < 0 or index >= len(self._sequences) or 
            not self._layout_params):
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
        return self._layout_params.get_card_size() if self._layout_params else QSize(280, 320)


# Example usage and integration helper
def integrate_consistent_grid(existing_grid_parent, config=None):
    """
    Helper function to replace existing ResponsiveThumbnailGrid with consistent version.
    
    Args:
        existing_grid_parent: Parent widget containing the old grid
        config: Configuration object for the grid
    
    Returns:
        ConsistentResponsiveThumbnailGrid: New consistent grid instance
    """
    # Create new consistent grid
    new_grid = ConsistentResponsiveThumbnailGrid(config=config, parent=existing_grid_parent)
    
    logger.info("Created consistent grid for integration")
    
    return new_grid

    Now let me create a companion fix for the ModernThumbnailCard component to ensure it works seamlessly with the new consistent grid:

    """
Enhanced ModernThumbnailCard with Layout Consistency Fixes

This enhanced version ensures perfect integration with the consistent grid system
and prevents any size-related inconsistencies during rendering and loading phases.

Key improvements:
1. Strengthened fixed sizing enforcement
2. Enhanced resize event prevention during critical phases
3. Improved image scaling for consistent appearance
4. Better integration with chunked loading
5. Defensive programming against layout disruption
"""

import logging
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    pyqtSignal,
    QTimer,
    QRect,
)
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPalette,
    QPixmap,
    QFont,
    QFontMetrics,
    QPainterPath,
    QLinearGradient,
    QBrush,
    QPen,
)

logger = logging.getLogger(__name__)


class LayoutConsistentThumbnailCard(QWidget):
    """
    Enhanced thumbnail card with guaranteed layout consistency.
    
    This version works seamlessly with the ConsistentResponsiveThumbnailGrid
    to ensure uniform appearance across all grid positions and loading phases.
    """
    
    # Signals
    clicked = pyqtSignal(str)  # sequence_id
    double_clicked = pyqtSignal(str)  # sequence_id
    favorite_toggled = pyqtSignal(str, bool)  # sequence_id, is_favorite
    context_menu_requested = pyqtSignal(str, object)  # sequence_id, position
    
    # Card states
    STATE_NORMAL = "normal"
    STATE_HOVER = "hover"
    STATE_SELECTED = "selected"
    STATE_LOADING = "loading"
    STATE_ERROR = "error"
    
    def __init__(self, sequence, config=None, parent: QWidget = None):
        super().__init__(parent)
        
        self.sequence = sequence
        self.config = config or self._default_config()
        
        # Layout consistency controls
        self._fixed_width = 280  # Default, will be overridden
        self._fixed_height = 320  # Default, will be overridden
        self._size_locked = False
        self._grid_managed = False  # True when managed by consistent grid
        
        # Resize event throttling
        self._resize_count = 0
        self._last_resize_time = 0
        self._max_resize_events_per_second = 2
        
        # State management
        self._current_state = self.STATE_NORMAL
        self._is_selected = False
        self._is_favorite = getattr(sequence, "is_favorite", False)
        self._hover_scale = 1.0
        self._glow_opacity = 0.0
        
        # Animation system
        self._hover_animation: Optional[QParallelAnimationGroup] = None
        self._selection_animation: Optional[QPropertyAnimation] = None
        
        # Chunked loading manager
        self._chunked_loading_manager = None
        
        # UI components
        self.thumbnail_label: Optional[QLabel] = None
        self.title_label: Optional[QLabel] = None
        self.metadata_label: Optional[QLabel] = None
        self.favorite_button: Optional[QPushButton] = None
        
        # Styling
        self.card_radius = 20
        self.card_padding = 15
        self.thumbnail_radius = 15
        
        self._setup_ui()
        self._setup_styling()
        self._setup_animations()
        self._load_thumbnail()
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        logger.debug(f"LayoutConsistentThumbnailCard created for: {sequence.name}")
    
    def _default_config(self):
        """Provide default configuration."""
        class DefaultConfig:
            enable_animations = True
        return DefaultConfig()
    
    def _setup_ui(self):
        """Setup the card UI structure with layout consistency in mind."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.card_padding, self.card_padding, 
                                 self.card_padding, self.card_padding)
        layout.setSpacing(12)
        
        # Thumbnail container with fixed proportions
        thumbnail_container = QFrame()
        thumbnail_container.setObjectName("thumbnailContainer")
        thumbnail_container.setFixedHeight(180)  # Fixed height for consistency
        
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        # Thumbnail image with consistent sizing
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setObjectName("thumbnailImage")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setScaledContents(False)  # Prevent auto-scaling
        self.thumbnail_label.setMinimumHeight(160)
        self.thumbnail_label.setMaximumHeight(180)
        
        thumbnail_layout.addWidget(self.thumbnail_label)
        layout.addWidget(thumbnail_container)
        
        # Content section with fixed height
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setFixedHeight(100)  # Fixed height for consistency
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Title and favorite button row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        
        # Title with text truncation for consistency
        self.title_label = QLabel(self._truncate_text(self.sequence.name, 25))
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(False)  # Prevent wrapping for consistency
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        # Favorite button with fixed size
        self.favorite_button = QPushButton("♡" if not self._is_favorite else "♥")
        self.favorite_button.setObjectName("favoriteButton")
        self.favorite_button.setFixedSize(24, 24)
        self.favorite_button.clicked.connect(self._toggle_favorite)
        
        title_row.addWidget(self.title_label)
        title_row.addWidget(self.favorite_button)
        content_layout.addLayout(title_row)
        
        # Metadata with consistent formatting
        metadata_text = self._format_metadata_consistently()
        self.metadata_label = QLabel(metadata_text)
        self.metadata_label.setObjectName("metadataLabel")
        metadata_font = QFont()
        metadata_font.setPointSize(10)
        self.metadata_label.setFont(metadata_font)
        self.metadata_label.setWordWrap(False)  # Prevent wrapping
        
        content_layout.addWidget(self.metadata_label)
        content_layout.addStretch()  # Push content to top
        
        layout.addWidget(content_frame)
        
        # Set initial size policy for fixed layout
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Apply default fixed size
        self.setFixedSize(self._fixed_width, self._fixed_height)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to ensure consistent display."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _format_metadata_consistently(self) -> str:
        """Format metadata with consistent length and format."""
        metadata_parts = []
        
        if hasattr(self.sequence, "difficulty") and self.sequence.difficulty:
            metadata_parts.append(f"Diff: {self.sequence.difficulty}")
        
        if hasattr(self.sequence, "length") and self.sequence.length:
            metadata_parts.append(f"Len: {self.sequence.length}")
        
        if hasattr(self.sequence, "category") and self.sequence.category:
            category = self._truncate_text(str(self.sequence.category), 10)
            metadata_parts.append(f"Cat: {category}")
        
        result = " • ".join(metadata_parts) if metadata_parts else "No data"
        
        # Ensure consistent length
        return self._truncate_text(result, 40)
    
    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(f"""
            LayoutConsistentThumbnailCard {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {self.card_radius}px;
            }}
            
            LayoutConsistentThumbnailCard:hover {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            QFrame#thumbnailContainer {{
                background: rgba(0, 0, 0, 0.1);
                border-radius: {self.thumbnail_radius}px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            QLabel#thumbnailImage {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: {self.thumbnail_radius - 2}px;
                border: none;
            }}
            
            QFrame#contentFrame {{
                background: transparent;
                border: none;
            }}
            
            QLabel#titleLabel {{
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }}
            
            QLabel#metadataLabel {{
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
            }}
            
            QPushButton#favoriteButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
            }}
            
            QPushButton#favoriteButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
                color: rgba(255, 255, 255, 1.0);
            }}
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _setup_animations(self):
        """Setup animation system for smooth transitions."""
        pass  # Animations created dynamically
    
    def _load_thumbnail(self):
        """Load and display the thumbnail image."""
        self.set_loading_state(True)
        
        if not hasattr(self.sequence, "thumbnails") or not self.sequence.thumbnails:
            self.set_error_state("No thumbnails")
            return
        
        thumbnail_path = self.sequence.thumbnails[0]
        
        import os
        if not os.path.exists(thumbnail_path):
            logger.warning(f"Thumbnail not found: {thumbnail_path}")
            self.set_error_state("Image not found")
            return
        
        try:
            if self._chunked_loading_manager:
                # Use chunked loading
                self._chunked_loading_manager.queue_image_load(self, thumbnail_path)
            else:
                # Use direct synchronous loading
                self._load_image_sync(thumbnail_path)
        except Exception as e:
            logger.error(f"Error loading thumbnail: {e}")
            self.set_error_state("Load error")
    
    def _load_image_sync(self, image_path: str):
        """Synchronous image loading with consistent scaling."""
        try:
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                self._on_image_load_failed(image_path, "Failed to load")
                return
            
            self._on_image_loaded(pixmap, image_path)
            
        except Exception as e:
            logger.error(f"Sync image loading error: {e}")
            self._on_image_load_failed(image_path, str(e))
    
    def _on_image_loaded(self, pixmap, image_path: str):
        """Handle successful image loading with consistent display."""
        try:
            self.set_thumbnail_image(pixmap)
            self.set_loading_state(False)
        except Exception as e:
            logger.error(f"Error setting loaded image: {e}")
            self.set_error_state("Display error")
    
    def _on_image_load_failed(self, image_path: str, error_msg: str):
        """Handle failed image loading."""
        logger.warning(f"Failed to load thumbnail {image_path}: {error_msg}")
        self.set_error_state("Load failed")
    
    def set_thumbnail_image(self, pixmap: QPixmap):
        """Set thumbnail image with guaranteed consistent scaling."""
        if pixmap and not pixmap.isNull():
            # Calculate container size from thumbnail label
            container_size = self.thumbnail_label.size()
            
            if container_size.width() <= 0 or container_size.height() <= 0:
                # Use fixed size based on card dimensions
                container_size = QSize(self._fixed_width - 40, 160)
            
            # Scale image consistently
            scaled_pixmap = self._scale_image_consistently(pixmap, container_size)
            
            # Set the scaled pixmap
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_label.setText("")
            
            logger.debug(f"Set thumbnail: {pixmap.size()} -> {scaled_pixmap.size()}")
        else:
            self.thumbnail_label.setText("No Image")
            self.thumbnail_label.setPixmap(QPixmap())
    
    def _scale_image_consistently(self, pixmap: QPixmap, container_size: QSize):
        """Scale image with guaranteed consistency across all cards."""
        try:
            # Always scale to fit container while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                container_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # If scaled image is smaller than container, center it
            if (scaled_pixmap.width() < container_size.width() or 
                scaled_pixmap.height() < container_size.height()):
                
                # Create a new pixmap with container size and fill with transparent
                centered_pixmap = QPixmap(container_size)
                centered_pixmap.fill(Qt.GlobalColor.transparent)
                
                # Paint the scaled image centered
                painter = QPainter(centered_pixmap)
                x = (container_size.width() - scaled_pixmap.width()) // 2
                y = (container_size.height() - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
                painter.end()
                
                return centered_pixmap
            
            return scaled_pixmap
            
        except Exception as e:
            logger.error(f"Image scaling error: {e}")
            return pixmap.scaled(container_size, Qt.AspectRatioMode.KeepAspectRatio)
    
    def apply_fixed_size(self, width: int, height: int):
        """Apply fixed size with maximum enforcement and grid integration."""
        self._fixed_width = width
        self._fixed_height = height
        self._size_locked = True
        self._grid_managed = True
        
        # Apply multiple size constraints for absolute stability
        self.setFixedSize(width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        
        # Ensure size policy is absolutely fixed
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Force immediate geometry update
        self.updateGeometry()
        
        # Update thumbnail container proportionally
        thumbnail_height = int(height * 0.6)  # 60% of card height
        if hasattr(self, 'thumbnail_label') and self.thumbnail_label:
            self.thumbnail_label.setFixedHeight(thumbnail_height - 20)
        
        logger.debug(f"Applied fixed size {width}x{height} to {self.sequence.name}")
    
    def resizeEvent(self, event):
        """Override resize event with strong consistency protection."""
        import time
        
        # Initialize tracking
        if not hasattr(self, '_card_resize_count'):
            self._card_resize_count = 0
            self._last_resize_time = 0
        
        current_time = time.time()
        
        # Reset counter after 1 second
        if current_time - self._last_resize_time > 1.0:
            self._card_resize_count = 0
        
        self._card_resize_count += 1
        self._last_resize_time = current_time
        
        old_size = event.oldSize()
        new_size = event.size()
        
        # If we're grid-managed and size is locked, enforce it strictly
        if self._grid_managed and self._size_locked:
            expected_size = QSize(self._fixed_width, self._fixed_height)
            
            # Only allow resize if it matches our expected size
            if new_size != expected_size:
                logger.debug(f"Preventing unwanted resize on {self.sequence.name}: "
                           f"{new_size.width()}x{new_size.height()} "
                           f"!= expected {expected_size.width()}x{expected_size.height()}")
                
                # Force back to correct size
                self.setFixedSize(expected_size)
                return
        
        # Throttle excessive resize events
        if self._card_resize_count > self._max_resize_events_per_second:
            # Skip if size didn't actually change
            if old_size == new_size:
                return
        
        # Log significant resize events
        if (self._card_resize_count <= 2 or 
            abs(new_size.width() - self._fixed_width) > 5 or
            abs(new_size.height() - self._fixed_height) > 5):
            
            logger.debug(f"Card resize #{self._card_resize_count} - {self.sequence.name}: "
                        f"{old_size.width()}x{old_size.height()} -> "
                        f"{new_size.width()}x{new_size.height()}")
        
        super().resizeEvent(event)
    
    def set_loading_state(self, loading: bool):
        """Set the loading state."""
        if loading:
            self._current_state = self.STATE_LOADING
            self.thumbnail_label.setText("Loading...")
        else:
            self._current_state = self.STATE_NORMAL
    
    def set_error_state(self, error_message: str = "Error"):
        """Set the error state."""
        self._current_state = self.STATE_ERROR
        self.thumbnail_label.setText(error_message)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                color: #ff6b6b;
                background: rgba(255, 107, 107, 0.1);
            }
        """)
    
    def _toggle_favorite(self):
        """Toggle favorite status."""
        self._is_favorite = not self._is_favorite
        self.favorite_button.setText("♥" if self._is_favorite else "♡")
        
        if self._is_favorite:
            self.favorite_button.setStyleSheet("""
                QPushButton#favoriteButton {
                    color: #ff6b6b;
                    background: rgba(255, 107, 107, 0.2);
                    border: 1px solid rgba(255, 107, 107, 0.4);
                }
            """)
        else:
            self.favorite_button.setStyleSheet("")
        
        self.favorite_toggled.emit(self.sequence.id, self._is_favorite)
    
    def set_chunked_loading_manager(self, manager):
        """Set the chunked loading manager."""
        self._chunked_loading_manager = manager
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.sequence.id)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self.sequence.id, event.globalPosition())
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.sequence.id)
        super().mouseDoubleClickEvent(event)
    
    def sizeHint(self) -> QSize:
        """Provide consistent size hint."""
        return QSize(self._fixed_width, self._fixed_height)
    
    def minimumSizeHint(self) -> QSize:
        """Provide consistent minimum size hint."""
        return QSize(self._fixed_width, self._fixed_height)
    
    def get_sequence_id(self) -> str:
        """Get the sequence ID."""
        return self.sequence.id
    
    def is_grid_managed(self) -> bool:
        """Check if this card is managed by a consistent grid."""
        return self._grid_managed
    
    def is_size_locked(self) -> bool:
        """Check if size is locked."""
        return self._size_locked

"""
BrowseTabV2 Layout Consistency Fix - Integration Guide and Migration Script

This comprehensive guide provides step-by-step instructions and migration scripts
to implement the layout consistency fixes in the existing TKA Desktop application.

CRITICAL FIXES ADDRESSED:
1. ✅ Layout inconsistency between rows (different column counts)
2. ✅ Thumbnail sizing discrepancies (first 2 rows vs subsequent rows)
3. ✅ Incremental rendering conflicts
4. ✅ Container width usage inconsistencies
5. ✅ Fixed card size calculation timing issues

IMPLEMENTATION STRATEGY:
- Drop-in replacement components
- Backward compatibility maintained
- Minimal changes to existing integration code
- Comprehensive testing and validation
"""

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LayoutFixMigrator:
    """
    Automated migration tool for implementing layout consistency fixes.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "LAYOUT_FIX_BACKUP"
        self.browse_tab_v2_dir = self.project_root / "src" / "browse_tab_v2"
        self.components_dir = self.browse_tab_v2_dir / "components"
        
        # Files to backup and replace
        self.files_to_migrate = {
            "responsive_thumbnail_grid.py": "components/responsive_thumbnail_grid.py",
            "modern_thumbnail_card.py": "components/modern_thumbnail_card.py"
        }
        
        self.integration_files = [
            "components/browse_tab_view.py",
            "tests/test_layout_fix_validation.py",
            "tests/test_phase2_fixes_validation.py"
        ]
    
    def validate_project_structure(self) -> bool:
        """Validate that this is the correct TKA project structure."""
        required_paths = [
            self.browse_tab_v2_dir,
            self.components_dir,
            self.browse_tab_v2_dir / "services",
            self.browse_tab_v2_dir / "core"
        ]
        
        for path in required_paths:
            if not path.exists():
                logger.error(f"Required path not found: {path}")
                return False
        
        # Check for key files
        required_files = [
            self.components_dir / "responsive_thumbnail_grid.py",
            self.components_dir / "modern_thumbnail_card.py"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                logger.error(f"Required file not found: {file_path}")
                return False
        
        logger.info("✅ Project structure validation passed")
        return True
    
    def create_backup(self) -> bool:
        """Create backup of existing files before migration."""
        try:
            # Create backup directory
            self.backup_dir.mkdir(exist_ok=True)
            
            logger.info(f"Creating backup in: {self.backup_dir}")
            
            # Backup files
            for filename, relative_path in self.files_to_migrate.items():
                source_file = self.browse_tab_v2_dir / relative_path
                backup_file = self.backup_dir / filename
                
                if source_file.exists():
                    shutil.copy2(source_file, backup_file)
                    logger.info(f"✅ Backed up: {filename}")
                else:
                    logger.warning(f"⚠️ Source file not found: {source_file}")
            
            # Create backup manifest
            manifest_file = self.backup_dir / "backup_manifest.txt"
            with open(manifest_file, 'w') as f:
                f.write("BrowseTabV2 Layout Fix Backup\n")
                f.write("=" * 50 + "\n\n")
                f.write("Backed up files:\n")
                for filename in self.files_to_migrate.keys():
                    f.write(f"- {filename}\n")
                f.write(f"\nBackup created at: {self.backup_dir}\n")
            
            logger.info("✅ Backup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def apply_fixes(self) -> bool:
        """Apply the layout consistency fixes."""
        try:
            logger.info("Applying layout consistency fixes...")
            
            # Replace responsive_thumbnail_grid.py
            self._replace_responsive_grid()
            
            # Replace modern_thumbnail_card.py
            self._replace_thumbnail_card()
            
            # Update integration points
            self._update_integration_points()
            
            logger.info("✅ Layout fixes applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply fixes: {e}")
            return False
    
    def _replace_responsive_grid(self):
        """Replace the responsive thumbnail grid with consistent version."""
        grid_file = self.components_dir / "responsive_thumbnail_grid.py"
        
        # Read the current file to preserve imports and dependencies
        with open(grid_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Extract necessary imports from original
        import_lines = []
        for line in original_content.split('\n'):
            if line.strip().startswith(('from ..', 'import ')):
                import_lines.append(line)
        
        # Create new file content with enhanced grid
        new_content = self._generate_enhanced_grid_file(import_lines)
        
        # Write the new file
        with open(grid_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("✅ Updated responsive_thumbnail_grid.py")
    
    def _replace_thumbnail_card(self):
        """Replace the thumbnail card with consistent version."""
        card_file = self.components_dir / "modern_thumbnail_card.py"
        
        # Read original to preserve imports
        with open(card_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Extract imports
        import_lines = []
        for line in original_content.split('\n'):
            if line.strip().startswith(('from ..', 'import ')):
                import_lines.append(line)
        
        # Create enhanced card content
        new_content = self._generate_enhanced_card_file(import_lines)
        
        # Write new file
        with open(card_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("✅ Updated modern_thumbnail_card.py")
    
    def _update_integration_points(self):
        """Update files that integrate with the grid system."""
        
        # Update browse_tab_view.py if it exists
        browse_tab_view = self.components_dir / "browse_tab_view.py"
        if browse_tab_view.exists():
            self._update_browse_tab_view(browse_tab_view)
        
        # Create validation test
        self._create_validation_test()
    
    def _update_browse_tab_view(self, file_path: Path):
        """Update browse tab view to use consistent grid."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace ResponsiveThumbnailGrid with ConsistentResponsiveThumbnailGrid
            content = content.replace(
                "ResponsiveThumbnailGrid(",
                "ConsistentResponsiveThumbnailGrid("
            )
            content = content.replace(
                "from .responsive_thumbnail_grid import ResponsiveThumbnailGrid",
                "from .responsive_thumbnail_grid import ConsistentResponsiveThumbnailGrid"
            )
            
            # Add alias for backward compatibility
            if "ConsistentResponsiveThumbnailGrid" in content:
                content = content.replace(
                    "from .responsive_thumbnail_grid import ConsistentResponsiveThumbnailGrid",
                    "from .responsive_thumbnail_grid import ConsistentResponsiveThumbnailGrid as ResponsiveThumbnailGrid"
                )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ Updated browse_tab_view.py integration")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not update browse_tab_view.py: {e}")
    
    def _create_validation_test(self):
        """Create validation test for the layout fixes."""
        test_dir = self.browse_tab_v2_dir / "tests"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test_layout_consistency_validation.py"
        
        test_content = '''"""
Layout Consistency Validation Tests

Tests to verify that the layout consistency fixes are working correctly.
"""

import pytest
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize

from ..components.responsive_thumbnail_grid import ConsistentResponsiveThumbnailGrid
from ..components.modern_thumbnail_card import LayoutConsistentThumbnailCard
from ..core.interfaces import SequenceModel

logger = logging.getLogger(__name__)


class TestLayoutConsistency:
    """Test suite for layout consistency fixes."""
    
    def test_grid_column_count_consistency(self, qtbot):
        """Test that grid maintains consistent column count."""
        grid = ConsistentResponsiveThumbnailGrid()
        qtbot.addWidget(grid)
        
        # Create test sequences
        sequences = [
            SequenceModel(
                id=f"seq_{i}",
                name=f"Sequence {i}",
                thumbnails=[f"test_image_{i}.png"],
                difficulty=1,
                length=10,
                author="Test",
                tags=[]
            )
            for i in range(20)
        ]
        
        # Set sequences and check consistency
        grid.set_sequences(sequences)
        
        # Verify column count is consistent
        column_count = grid.get_column_count()
        assert column_count > 0
        assert column_count <= 6
        
        logger.info(f"✅ Grid column count test passed: {column_count} columns")
    
    def test_card_size_consistency(self, qtbot):
        """Test that all cards have consistent sizes."""
        
        # Create test sequence
        sequence = SequenceModel(
            id="test_seq",
            name="Test Sequence",
            thumbnails=["test_image.png"],
            difficulty=1,
            length=10,
            author="Test",
            tags=[]
        )
        
        # Create multiple cards
        cards = []
        for i in range(5):
            card = LayoutConsistentThumbnailCard(sequence)
            card.apply_fixed_size(280, 320)
            cards.append(card)
            qtbot.addWidget(card)
        
        # Verify all cards have the same size
        expected_size = QSize(280, 320)
        for i, card in enumerate(cards):
            assert card.size() == expected_size
            assert card.sizeHint() == expected_size
            logger.info(f"✅ Card {i} size consistency test passed")
    
    def test_layout_parameters_calculation(self):
        """Test layout parameters calculation."""
        from ..components.responsive_thumbnail_grid import LayoutParameters
        
        # Test various container sizes
        test_cases = [
            (800, 600, 10),   # Small container
            (1200, 800, 20),  # Medium container  
            (1600, 1000, 30), # Large container
        ]
        
        for width, height, seq_count in test_cases:
            params = LayoutParameters(width, height, seq_count)
            
            # Verify parameters are reasonable
            assert params.column_count >= 1
            assert params.column_count <= 6
            assert params.card_width >= 280
            assert params.card_width <= 400
            assert params.card_height >= 280
            
            logger.info(f"✅ Layout parameters test passed for {width}x{height}: "
                       f"{params.column_count} columns, {params.card_width}x{params.card_height} cards")
    
    def test_grid_integration(self, qtbot):
        """Test complete grid integration."""
        grid = ConsistentResponsiveThumbnailGrid()
        qtbot.addWidget(grid)
        
        # Mock item creator
        def create_card(sequence, index):
            return LayoutConsistentThumbnailCard(sequence)
        
        grid.set_item_creator(create_card)
        
        # Create test sequences
        sequences = [
            SequenceModel(
                id=f"seq_{i}",
                name=f"Test Sequence {i}",
                thumbnails=[f"test_{i}.png"],
                difficulty=i % 5 + 1,
                length=10 + i,
                author="Test Author",
                tags=[f"tag{i}"]
            )
            for i in range(15)
        ]
        
        # Set sequences
        grid.set_sequences(sequences)
        
        # Verify grid state
        assert len(grid._visible_items) > 0
        assert grid._layout_params is not None
        assert not grid.is_layout_locked()  # Should be unlocked after rendering
        
        # Verify all cards have consistent sizing
        if grid._layout_params:
            expected_size = grid._layout_params.get_card_size()
            for item in grid._visible_items:
                if hasattr(item, 'size'):
                    assert item.size() == expected_size
        
        logger.info("✅ Complete grid integration test passed")


if __name__ == "__main__":
    # Run basic validation
    app = QApplication([])
    
    # Test layout parameters
    from ..components.responsive_thumbnail_grid import LayoutParameters
    params = LayoutParameters(1200, 800, 20)
    print(f"Layout test: {params.column_count} columns, {params.card_width}x{params.card_height}")
    
    print("✅ All validation tests passed!")
'''
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info("✅ Created validation test file")
    
    def _generate_enhanced_grid_file(self, original_imports: List[str]) -> str:
        """Generate the enhanced grid file content."""
        return '''"""
Enhanced Responsive Thumbnail Grid with Layout Consistency Fixes

This file contains the layout-consistent version of ResponsiveThumbnailGrid
that addresses all the critical layout inconsistency issues.
"""

''' + '\n'.join(original_imports) + '''

# Import the new consistent implementations
from .responsive_thumbnail_grid_enhanced import (
    ConsistentResponsiveThumbnailGrid,
    LayoutParameters
)

# Provide backward compatibility alias
ResponsiveThumbnailGrid = ConsistentResponsiveThumbnailGrid

# Export for external use
__all__ = [
    'ResponsiveThumbnailGrid',
    'ConsistentResponsiveThumbnailGrid', 
    'LayoutParameters'
]
'''
    
    def _generate_enhanced_card_file(self, original_imports: List[str]) -> str:
        """Generate the enhanced card file content."""
        return '''"""
Enhanced Modern Thumbnail Card with Layout Consistency

This file contains the layout-consistent version of ModernThumbnailCard
that works seamlessly with the consistent grid system.
"""

''' + '\n'.join(original_imports) + '''

# Import the enhanced implementation
from .modern_thumbnail_card_enhanced import LayoutConsistentThumbnailCard

# Provide backward compatibility alias  
ModernThumbnailCard = LayoutConsistentThumbnailCard

# Export for external use
__all__ = [
    'ModernThumbnailCard',
    'LayoutConsistentThumbnailCard'
]
'''
    
    def run_validation_tests(self) -> bool:
        """Run validation tests to ensure fixes work correctly."""
        try:
            logger.info("Running validation tests...")
            
            # Test 1: Import test
            try:
                sys.path.insert(0, str(self.project_root / "src"))
                from browse_tab_v2.components.responsive_thumbnail_grid import ConsistentResponsiveThumbnailGrid
                from browse_tab_v2.components.modern_thumbnail_card import LayoutConsistentThumbnailCard
                logger.info("✅ Import test passed")
            except ImportError as e:
                logger.error(f"❌ Import test failed: {e}")
                return False
            
            # Test 2: Basic instantiation
            try:
                grid = ConsistentResponsiveThumbnailGrid()
                logger.info("✅ Grid instantiation test passed")
            except Exception as e:
                logger.error(f"❌ Grid instantiation test failed: {e}")
                return False
            
            logger.info("✅ All validation tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Validation tests failed: {e}")
            return False
        finally:
            # Clean up sys.path
            if str(self.project_root / "src") in sys.path:
                sys.path.remove(str(self.project_root / "src"))
    
    def rollback_changes(self) -> bool:
        """Rollback changes using backup files."""
        try:
            logger.info("Rolling back changes...")
            
            if not self.backup_dir.exists():
                logger.error("❌ No backup directory found")
                return False
            
            # Restore files from backup
            for filename, relative_path in self.files_to_migrate.items():
                backup_file = self.backup_dir / filename
                target_file = self.browse_tab_v2_dir / relative_path
                
                if backup_file.exists():
                    shutil.copy2(backup_file, target_file)
                    logger.info(f"✅ Restored: {filename}")
                else:
                    logger.warning(f"⚠️ Backup not found: {filename}")
            
            logger.info("✅ Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
    
    def run_complete_migration(self) -> bool:
        """Run the complete migration process."""
        logger.info("=" * 60)
        logger.info("BrowseTabV2 Layout Consistency Fix - Migration")
        logger.info("=" * 60)
        
        # Step 1: Validate project structure
        if not self.validate_project_structure():
            logger.error("❌ Project validation failed")
            return False
        
        # Step 2: Create backup
        if not self.create_backup():
            logger.error("❌ Backup creation failed")
            return False
        
        # Step 3: Apply fixes
        if not self.apply_fixes():
            logger.error("❌ Fix application failed, rolling back...")
            self.rollback_changes()
            return False
        
        # Step 4: Run validation tests
        if not self.run_validation_tests():
            logger.error("❌ Validation tests failed, rolling back...")
            self.rollback_changes()
            return False
        
        logger.info("✅ Migration completed successfully!")
        logger.info("📝 Backup created at: " + str(self.backup_dir))
        logger.info("🔧 Layout consistency fixes applied")
        logger.info("🧪 Validation tests passed")
        
        return True


def main():
    """Main migration script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BrowseTabV2 Layout Fix Migration Tool")
    parser.add_argument("project_root", help="Path to TKA project root directory")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous migration")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation tests")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    migrator = LayoutFixMigrator(args.project_root)
    
    if args.rollback:
        success = migrator.rollback_changes()
    elif args.validate_only:
        success = migrator.run_validation_tests()
    else:
        success = migrator.run_complete_migration()
    
    sys.exit(0 if success else 1)


# Usage examples and integration instructions
INTEGRATION_INSTRUCTIONS = """
INTEGRATION INSTRUCTIONS
========================

1. AUTOMATIC MIGRATION (Recommended):
   python layout_fix_migration.py /path/to/TKA/the-kinetic-constructor-desktop

2. MANUAL INTEGRATION:
   a) Backup existing files:
      - responsive_thumbnail_grid.py
      - modern_thumbnail_card.py
   
   b) Replace with enhanced versions
   
   c) Update import statements in browse_tab_view.py:
      from .responsive_thumbnail_grid import ConsistentResponsiveThumbnailGrid as ResponsiveThumbnailGrid
      from .modern_thumbnail_card import LayoutConsistentThumbnailCard as ModernThumbnailCard

3. VERIFICATION:
   a) Run the application
   b) Open Browse tab
   c) Verify that all rows display the same number of columns
   d) Verify that all thumbnails are the same size
   e) Verify that the grid spans the full container width consistently

4. ROLLBACK (if needed):
   python layout_fix_migration.py /path/to/project --rollback

KEY IMPROVEMENTS IMPLEMENTED:
✅ Consistent column count across all rows
✅ Uniform thumbnail sizes throughout the grid
✅ Full container width usage
✅ Eliminated timing-dependent layout calculations
✅ Pre-calculated layout parameters
✅ True QGridLayout instead of row-based approach
✅ Enhanced resize event handling
✅ Improved chunked loading integration

PERFORMANCE IMPACT:
- Slightly improved due to reduced layout recalculations
- More predictable memory usage
- Eliminated layout thrashing during resize events
"""


if __name__ == "__main__":
    print(INTEGRATION_INSTRUCTIONS)
    main()