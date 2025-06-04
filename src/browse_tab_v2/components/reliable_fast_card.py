"""
Reliable Fast Card - Simple and Working

This card prioritizes reliability over complex optimizations.
It loads images synchronously but efficiently, ensuring content always appears.

Key features:
1. Synchronous image loading that always works
2. Simple caching without background threads
3. Immediate content display - no blank cards
4. Clear error handling
5. Minimal complexity
"""

import logging
import os
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    pyqtSignal,
)
from PyQt6.QtGui import QPixmap, QFont

logger = logging.getLogger(__name__)


class ReliableFastCard(QWidget):
    """
    Reliable thumbnail card that always shows content.
    
    This version prioritizes reliability over complex optimizations.
    Images load synchronously but with efficient caching.
    """
    
    # Signals
    clicked = pyqtSignal(str)  # sequence_id
    double_clicked = pyqtSignal(str)  # sequence_id
    
    # Simple class-level cache
    _image_cache: Dict[str, QPixmap] = {}
    _max_cache_size = 100
    
    def __init__(self, sequence, config=None, parent=None):
        super().__init__(parent)
        
        self.sequence = sequence
        self.config = config
        
        # Fixed size for consistency
        self._width = 280
        self._height = 320
        
        self._setup_ui()
        self._load_content()
        
        logger.debug(f"Created ReliableFastCard for {sequence.name}")
    
    def _setup_ui(self):
        """Setup simple UI structure."""
        # Apply fixed size
        self.setFixedSize(self._width, self._height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Simple layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Image area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(240)
        self.image_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.7);
            }
        """)
        layout.addWidget(self.image_label)
        
        # Title
        self.title_label = QLabel(self._get_display_name())
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(False)
        
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        
        self.title_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                padding: 5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Card styling
        self.setStyleSheet("""
            ReliableFastCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
            ReliableFastCard:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
        """)
    
    def _get_display_name(self) -> str:
        """Get display name with truncation."""
        name = getattr(self.sequence, 'name', 'Unknown')
        if len(name) > 25:
            return name[:22] + "..."
        return name
    
    def _load_content(self):
        """Load card content reliably."""
        # Always show title immediately
        self.title_label.setText(self._get_display_name())
        
        # Load image
        self._load_image_sync()
    
    def _load_image_sync(self):
        """Load image synchronously with caching."""
        # Check if sequence has thumbnails
        if not hasattr(self.sequence, "thumbnails") or not self.sequence.thumbnails:
            self.image_label.setText("No Image")
            return
        
        image_path = self.sequence.thumbnails[0]
        
        # Check cache first
        if image_path in self._image_cache:
            self.image_label.setPixmap(self._image_cache[image_path])
            return
        
        # Check if file exists
        if not os.path.exists(image_path):
            self.image_label.setText("Missing")
            logger.debug(f"Image not found: {image_path}")
            return
        
        try:
            # Load image
            original_pixmap = QPixmap(image_path)
            
            if original_pixmap.isNull():
                self.image_label.setText("Error")
                logger.warning(f"Failed to load image: {image_path}")
                return
            
            # Scale to fit
            target_size = QSize(self._width - 20, 220)
            scaled_pixmap = original_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Cache the scaled image
            self._cache_image(image_path, scaled_pixmap)
            
            # Display image
            self.image_label.setPixmap(scaled_pixmap)
            
            logger.debug(f"Loaded image: {os.path.basename(image_path)}")
            
        except Exception as e:
            self.image_label.setText("Error")
            logger.error(f"Error loading image {image_path}: {e}")
    
    def _cache_image(self, path: str, pixmap: QPixmap):
        """Cache image with simple size management."""
        # Remove oldest entries if cache is full
        if len(self._image_cache) >= self._max_cache_size:
            # Remove first 20 entries
            keys_to_remove = list(self._image_cache.keys())[:20]
            for key in keys_to_remove:
                del self._image_cache[key]
        
        self._image_cache[path] = pixmap
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.sequence.id)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.sequence.id)
        super().mouseDoubleClickEvent(event)
    
    def get_sequence_id(self) -> str:
        """Get sequence ID."""
        return self.sequence.id
    
    @classmethod
    def clear_cache(cls):
        """Clear image cache."""
        cls._image_cache.clear()
        logger.info("Image cache cleared")
    
    @classmethod
    def get_cache_size(cls) -> int:
        """Get cache size."""
        return len(cls._image_cache)


class PlaceholderCard(QWidget):
    """Simple placeholder card for immediate display."""
    
    def __init__(self, sequence, parent=None):
        super().__init__(parent)
        
        self.sequence = sequence
        
        # Fixed size
        self.setFixedSize(280, 320)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Simple layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder image
        image_placeholder = QLabel("Loading...")
        image_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_placeholder.setFixedHeight(240)
        image_placeholder.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.5);
                font-size: 14px;
            }
        """)
        layout.addWidget(image_placeholder)
        
        # Title
        name = getattr(sequence, 'name', 'Unknown')
        if len(name) > 25:
            name = name[:22] + "..."
        
        title_label = QLabel(name)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # Basic styling
        self.setStyleSheet("""
            PlaceholderCard {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
    
    def get_sequence_id(self) -> str:
        """Get sequence ID."""
        return self.sequence.id


class DebugCard(QWidget):
    """Debug card that shows detailed information."""
    
    def __init__(self, sequence, index: int, parent=None):
        super().__init__(parent)
        
        self.sequence = sequence
        self.index = index
        
        # Fixed size
        self.setFixedSize(280, 320)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Debug info
        debug_info = QLabel(f"Index: {index}\nID: {sequence.id}\nName: {sequence.name}")
        debug_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        debug_info.setWordWrap(True)
        debug_info.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.9);
                padding: 10px;
                font-family: monospace;
            }
        """)
        layout.addWidget(debug_info)
        
        # Card styling
        self.setStyleSheet("""
            DebugCard {
                background: rgba(255, 100, 100, 0.2);
                border: 2px solid rgba(255, 100, 100, 0.5);
                border-radius: 12px;
            }
        """)
    
    def get_sequence_id(self) -> str:
        """Get sequence ID."""
        return self.sequence.id
