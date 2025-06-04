"""
Fast Thumbnail Card - Performance-Optimized Implementation with Modern Animations

This card implementation balances speed with modern UX:
1. Minimal widget hierarchy
2. Pre-scaled image loading
3. Optional modern animations (2025 trends)
4. Efficient memory usage
5. Fast creation/destruction
6. Glassmorphic hover effects
7. Micro-interactions and feedback

Performance targets:
- <5ms card creation time
- <2ms image loading (with cache)
- <1ms resize handling
- 60fps animations
- Minimal memory footprint
"""

import logging
import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QPixmap, QFont

# Import AnimationType for animations
try:
    from .animation_system import AnimationType
except ImportError:
    # Fallback if animation system not available
    class AnimationType:
        FADE_IN = "fade_in"
        SCALE_IN = "scale_in"


from .optimized_hover_manager import VirtualScrollIntegratedHoverMixin

logger = logging.getLogger(__name__)


class FastThumbnailCard(VirtualScrollIntegratedHoverMixin, QWidget):
    """
    Ultra-fast thumbnail card with minimal features.

    Features removed for performance:
    - Animations and hover effects
    - Complex styling and glassmorphism
    - Favorite buttons and metadata
    - Drop shadows and effects

    Features kept:
    - Basic image display
    - Title text
    - Click events
    - Fixed sizing
    """

    # Signals
    clicked = pyqtSignal(str)  # sequence_id
    double_clicked = pyqtSignal(str)  # sequence_id

    # Class-level image cache for performance
    _image_cache = {}  # path -> scaled_pixmap
    _cache_size_limit = 100  # Limit cache size

    def __init__(self, sequence, config=None, parent=None):
        super().__init__(parent)

        self.sequence = sequence
        self.config = config

        # Fixed dimensions for performance
        self._width = 280
        self._height = 320

        # State
        self._image_loaded = False
        self._is_hovered = False
        self._hover_animation_active = False  # Prevent duplicate hover animations
        self._animation_manager = None  # Will be set by parent if animations enabled

        self._setup_ui()
        self._load_image_fast()

        # Enable mouse events for hover animations
        self.setMouseTracking(True)  # Enable for modern hover effects

    def _setup_ui(self):
        """Setup minimal UI structure."""
        # Apply fixed size immediately
        self.setFixedSize(self._width, self._height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Simple vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Image label - takes most of the space
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(240)  # Fixed height for consistency
        self._setup_loading_state()
        self._setup_error_state()
        layout.addWidget(self.image_label)

        # Title label - minimal styling
        self.title_label = QLabel(self._truncate_text(self.sequence.name, 30))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(False)

        # Simple font
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)

        self.title_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                padding: 5px;
            }
        """
        )
        layout.addWidget(self.title_label)

        # PyQt6-compatible card styling (removed unsupported CSS properties)
        self.setStyleSheet(
            """
            FastThumbnailCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:0.5 rgba(255, 255, 255, 0.12),
                    stop:1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 20px;
            }
            FastThumbnailCard:hover,
            FastThumbnailCard[hovered="true"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15),
                    stop:0.5 rgba(255, 255, 255, 0.20),
                    stop:1 rgba(255, 255, 255, 0.15));
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
        """
        )

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text efficiently."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _setup_loading_state(self):
        """Setup modern glassmorphic loading state."""
        self._loading_style = """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.05),
                    stop:0.5 rgba(255, 255, 255, 0.12),
                    stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                font-weight: bold;
            }
        """

    def _setup_error_state(self):
        """Setup modern glassmorphic error state."""
        self._error_style = """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(244, 67, 54, 0.15),
                    stop:0.5 rgba(244, 67, 54, 0.25),
                    stop:1 rgba(244, 67, 54, 0.15));
                border: 2px solid rgba(244, 67, 54, 0.4);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-weight: bold;
            }
        """

    def _success_style(self):
        """Get success state style for loaded images."""
        return """
            QLabel {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """

    def _load_image_fast(self):
        """Load image with aggressive caching and modern loading states."""
        logger.info(
            f"🎯 FAST_CARD: _load_image_fast called for sequence '{self.sequence.name}'"
        )

        # Show loading state immediately
        self._show_loading_state()

        if not hasattr(self.sequence, "thumbnails") or not self.sequence.thumbnails:
            logger.warning(
                f"🎯 FAST_CARD: No thumbnails for sequence '{self.sequence.name}'"
            )
            self._show_error_state(
                "No Image Available", "This sequence has no thumbnail image."
            )
            return

        image_path = self.sequence.thumbnails[0]
        logger.info(f"🎯 FAST_CARD: Loading image from '{image_path}'")

        # Check cache first
        cache_key = f"{image_path}_{self._width-20}x{240-20}"  # Account for margins
        if cache_key in self._image_cache:
            logger.info(f"🎯 FAST_CARD: Cache hit for '{image_path}'")
            self._show_success_state()
            self.image_label.setPixmap(self._image_cache[cache_key])
            self._image_loaded = True
            return

        logger.info(f"🎯 FAST_CARD: Cache miss for '{image_path}', loading from disk")

        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"🎯 FAST_CARD: File not found - '{image_path}'")
            self._show_error_state(
                "File Missing", f"Image file not found:\n{os.path.basename(image_path)}"
            )
            return

        try:
            logger.info(f"🎯 FAST_CARD: Loading QPixmap from '{image_path}'")
            # Load and scale image
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                logger.error(f"🎯 FAST_CARD: QPixmap.isNull() for '{image_path}'")
                self._show_error_state(
                    "Invalid Image",
                    "The image file appears to be corrupted or in an unsupported format.",
                )
                return

            logger.info(f"🎯 FAST_CARD: Original pixmap loaded, size={pixmap.size()}")

            # Scale to exact display size with high quality
            target_size = QSize(self._width - 20, 220)  # Account for margins and title
            logger.info(f"🎯 FAST_CARD: Scaling to target size {target_size}")
            scaled_pixmap = pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,  # High quality scaling
            )

            logger.info(f"🎯 FAST_CARD: Scaled pixmap size={scaled_pixmap.size()}")

            # Cache the scaled image
            self._cache_image(cache_key, scaled_pixmap)

            # Show success state and set image
            self._show_success_state()
            self.image_label.setPixmap(scaled_pixmap)
            self._image_loaded = True
            logger.info(
                f"🎯 FAST_CARD: Successfully loaded and displayed '{image_path}'"
            )

        except Exception as e:
            logger.error(f"🎯 FAST_CARD: Exception loading '{image_path}': {e}")
            self._show_error_state(
                "Loading Error", f"Failed to load image:\n{str(e)[:50]}..."
            )

    def _cache_image(self, cache_key: str, pixmap: QPixmap):
        """Cache scaled image with size limit."""
        # Remove oldest entries if cache is full
        if len(self._image_cache) >= self._cache_size_limit:
            # Remove first 20 entries (FIFO)
            keys_to_remove = list(self._image_cache.keys())[:20]
            for key in keys_to_remove:
                del self._image_cache[key]

        self._image_cache[cache_key] = pixmap

    def mousePressEvent(self, event):
        """Handle mouse press with modern feedback animations."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Trigger micro bounce animation for click feedback
            if self._animation_manager:
                bounce_id = self._animation_manager.create_micro_bounce_animation(self)
                self._animation_manager.start_animation(bounce_id)

            self.clicked.emit(self.sequence.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click with elastic scale animation."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Trigger elastic scale animation for double-click feedback
            if self._animation_manager:
                scale_id = self._animation_manager.create_elastic_scale_animation(
                    self, scale_factor=1.05
                )
                self._animation_manager.start_animation(scale_id)

            self.double_clicked.emit(self.sequence.id)
        super().mouseDoubleClickEvent(event)

    def enterEvent(self, event):
        """Optimized hover enter - lightweight CSS-only animation for 60fps performance."""
        # PERFORMANCE FIX: Remove all animation conflicts and complex state tracking
        if not self._is_hovered:
            self._is_hovered = True

            # Use pure CSS hover animations only - no JavaScript/Python animations
            # This ensures 60fps performance and eliminates timing conflicts
            self.setProperty("hovered", True)
            self.style().polish(self)  # Force style update for immediate response

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Optimized hover leave - immediate CSS reset."""
        # PERFORMANCE FIX: Immediate state reset with CSS-only animations
        self._is_hovered = False

        # Reset CSS hover state immediately
        self.setProperty("hovered", False)
        self.style().polish(self)  # Force style update for immediate response

        super().leaveEvent(event)

    def resizeEvent(self, event):
        """Prevent resize events for performance."""
        # Only allow resize if it matches our fixed size
        new_size = event.size()
        if new_size.width() != self._width or new_size.height() != self._height:
            # Force back to fixed size
            self.setFixedSize(self._width, self._height)
            return

        super().resizeEvent(event)

    def sizeHint(self) -> QSize:
        """Provide fixed size hint."""
        return QSize(self._width, self._height)

    def minimumSizeHint(self) -> QSize:
        """Provide fixed minimum size hint."""
        return QSize(self._width, self._height)

    def get_sequence_id(self) -> str:
        """Get sequence ID."""
        return self.sequence.id

    def is_image_loaded(self) -> bool:
        """Check if image is loaded."""
        return self._image_loaded

    def set_animation_manager(self, animation_manager):
        """Set the animation manager for modern effects."""
        self._animation_manager = animation_manager

    def trigger_entrance_animation(self):
        """Trigger entrance animation when card becomes visible."""
        if self._animation_manager:
            # Create fade + scale entrance animation
            fade_id = self._animation_manager.create_fade_animation(
                self, AnimationType.FADE_IN, duration=300
            )
            scale_id = self._animation_manager.create_scale_animation(
                self, AnimationType.SCALE_IN, duration=300
            )

            # Start both animations (they'll run in parallel)
            self._animation_manager.start_animation(fade_id)
            self._animation_manager.start_animation(scale_id)

    def update_sequence_info(self, new_sequence):
        """Update the card with new sequence information when reused from widget pool."""
        # LOOP PREVENTION: Check if sequence is actually different
        if hasattr(self, "sequence") and self.sequence.id == new_sequence.id:
            # Same sequence, no update needed - prevents infinite loops
            return

        print(
            f"🔄 FastThumbnailCard.update_sequence_info: Updating from {self.sequence.id if hasattr(self, 'sequence') else 'None'} to {new_sequence.id}"
        )

        # Update sequence reference
        old_sequence_id = self.sequence.id if hasattr(self, "sequence") else "None"
        self.sequence = new_sequence

        # Update title label with new sequence name
        new_title = self._truncate_text(self.sequence.name, 30)
        self.title_label.setText(new_title)

        # Reset image loading state and reload image
        self._image_loaded = False
        self._load_image_fast()

        print(
            f"🔄 FastThumbnailCard.update_sequence_info: Updated title from sequence {old_sequence_id} to {new_sequence.id}: '{new_title}'"
        )

    def _show_loading_state(self):
        """Show modern glassmorphic loading state."""
        self.image_label.setStyleSheet(self._loading_style)
        self.image_label.setText("✨ Loading...")
        self.image_label.clear()  # Clear any existing pixmap

    def _show_error_state(self, title: str, message: str):
        """Show modern glassmorphic error state with retry option."""
        self.image_label.setStyleSheet(self._error_style)
        self.image_label.setText(f"❌ {title}\n\n{message}\n\n🔄 Click to retry")
        self.image_label.clear()  # Clear any existing pixmap
        self._image_loaded = False

    def _show_success_state(self):
        """Show success state styling for loaded images."""
        self.image_label.setStyleSheet(self._success_style())

    def _show_empty_state(self, message: str = "No sequences found"):
        """Show empty state when no content is available."""
        empty_style = """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(158, 158, 158, 0.1),
                    stop:0.5 rgba(158, 158, 158, 0.2),
                    stop:1 rgba(158, 158, 158, 0.1));
                border: 1px dashed rgba(158, 158, 158, 0.3);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 13px;
                font-style: italic;
            }
        """
        self.image_label.setStyleSheet(empty_style)
        self.image_label.setText(f"📭 {message}")
        self.image_label.clear()  # Clear any existing pixmap

    @classmethod
    def clear_image_cache(cls):
        """Clear the image cache to free memory."""
        cls._image_cache.clear()
        logger.info("Image cache cleared")

    @classmethod
    def get_cache_size(cls) -> int:
        """Get current cache size."""
        return len(cls._image_cache)


class PreloadedThumbnailCard(FastThumbnailCard):
    """
    Even faster card that expects pre-loaded images.

    This version assumes images are already scaled and cached
    by a background service, eliminating load time entirely.
    """

    def __init__(
        self, sequence, preloaded_pixmap: QPixmap = None, config=None, parent=None
    ):
        self.preloaded_pixmap = preloaded_pixmap
        super().__init__(sequence, config, parent)

    def _load_image_fast(self):
        """Use preloaded image if available."""
        if self.preloaded_pixmap and not self.preloaded_pixmap.isNull():
            self.image_label.setPixmap(self.preloaded_pixmap)
            self._image_loaded = True
        else:
            # Fallback to normal loading
            super()._load_image_fast()


class PlaceholderThumbnailCard(QWidget):
    """
    Ultra-minimal placeholder card for instant loading.

    Shows immediately while real cards load in background.
    """

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
        image_placeholder.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.5);
            }
        """
        )
        layout.addWidget(image_placeholder)

        # Title
        title_label = QLabel(
            sequence.name[:25] + "..." if len(sequence.name) > 25 else sequence.name
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                padding: 5px;
            }
        """
        )
        layout.addWidget(title_label)

        # Basic styling
        self.setStyleSheet(
            """
            PlaceholderThumbnailCard {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """
        )

    def get_sequence_id(self) -> str:
        """Get sequence ID."""
        return self.sequence.id
