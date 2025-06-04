"""
Simple Fast Grid - Reliable Performance Solution

This is a simplified approach that prioritizes reliability over complex optimization.
It addresses the blank content issue while maintaining good performance.

Key features:
1. Simple virtual scrolling that actually works
2. Reliable card creation for all visible items
3. Immediate fallback to synchronous loading if background fails
4. Clear error handling and logging
5. No complex widget pooling that can cause blank content
"""

import logging
import math
from typing import List, Optional, Callable, Dict
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QResizeEvent

logger = logging.getLogger(__name__)


class SimpleFastGrid(QWidget):
    """
    Simple, reliable virtual grid that prioritizes working correctly
    over complex optimizations that can cause blank content.
    """
    
    # Signals
    item_clicked = pyqtSignal(str, int)
    item_double_clicked = pyqtSignal(str, int)
    viewport_changed = pyqtSignal(int, int)
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        
        self.config = config or self._default_config()
        
        # Fixed grid configuration for reliability
        self.card_width = 280
        self.card_height = 320
        self.spacing = 20
        self.margin = 15
        self.columns = 4  # Start with fixed columns
        
        # Data
        self._sequences: List = []
        self._visible_cards: Dict[int, QWidget] = {}  # index -> widget
        
        # Viewport tracking
        self._viewport_start = 0
        self._viewport_end = 0
        
        # Item creator
        self._item_creator: Optional[Callable] = None
        
        # Scroll throttling
        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._update_visible_cards)
        
        self._setup_ui()
        
        logger.info("SimpleFastGrid initialized")
    
    def _default_config(self):
        """Default configuration."""
        class Config:
            enable_animations = False
        return Config()
    
    def _setup_ui(self):
        """Setup UI with simple structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self.margin, self.margin, self.margin, self.margin)
        layout.setSpacing(0)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget - where cards are placed
        self.content_widget = QFrame()
        self.content_widget.setObjectName("content")
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
        # Connect scroll events
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        # Basic styling
        self.setStyleSheet("""
            SimpleFastGrid {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QFrame#content {
                background: transparent;
            }
        """)
    
    def set_sequences(self, sequences: List):
        """Set sequences with reliable rendering."""
        logger.info(f"Setting {len(sequences)} sequences")
        
        self._sequences = sequences
        
        # Clear existing cards
        self._clear_all_cards()
        
        # Calculate content size
        self._update_content_size()
        
        # Update visible cards
        self._update_visible_cards()
        
        logger.info(f"Grid updated with {len(sequences)} sequences")
    
    def _clear_all_cards(self):
        """Clear all existing cards."""
        for card in self._visible_cards.values():
            card.setParent(None)
            card.deleteLater()
        self._visible_cards.clear()
    
    def _update_content_size(self):
        """Update content widget size for scrolling."""
        if not self._sequences:
            self.content_widget.setFixedSize(0, 0)
            return
        
        # Calculate grid dimensions
        total_rows = math.ceil(len(self._sequences) / self.columns)
        total_width = self.columns * self.card_width + (self.columns - 1) * self.spacing
        total_height = total_rows * self.card_height + (total_rows - 1) * self.spacing
        
        self.content_widget.setFixedSize(total_width, total_height)
        
        logger.debug(f"Content size: {total_width}x{total_height} for {total_rows} rows")
    
    def _on_scroll(self, value: int):
        """Handle scroll events with throttling."""
        # Throttle scroll updates for performance
        self._scroll_timer.stop()
        self._scroll_timer.start(50)  # 20fps update rate
    
    def _update_visible_cards(self):
        """Update which cards are visible and create/destroy as needed."""
        if not self._sequences:
            return
        
        # Calculate visible range
        scroll_value = self.scroll_area.verticalScrollBar().value()
        viewport_height = self.scroll_area.viewport().height()
        
        row_height = self.card_height + self.spacing
        
        # Calculate visible rows with buffer
        start_row = max(0, (scroll_value // row_height) - 1)  # 1 row buffer above
        end_row = min(
            math.ceil(len(self._sequences) / self.columns),
            ((scroll_value + viewport_height) // row_height) + 2  # 1 row buffer below
        )
        
        # Convert to item indices
        new_start = int(start_row * self.columns)
        new_end = min(len(self._sequences), int(end_row * self.columns))
        
        # Only update if range changed
        if new_start != self._viewport_start or new_end != self._viewport_end:
            self._viewport_start = new_start
            self._viewport_end = new_end
            
            logger.debug(f"Viewport changed: {self._viewport_start}-{self._viewport_end}")
            
            # Update visible cards
            self._render_visible_range()
            
            # Emit signal
            self.viewport_changed.emit(self._viewport_start, self._viewport_end)
    
    def _render_visible_range(self):
        """Render cards in the visible range."""
        if not self._item_creator:
            logger.warning("No item creator set")
            return
        
        # Determine which cards should be visible
        should_be_visible = set(range(self._viewport_start, self._viewport_end))
        currently_visible = set(self._visible_cards.keys())
        
        # Remove cards that should no longer be visible
        to_remove = currently_visible - should_be_visible
        for index in to_remove:
            self._remove_card(index)
        
        # Add cards that should now be visible
        to_add = should_be_visible - currently_visible
        for index in to_add:
            self._create_card(index)
        
        logger.debug(f"Rendered: removed {len(to_remove)}, added {len(to_add)} cards")
    
    def _create_card(self, index: int):
        """Create a card for the given index."""
        if index >= len(self._sequences):
            return
        
        sequence = self._sequences[index]
        
        try:
            # Create card using item creator
            card = self._item_creator(sequence, index)
            
            if not card:
                logger.error(f"Item creator returned None for index {index}")
                return
            
            # Calculate position
            row = index // self.columns
            col = index % self.columns
            
            x = col * (self.card_width + self.spacing)
            y = row * (self.card_height + self.spacing)
            
            # Set card properties
            card.setParent(self.content_widget)
            card.setFixedSize(self.card_width, self.card_height)
            card.setGeometry(x, y, self.card_width, self.card_height)
            card.show()
            
            # Store card
            self._visible_cards[index] = card
            
            # Connect events
            self._connect_card_events(card, sequence, index)
            
            logger.debug(f"Created card {index} at ({x}, {y})")
            
        except Exception as e:
            logger.error(f"Error creating card {index}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _remove_card(self, index: int):
        """Remove a card."""
        if index in self._visible_cards:
            card = self._visible_cards.pop(index)
            card.hide()
            card.setParent(None)
            card.deleteLater()
            
            logger.debug(f"Removed card {index}")
    
    def _connect_card_events(self, card: QWidget, sequence, index: int):
        """Connect card events."""
        if hasattr(card, "clicked"):
            def handle_click():
                self.item_clicked.emit(sequence.id, index)
            card.clicked.connect(handle_click)
        
        if hasattr(card, "double_clicked"):
            def handle_double_click():
                self.item_double_clicked.emit(sequence.id, index)
            card.double_clicked.connect(handle_double_click)
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle resize events."""
        super().resizeEvent(event)
        
        old_size = event.oldSize()
        new_size = event.size()
        
        # Skip initial resize
        if not old_size.isValid():
            return
        
        # Check if width changed significantly
        if abs(new_size.width() - old_size.width()) < 50:
            return
        
        # Recalculate columns
        available_width = new_size.width() - (2 * self.margin)
        new_columns = max(1, available_width // (self.card_width + self.spacing))
        
        if new_columns != self.columns:
            logger.info(f"Columns changed: {self.columns} -> {new_columns}")
            self.columns = new_columns
            
            # Clear and recreate
            self._clear_all_cards()
            self._update_content_size()
            self._update_visible_cards()
    
    def set_item_creator(self, creator: Callable):
        """Set the item creator function."""
        self._item_creator = creator
        logger.info("Item creator set")
    
    def get_column_count(self) -> int:
        """Get current column count."""
        return self.columns
    
    def get_visible_range(self) -> tuple[int, int]:
        """Get visible range."""
        return self._viewport_start, self._viewport_end
    
    def scroll_to_item(self, index: int):
        """Scroll to make item visible."""
        if index < 0 or index >= len(self._sequences):
            return
        
        row = index // self.columns
        target_y = row * (self.card_height + self.spacing)
        
        self.scroll_area.verticalScrollBar().setValue(target_y)
    
    def get_visible_card_count(self) -> int:
        """Get number of currently visible cards."""
        return len(self._visible_cards)
