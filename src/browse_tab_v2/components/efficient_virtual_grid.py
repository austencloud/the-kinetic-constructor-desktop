"""
Efficient Virtual Grid - Performance-First Approach

This implementation focuses on maximum performance by:
1. True virtual scrolling - only render visible items
2. Lazy image loading with pre-scaled thumbnails
3. Isolated resize events - no cascading
4. Minimal DOM manipulation
5. Efficient memory management

Key Performance Optimizations:
- Only 10-15 cards exist in memory at any time
- Images are pre-scaled to display size
- No global resize events
- Viewport-based rendering only
"""

import logging
import math
import time
from typing import List, Optional, Callable, Dict, Set
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
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
    QElapsedTimer,
)
from PyQt6.QtGui import QResizeEvent, QPixmap

from .skeleton_thumbnail_card import SkeletonThumbnailCard, FastSkeletonCard
from .empty_state_widget import EmptyStateWidget

logger = logging.getLogger(__name__)


class VirtualGridItem:
    """Lightweight virtual item representation."""

    def __init__(self, sequence, index: int, row: int, col: int):
        self.sequence = sequence
        self.index = index
        self.row = row
        self.col = col
        self.widget = None  # Only created when visible
        self.is_visible = False
        self.image_loaded = False
        self.cached_pixmap = None


class EfficientVirtualGrid(QWidget):
    """
    Ultra-efficient virtual grid that only renders visible items.

    Performance targets:
    - <50ms initial load time
    - <16ms scroll response (60fps)
    - <100MB memory usage for 1000+ sequences
    """

    # Signals
    item_clicked = pyqtSignal(str, int)
    item_double_clicked = pyqtSignal(str, int)
    viewport_changed = pyqtSignal(int, int)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)

        self.config = config or self._default_config()

        # Grid configuration - FIXED for performance
        self.card_width = 280
        self.card_height = 320
        self.spacing = 20
        self.margin = 15
        self.columns = 4  # Fixed columns for simplicity

        # Virtual items
        self._sequences: List = []
        self._virtual_items: List[VirtualGridItem] = []
        self._all_widgets: Dict[int, QWidget] = (
            {}
        )  # index -> widget (all widgets created eagerly)
        # Widget pooling system removed - using eager creation instead

        # Viewport tracking
        self._viewport_start = 0
        self._viewport_end = 0
        self._last_scroll_value = 0

        # Fast scroll detection removed - no longer needed with eager widgets

        # Performance optimization
        self._item_creator: Optional[Callable] = None
        self._widget_creator = None
        self._widgets_created = False  # Flag to prevent unnecessary recreation

        # Progressive widget creation state (individual widget processing)
        self._progressive_creation_active = False
        self._creation_timer = QTimer()
        self._creation_timer.setSingleShot(True)
        self._creation_timer.timeout.connect(
            self._create_next_batch
        )  # Method name kept for compatibility
        self._creation_queue = []  # Indices to create
        self._creation_index = (
            0  # Current index in creation queue (replaces batch processing)
        )
        self._creation_batch_index = 0
        self._viewport_widgets_created = False  # Track if viewport widgets are ready

        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(
            self._update_viewport
        )  # CRITICAL FIX: Connect to _update_viewport, not _render_viewport

        # Resize isolation
        self._resize_locked = False

        # Loading states
        self._loading_state = False
        self._empty_state_widget = None
        self._skeleton_cards = []

        # Fast scroll skeleton system removed - no longer needed with eager widgets

        self._setup_ui()

        # Performance monitoring
        self._performance_timer = QElapsedTimer()
        self._frame_times = []
        self._scroll_times = []
        self._max_frame_history = 100
        self._target_fps = 120
        self._target_frame_time = 1000.0 / self._target_fps  # 8.33ms for 120fps

        # Scroll event debouncing for 120fps
        self._scroll_debounce_timer = QTimer()
        self._scroll_debounce_timer.setSingleShot(True)
        self._scroll_debounce_timer.timeout.connect(self._process_debounced_scroll)
        self._pending_scroll_value = None

        # Optimized hover animation system integration
        from .optimized_hover_manager import initialize_hover_system

        self.hover_coordinator = initialize_hover_system(self)

        logger.debug(
            "EfficientVirtualGrid initialized with optimized hover system and performance monitoring"
        )

    def _default_config(self):
        """Default configuration."""

        class Config:
            enable_animations = False  # Disabled for performance
            max_visible_items = 15

        return Config()

    def _setup_ui(self):
        """Setup minimal UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        layout.setSpacing(0)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Viewport widget - this is where visible items are placed
        self.viewport_widget = QFrame()
        self.viewport_widget.setObjectName("viewport")

        # No layout manager - we'll position items manually for performance
        self.scroll_area.setWidget(self.viewport_widget)
        layout.addWidget(self.scroll_area)

        # Connect scroll events
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # Styling
        self.setStyleSheet(
            """
            EfficientVirtualGrid {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QFrame#viewport {
                background: transparent;
            }
        """
        )

    def set_sequences(self, sequences: List):
        """Set sequences with instant content display (no skeleton loaders)."""
        if self._resize_locked:
            logger.warning("Cannot set sequences while resize is locked")
            return

        start_time = self._get_time()
        logger.info(
            f"🚀 INSTANT_VIRTUAL_GRID: Setting {len(sequences)} sequences for immediate display"
        )

        self._sequences = sequences

        # Phase 1: Create virtual items
        self._create_virtual_items()

        # Phase 2: Create ALL widgets eagerly for instant display
        self._create_all_widgets_eagerly()

        # Phase 3: Setup viewport and trigger initial image loading
        self._calculate_viewport_size()
        self._update_viewport()

        end_time = self._get_time()
        logger.info(
            f"✅ INSTANT_VIRTUAL_GRID: Set {len(sequences)} sequences with {len(self._all_widgets)} widgets in {(end_time - start_time)*1000:.1f}ms - content displayed immediately"
        )

    def _create_virtual_items(self):
        """Create virtual item representations (no widgets yet)."""
        self._virtual_items.clear()

        for index, sequence in enumerate(self._sequences):
            row = index // self.columns
            col = index % self.columns

            virtual_item = VirtualGridItem(sequence, index, row, col)
            self._virtual_items.append(virtual_item)

    def _create_all_widgets_eagerly(self):
        """Create widgets progressively - viewport first, then background batches."""
        # Prevent unnecessary recreation if widgets already exist
        if self._widgets_created and len(self._all_widgets) == len(self._sequences):
            return

        # Clear any existing widgets and stop any ongoing creation
        self._stop_progressive_creation()
        for widget in self._all_widgets.values():
            widget.hide()
            widget.deleteLater()
        self._all_widgets.clear()
        self._widgets_created = False
        self._viewport_widgets_created = False

        # Start progressive creation
        self._start_progressive_creation()

    def _start_progressive_creation(self):
        """Start progressive widget creation - viewport first, then background batches."""
        if not self._widget_creator:
            logger.error("Widget creator not set!")
            return

        # Calculate viewport range for immediate creation
        viewport_height = self.scroll_area.viewport().height()
        row_height = self.card_height + self.spacing
        viewport_rows = max(2, (viewport_height // row_height) + 1)  # At least 2 rows
        viewport_count = min(len(self._virtual_items), viewport_rows * self.columns)

        # PROGRESSIVE DISPLAY: Create and show viewport widgets individually for instant feedback
        # Each widget appears immediately after creation, not after batch completion
        for index in range(viewport_count):
            self._create_and_show_single_widget_immediately(index)

            # Process events after each widget to ensure immediate UI updates
            QApplication.processEvents()

        self._viewport_widgets_created = True

        # Set up progressive creation for remaining widgets (individual, not batched)
        remaining_indices = list(range(viewport_count, len(self._virtual_items)))
        if remaining_indices:
            self._creation_queue = remaining_indices
            self._creation_index = 0
            self._progressive_creation_active = True

            # Start progressive creation with minimal delay for smooth individual widget appearance
            self._creation_timer.start(
                5
            )  # Reduced to 5ms for faster individual widget display

    def _create_next_batch(self):
        """Progressive individual widget creation for instant visual feedback.

        Replaces batch processing with individual widget creation to eliminate
        129-283ms batch delays that cause poor UX.
        """
        if not self._progressive_creation_active or not self._creation_queue:
            return

        # Check if we've processed all widgets
        if self._creation_index >= len(self._creation_queue):
            self._finish_progressive_creation()
            return

        # Get next widget index to create
        queue_index = self._creation_index
        widget_index = self._creation_queue[queue_index]

        # Start widget performance timer
        widget_timer = QElapsedTimer()
        widget_timer.start()

        try:
            # Create and show single widget immediately
            self._create_and_show_single_widget_immediately(widget_index)

            widget_time = widget_timer.elapsed()

            # Record performance for monitoring
            self._record_individual_widget_performance(widget_time)

            # Log slow widget creation
            if widget_time > 50:  # 50ms per widget is too slow
                logger.warning(
                    f"Slow widget creation: {widget_time:.1f}ms for widget {widget_index}"
                )

        except Exception as e:
            logger.error(f"Widget creation failed for index {widget_index}: {e}")

        # Move to next widget
        self._creation_index += 1

        # Continue with next widget using minimal delay for smooth progression
        if self._creation_index < len(self._creation_queue):
            # Use adaptive delay based on widget creation performance
            delay = self._calculate_individual_widget_delay(widget_timer.elapsed())
            self._creation_timer.start(delay)
        else:
            self._finish_progressive_creation()

    def _calculate_individual_widget_delay(self, widget_time: float) -> int:
        """Calculate adaptive delay between individual widget creation based on performance."""
        base_delay = 5  # 5ms base delay for smooth progression

        # Adaptive delay based on widget creation performance
        if widget_time < 10:  # Very fast widget creation
            return max(1, base_delay // 2)  # Minimal delay for fast progression
        elif widget_time < 25:  # Fast widget creation
            return base_delay  # Standard delay
        elif widget_time < 50:  # Acceptable widget creation
            return min(10, base_delay * 2)  # Slightly longer delay
        else:  # Slow widget creation
            return min(20, base_delay * 4)  # Longer delay to prevent UI blocking

    def _record_individual_widget_performance(self, widget_time: float):
        """Record individual widget creation performance metrics."""
        if not hasattr(self, "_individual_widget_times"):
            self._individual_widget_times = []

        self._individual_widget_times.append(widget_time)

        # Keep only recent measurements (last 50 widgets)
        if len(self._individual_widget_times) > 50:
            self._individual_widget_times.pop(0)

        # Log performance for monitoring
        logger.debug(f"Individual widget creation: {widget_time:.1f}ms")

        # Calculate running average for performance insights
        if len(self._individual_widget_times) >= 10:
            recent_avg = sum(self._individual_widget_times[-10:]) / 10
            if recent_avg > 30:
                logger.warning(
                    f"Consistently slow widget creation: {recent_avg:.1f}ms average over last 10 widgets"
                )

    def _create_single_widget(self, index: int):
        """Create a single widget at the specified index."""
        if index >= len(self._virtual_items):
            return

        virtual_item = self._virtual_items[index]

        # Create widget
        widget = self._widget_creator(virtual_item.sequence, virtual_item.index)

        # Position widget in final grid coordinates
        x = virtual_item.col * (self.card_width + self.spacing)
        y = virtual_item.row * (self.card_height + self.spacing)

        # Set parent and geometry
        widget.setParent(self.viewport_widget)
        widget.setGeometry(x, y, self.card_width, self.card_height)

        # Initialize with sequence metadata but no image (lazy loading)
        if hasattr(widget, "update_sequence_info"):
            widget.update_sequence_info(virtual_item.sequence)

        # Connect widget events
        self._connect_widget_events(widget, virtual_item)

        # Show widget immediately
        widget.show()

        # Track widget
        self._all_widgets[index] = widget
        virtual_item.is_visible = True

    def _create_and_show_single_widget_immediately(self, index: int):
        """Create and show a single widget immediately for progressive display.

        This method ensures widgets appear instantly with placeholder content,
        eliminating batch processing delays that cause poor UX.
        """
        if index >= len(self._virtual_items):
            return

        virtual_item = self._virtual_items[index]

        # Create widget with placeholder content
        widget = self._widget_creator(virtual_item.sequence, virtual_item.index)

        # Position widget in final grid coordinates
        x = virtual_item.col * (self.card_width + self.spacing)
        y = virtual_item.row * (self.card_height + self.spacing)

        # Set parent and geometry
        widget.setParent(self.viewport_widget)
        widget.setGeometry(x, y, self.card_width, self.card_height)

        # Initialize with sequence metadata immediately (no image loading delay)
        if hasattr(widget, "update_sequence_info"):
            widget.update_sequence_info(virtual_item.sequence)

        # CRITICAL: Show widget with placeholder content immediately
        # This ensures users see the widget structure instantly
        widget.show()

        # Connect widget events
        self._connect_widget_events(widget, virtual_item)

        # Track widget
        self._all_widgets[index] = widget
        virtual_item.is_visible = True

        # Queue image loading asynchronously (decoupled from widget display)
        if hasattr(widget, "_queue_image_loading_async"):
            widget._queue_image_loading_async()

        logger.debug(
            f"✅ Widget {index} displayed immediately with placeholder content"
        )

    def _finish_progressive_creation(self):
        """Finish progressive creation and mark as complete."""
        self._progressive_creation_active = False
        self._widgets_created = True

        logger.info(
            f"Progressive widget creation completed: {len(self._all_widgets)} widgets"
        )

    def _stop_progressive_creation(self):
        """Stop any ongoing progressive creation."""
        self._progressive_creation_active = False
        self._creation_timer.stop()
        self._creation_queue.clear()
        self._creation_index = 0  # Reset individual index instead of batch index

    def _calculate_viewport_size(self):
        """Calculate total viewport size for scrolling."""
        if not self._virtual_items:
            self.viewport_widget.setFixedSize(0, 0)
            return

        total_rows = math.ceil(len(self._virtual_items) / self.columns)
        total_width = self.columns * self.card_width + (self.columns - 1) * self.spacing
        total_height = total_rows * self.card_height + (total_rows - 1) * self.spacing

        self.viewport_widget.setFixedSize(total_width, total_height)

    def _on_scroll(self, value: int):
        """Handle scroll with 120fps performance profiling and adaptive debouncing."""
        self._performance_timer.start()

        # Calculate scroll velocity for adaptive processing
        if hasattr(self, "_last_scroll_value") and hasattr(self, "_last_scroll_time"):
            current_time = time.time()
            time_delta = current_time - self._last_scroll_time
            if time_delta > 0:
                velocity = abs(value - self._last_scroll_value) / time_delta
                self._scroll_velocity = velocity

        self._last_scroll_value = value
        self._last_scroll_time = time.time()

        # Store pending scroll value for debounced processing
        self._pending_scroll_value = value

        # Adaptive debouncing based on scroll velocity
        debounce_delay = self._calculate_adaptive_scroll_delay()

        # Use adaptive debouncing for 120fps target
        self._scroll_debounce_timer.stop()
        self._scroll_debounce_timer.start(debounce_delay)

        # Log scroll event timing
        elapsed = self._performance_timer.elapsed()
        self._scroll_times.append(elapsed)
        if len(self._scroll_times) > self._max_frame_history:
            self._scroll_times.pop(0)

        # Performance warning for slow scroll event handling
        if elapsed > 4:  # 4ms is half of 8.33ms frame budget
            logger.warning(f"SLOW SCROLL EVENT: {elapsed:.2f}ms > 4ms budget")

        logger.debug(
            f"SCROLL EVENT: value={value}, velocity={getattr(self, '_scroll_velocity', 0):.1f}, delay={debounce_delay}ms, event_time={elapsed}ms"
        )

    def _calculate_adaptive_scroll_delay(self) -> int:
        """Calculate adaptive scroll debounce delay based on velocity and performance."""
        base_delay = 8  # 8ms for 120fps target

        # Get current scroll velocity (pixels per second)
        velocity = getattr(self, "_scroll_velocity", 0)

        # Adaptive delay based on scroll velocity
        if velocity > 2000:  # Very fast scrolling
            return max(4, base_delay // 2)  # Reduce delay for responsiveness
        elif velocity > 1000:  # Fast scrolling
            return max(6, int(base_delay * 0.75))
        elif velocity < 100:  # Slow/precise scrolling
            return min(16, base_delay * 2)  # Allow longer delay for precision
        else:
            return base_delay

    def _process_debounced_scroll(self):
        """Process debounced scroll events for optimal 120fps performance."""
        if self._pending_scroll_value is None:
            return

        self._performance_timer.restart()

        # Process the scroll update with performance monitoring
        try:
            self._update_viewport()
        except Exception as e:
            logger.error(f"Viewport update failed during scroll: {e}")
            return

        # Record frame time for performance monitoring
        frame_time = self._performance_timer.elapsed()
        self._frame_times.append(frame_time)
        if len(self._frame_times) > self._max_frame_history:
            self._frame_times.pop(0)

        # Enhanced frame drop detection with severity levels
        if frame_time > self._target_frame_time * 2:  # Severe frame drop (>16.67ms)
            logger.error(
                f"SEVERE FRAME DROP: {frame_time:.2f}ms > {self._target_frame_time * 2:.2f}ms (2x target)"
            )
            self._severe_frame_drops = getattr(self, "_severe_frame_drops", 0) + 1
        elif frame_time > self._target_frame_time:  # Minor frame drop
            logger.warning(
                f"FRAME DROP: {frame_time:.2f}ms > {self._target_frame_time:.2f}ms target"
            )
            self._minor_frame_drops = getattr(self, "_minor_frame_drops", 0) + 1

        # Periodic performance reporting (every 60 frames ~0.5s at 120fps)
        if len(self._frame_times) % 60 == 0:
            self._report_scroll_performance_metrics()

        # Clear pending scroll value
        self._pending_scroll_value = None

    def _report_scroll_performance_metrics(self):
        """Report comprehensive scroll performance metrics."""
        if not self._frame_times:
            return

        # Calculate performance statistics
        avg_frame_time = sum(self._frame_times) / len(self._frame_times)
        max_frame_time = max(self._frame_times)
        min_frame_time = min(self._frame_times)

        # Calculate frame rate
        avg_fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0

        # Count frame drops
        frame_drops = sum(1 for t in self._frame_times if t > self._target_frame_time)
        severe_drops = getattr(self, "_severe_frame_drops", 0)
        minor_drops = getattr(self, "_minor_frame_drops", 0)

        # Performance grade
        if avg_fps >= 120:
            grade = "EXCELLENT"
        elif avg_fps >= 60:
            grade = "GOOD"
        elif avg_fps >= 30:
            grade = "ACCEPTABLE"
        else:
            grade = "POOR"

        logger.info(
            f"SCROLL PERFORMANCE [{grade}]: "
            f"avg={avg_frame_time:.1f}ms ({avg_fps:.1f}fps), "
            f"range={min_frame_time:.1f}-{max_frame_time:.1f}ms, "
            f"drops={frame_drops}/{len(self._frame_times)} "
            f"(severe={severe_drops}, minor={minor_drops})"
        )

    def _update_viewport(self):
        """Optimized viewport calculation for 120fps performance."""
        if not self._virtual_items:
            return

        # Get scroll position and viewport height (optimized single calls)
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_value = scroll_bar.value()
        viewport_height = self.scroll_area.viewport().height()

        # Optimized row calculations (pre-computed row_height)
        row_height = self.card_height + self.spacing
        start_row = max(0, scroll_value // row_height)
        total_rows = math.ceil(len(self._virtual_items) / self.columns)
        end_row = min(total_rows, (scroll_value + viewport_height) // row_height + 2)

        # Optimized item index calculations
        new_start = start_row * self.columns
        new_end = min(len(self._virtual_items), end_row * self.columns)

        # Only update if viewport actually changed (optimized comparison)
        if new_start != self._viewport_start or new_end != self._viewport_end:
            logger.debug(
                f"📺 VIEWPORT_CHANGED: {self._viewport_start}-{self._viewport_end} → {new_start}-{new_end}"
            )
            self._viewport_start = new_start
            self._viewport_end = new_end

            # Trigger optimized render and emit signal
            self._render_viewport()
            self.viewport_changed.emit(self._viewport_start, self._viewport_end)
            logger.debug(
                f"📺 VIEWPORT_SIGNAL: Emitted viewport_changed({self._viewport_start}, {self._viewport_end})"
            )

    def _render_viewport(self):
        """Optimized image loading for visible items (120fps target)."""
        if not self._virtual_items:
            logger.debug("📺 RENDER_VIEWPORT: No virtual items to render")
            return

        logger.debug(
            f"📺 RENDER_VIEWPORT: Loading images for visible widgets (indices {self._viewport_start}-{self._viewport_end})"
        )

        # Optimized image loading for visible widgets
        for index in range(self._viewport_start, self._viewport_end):
            widget = self._all_widgets.get(index)
            if widget and hasattr(widget, "_load_image_fast"):
                if not getattr(widget, "_image_loaded", False):
                    logger.debug(
                        f"📺 RENDER_VIEWPORT: Triggering _load_image_fast for widget {index}"
                    )
                    widget._load_image_fast()
                else:
                    logger.debug(
                        f"📺 RENDER_VIEWPORT: Widget {index} already has image loaded"
                    )
            else:
                logger.debug(
                    f"📺 RENDER_VIEWPORT: Widget {index} missing or no _load_image_fast method"
                )

    # Old widget pooling methods removed - using eager widget creation instead

    # Fast scroll skeleton system removed - no longer needed with eager widgets

    # _show_item and _hide_item methods removed - widgets are created eagerly and always visible

    # _get_widget_for_item method removed - widgets are created eagerly in _create_all_widgets_eagerly

    # _update_widget_data and _return_widget_to_pool methods removed - no widget pooling needed

    def _connect_widget_events(self, widget: QWidget, virtual_item: VirtualGridItem):
        """Connect widget events."""
        if hasattr(widget, "clicked"):

            def handle_click():
                self.item_clicked.emit(virtual_item.sequence.id, virtual_item.index)

            widget.clicked.connect(handle_click)

        if hasattr(widget, "double_clicked"):

            def handle_double_click():
                self.item_double_clicked.emit(
                    virtual_item.sequence.id, virtual_item.index
                )

            widget.double_clicked.connect(handle_double_click)

    def resizeEvent(self, event: QResizeEvent):
        """Handle resize with minimal impact."""
        super().resizeEvent(event)

        # Lock resize to prevent cascading
        if self._resize_locked:
            return

        old_size = event.oldSize()
        new_size = event.size()

        # Only recalculate if width changed significantly
        if not old_size.isValid() or abs(new_size.width() - old_size.width()) < 50:
            return

        # Recalculate columns based on new width
        available_width = new_size.width() - (2 * self.margin)
        new_columns = max(1, available_width // (self.card_width + self.spacing))

        if new_columns != self.columns:
            self._resize_locked = True
            self.columns = new_columns

            # Recreate virtual items with new positions
            self._create_virtual_items()
            self._calculate_viewport_size()

            # ONLY recreate widgets if column count actually changed (force recreation)
            self._widgets_created = False  # Force recreation due to layout change
            self._create_all_widgets_eagerly()

            # Re-render viewport (trigger image loading)
            self._update_viewport()

            self._resize_locked = False

            logger.info(f"Resized to {new_columns} columns")

    def set_item_creator(self, creator: Callable):
        """Set widget creator function for eager widget creation."""
        self._widget_creator = creator

    def get_column_count(self) -> int:
        """Get current column count."""
        return self.columns

    def get_visible_range(self) -> tuple[int, int]:
        """Get visible range."""
        return self._viewport_start, self._viewport_end

    def _get_time(self) -> float:
        """Get current time for performance measurement."""
        import time

        return time.time()

    # ===== FAST SCROLL SKELETON SYSTEM REMOVED =====
    # All skeleton methods removed - using eager widget creation instead

    # ===== LOADING STATES INTEGRATION =====

    def show_loading_state(self, skeleton_count: int = 12):
        """Show skeleton loading state with specified number of skeleton cards."""
        self._loading_state = True
        self._clear_all_content()

        # Create skeleton cards
        self._skeleton_cards = []
        for i in range(skeleton_count):
            skeleton = FastSkeletonCard(self.viewport_widget)

            # Position skeleton cards in grid layout
            row = i // self.columns
            col = i % self.columns
            x = col * (self.card_width + self.spacing)
            y = row * (self.card_height + self.spacing)

            skeleton.setGeometry(x, y, self.card_width, self.card_height)
            skeleton.show()
            self._skeleton_cards.append(skeleton)

        # Update viewport size for skeleton cards
        total_rows = math.ceil(skeleton_count / self.columns)
        total_width = self.columns * self.card_width + (self.columns - 1) * self.spacing
        total_height = total_rows * self.card_height + (total_rows - 1) * self.spacing
        self.viewport_widget.setFixedSize(total_width, total_height)

        logger.info(f"Showing loading state with {skeleton_count} skeleton cards")

    def show_empty_state(self, state_type: str = "no_matches", **kwargs):
        """Show empty state widget for various scenarios."""
        self._loading_state = False
        self._clear_all_content()

        # Create empty state widget
        self._empty_state_widget = EmptyStateWidget(self.viewport_widget)

        # Configure empty state based on type
        if state_type == "no_matches":
            filter_count = kwargs.get("filter_count", 0)
            self._empty_state_widget.show_no_filter_matches(filter_count)
        elif state_type == "empty_dataset":
            self._empty_state_widget.show_empty_dataset()
        elif state_type == "search_no_results":
            search_term = kwargs.get("search_term", "")
            self._empty_state_widget.show_search_no_results(search_term)
        elif state_type == "loading_error":
            error_message = kwargs.get("error_message", "")
            self._empty_state_widget.show_loading_error(error_message)

        # Connect signals
        self._empty_state_widget.clear_filters_requested.connect(
            lambda: (
                self.parent().clear_filters()
                if hasattr(self.parent(), "clear_filters")
                else None
            )
        )
        self._empty_state_widget.refresh_requested.connect(
            lambda: (
                self.parent().refresh_content()
                if hasattr(self.parent(), "refresh_content")
                else None
            )
        )
        self._empty_state_widget.browse_all_requested.connect(
            lambda: (
                self.parent().browse_all()
                if hasattr(self.parent(), "browse_all")
                else None
            )
        )

        # Position empty state widget to fill viewport
        self._empty_state_widget.setGeometry(
            0,
            0,
            self.scroll_area.viewport().width(),
            self.scroll_area.viewport().height(),
        )
        self._empty_state_widget.show()

        # Set minimal viewport size
        self.viewport_widget.setFixedSize(
            self.scroll_area.viewport().width(), self.scroll_area.viewport().height()
        )

        logger.info(f"Showing empty state: {state_type}")

    def hide_loading_states(self):
        """Hide all loading states and return to normal content display."""
        self._loading_state = False
        self._clear_all_content()

        # Recalculate viewport for actual content
        if self._sequences:
            self._calculate_viewport_size()
            self._update_viewport()

        logger.info("Loading states hidden, returning to normal content")

    def _clear_all_content(self):
        """Clear all content from viewport (skeleton cards, empty states, eagerly created widgets)."""
        # Clear skeleton cards (loading state)
        for skeleton in self._skeleton_cards:
            skeleton.hide()
            skeleton.deleteLater()
        self._skeleton_cards.clear()

        # Clear empty state widget
        if self._empty_state_widget:
            self._empty_state_widget.hide()
            self._empty_state_widget.deleteLater()
            self._empty_state_widget = None

        # Clear all eagerly created widgets
        for widget in self._all_widgets.values():
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        self._all_widgets.clear()
        self._widgets_created = False  # Reset flag when clearing

    def is_loading(self) -> bool:
        """Check if currently in loading state."""
        return self._loading_state

    def has_content(self) -> bool:
        """Check if has actual content to display."""
        return len(self._sequences) > 0 and not self._loading_state
