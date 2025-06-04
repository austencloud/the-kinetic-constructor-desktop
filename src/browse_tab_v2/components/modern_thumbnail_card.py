"""
Modern Thumbnail Card Component - Phase 2 Week 3 Day 18-19

Modern thumbnail card with glassmorphism effects, hover animations, and state management.
Implements 2025 design system with smooth transitions and accessibility support.

Features:
- Glassmorphism background with backdrop blur
- Smooth hover animations (scale, glow, shadow)
- Modern typography and spacing
- State management (loading, error, selected)
- Accessibility support
- Performance optimized rendering
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

from ..core.state import SequenceModel
from ..core.interfaces import BrowseTabConfig
from .optimized_hover_manager import VirtualScrollIntegratedHoverMixin

logger = logging.getLogger(__name__)


class ModernThumbnailCard(VirtualScrollIntegratedHoverMixin, QWidget):
    """
    Modern thumbnail card implementing 2025 design system.

    Features:
    - Glassmorphic background with subtle transparency
    - Smooth hover animations with scale and glow effects
    - Modern typography with proper hierarchy
    - State indicators (loading, error, selected)
    - Accessibility support with keyboard navigation
    - Performance optimized with cached rendering
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

    def __init__(
        self,
        sequence: SequenceModel,
        config: BrowseTabConfig = None,
        parent: QWidget = None,
    ):
        super().__init__(parent)

        self.sequence = sequence
        self.config = config or BrowseTabConfig()

        # State management
        self._current_state = self.STATE_NORMAL
        self._is_selected = False
        self._is_favorite = getattr(sequence, "is_favorite", False)
        self._hover_scale = 1.0
        self._glow_opacity = 0.0

        # Animation system
        self._hover_animation: Optional[QParallelAnimationGroup] = None
        self._selection_animation: Optional[QPropertyAnimation] = None

        # Chunked loading manager (set externally)
        self._chunked_loading_manager = None

        # UI components
        self.thumbnail_label: Optional[QLabel] = None
        self.title_label: Optional[QLabel] = None
        self.metadata_label: Optional[QLabel] = None
        self.favorite_button: Optional[QPushButton] = None
        self.loading_indicator: Optional[QWidget] = None

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

        logger.debug(f"ModernThumbnailCard created for sequence: {sequence.name}")

    def _setup_ui(self):
        """Setup the card UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            self.card_padding, self.card_padding, self.card_padding, self.card_padding
        )
        layout.setSpacing(12)

        # Thumbnail container
        thumbnail_container = QFrame()
        thumbnail_container.setObjectName("thumbnailContainer")
        thumbnail_container.setFixedHeight(200)

        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        # Thumbnail image
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setObjectName("thumbnailImage")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setScaledContents(
            False
        )  # Disable auto-scaling to preserve aspect ratio
        self.thumbnail_label.setMinimumHeight(180)

        thumbnail_layout.addWidget(self.thumbnail_label)
        layout.addWidget(thumbnail_container)

        # Content section
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # Title and favorite button row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)

        # Title
        self.title_label = QLabel(self.sequence.name)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # Favorite button
        self.favorite_button = QPushButton("♡" if not self._is_favorite else "♥")
        self.favorite_button.setObjectName("favoriteButton")
        self.favorite_button.setFixedSize(24, 24)
        self.favorite_button.clicked.connect(self._toggle_favorite)

        title_row.addWidget(self.title_label)
        title_row.addWidget(self.favorite_button)

        content_layout.addLayout(title_row)

        # Metadata
        metadata_text = self._format_metadata()
        self.metadata_label = QLabel(metadata_text)
        self.metadata_label.setObjectName("metadataLabel")
        metadata_font = QFont()
        metadata_font.setPointSize(10)
        self.metadata_label.setFont(metadata_font)

        content_layout.addWidget(self.metadata_label)

        layout.addWidget(content_frame)

        # Set size policy for fixed layout stability
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Apply default fixed size (will be overridden by grid if needed)
        self.setFixedSize(280, 320)

        # Store default dimensions for sizeHint consistency
        self._fixed_width = 280
        self._fixed_height = 320

    def _setup_styling(self):
        """Apply modern glassmorphic styling with optimized CSS-only hover animations."""
        self.setStyleSheet(
            f"""
            ModernThumbnailCard {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {self.card_radius}px;
                transition: all 150ms cubic-bezier(0.4, 0.0, 0.2, 1);
            }}
            
            ModernThumbnailCard:hover,
            ModernThumbnailCard[hovered="true"] {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                transform: scale(1.02);
            }}
            
            QFrame#thumbnailContainer {{
                background: rgba(0, 0, 0, 0.1);
                border-radius: {self.thumbnail_radius}px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: all 150ms cubic-bezier(0.4, 0.0, 0.2, 1);
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
                transition: all 100ms ease-out;
            }}
            
            QPushButton#favoriteButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
                color: rgba(255, 255, 255, 1.0);
            }}
            
            QPushButton#favoriteButton:pressed {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """
        )

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _setup_animations(self):
        """Setup animation system for smooth transitions."""
        # Hover animation will be created dynamically
        pass

    def _format_metadata(self) -> str:
        """Format sequence metadata for display."""
        metadata_parts = []

        if hasattr(self.sequence, "difficulty") and self.sequence.difficulty:
            metadata_parts.append(f"Difficulty: {self.sequence.difficulty}")

        if hasattr(self.sequence, "length") and self.sequence.length:
            metadata_parts.append(f"Length: {self.sequence.length}")

        if hasattr(self.sequence, "category") and self.sequence.category:
            metadata_parts.append(f"Category: {self.sequence.category}")

        return " • ".join(metadata_parts) if metadata_parts else "No metadata"

    def _load_thumbnail(self):
        """Load and display the thumbnail image synchronously."""
        # Show loading state initially
        self.set_loading_state(True)

        # Check if sequence has thumbnails
        if not hasattr(self.sequence, "thumbnails") or not self.sequence.thumbnails:
            self.set_error_state("No thumbnails available")
            return

        # Get the first thumbnail path
        thumbnail_path = self.sequence.thumbnails[0]

        # Verify the file exists
        import os

        if not os.path.exists(thumbnail_path):
            logger.warning(f"Thumbnail file not found: {thumbnail_path}")
            self.set_error_state("Image not found")
            return

        try:
            # Check if we're in chunked loading mode
            if (
                hasattr(self, "_chunked_loading_manager")
                and self._chunked_loading_manager
            ):
                # Queue for chunked loading
                self._chunked_loading_manager.queue_image_load(self, thumbnail_path)
            else:
                # Use direct synchronous loading for reliability
                self._load_image_sync(thumbnail_path)

        except Exception as e:
            logger.error(f"Error loading thumbnail for {self.sequence.name}: {e}")
            self.set_error_state("Load error")

    def _load_image_async(self, image_path: str):
        """Load image asynchronously using the image loader service."""
        logger.debug(f"🔧 _load_image_async() called for {image_path}")
        try:
            # Get the image loader service from the parent's config or create one
            image_loader = self._get_image_loader()
            logger.debug(
                f"🔧 Image loader obtained: {type(image_loader) if image_loader else 'None'}"
            )

            if not image_loader:
                # Fallback to synchronous loading if no async loader available
                logger.warning(
                    f"⚠️ No async loader available, falling back to sync for {image_path}"
                )
                self._load_image_sync(image_path)
                return

            # Calculate target size for optimal loading
            target_size = (300, 200)  # Reasonable thumbnail size
            logger.debug(f"🎯 Target size for {image_path}: {target_size}")

            # Start async loading
            import asyncio
            from PyQt6.QtCore import QTimer

            def trigger_async_load():
                try:
                    logger.debug(f"🚀 Triggering async load for {image_path}")
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        logger.debug(
                            f"📡 Event loop running, creating task for {image_path}"
                        )
                        asyncio.create_task(
                            self._handle_async_image_load(
                                image_loader, image_path, target_size
                            )
                        )
                    else:
                        logger.debug(
                            f"🔄 Event loop not running, running until complete for {image_path}"
                        )
                        loop.run_until_complete(
                            self._handle_async_image_load(
                                image_loader, image_path, target_size
                            )
                        )
                except Exception as e:
                    logger.error(f"❌ Async image load failed for {image_path}: {e}")
                    self._load_image_sync(image_path)

            # Use QTimer to safely trigger async operation
            logger.debug(f"⏰ Setting QTimer for async load of {image_path}")
            QTimer.singleShot(10, trigger_async_load)

        except Exception as e:
            logger.error(
                f"❌ Failed to start async image loading for {image_path}: {e}"
            )
            self._load_image_sync(image_path)

    async def _handle_async_image_load(
        self, image_loader, image_path: str, target_size: tuple
    ):
        """Handle the async image loading process."""
        try:
            # Load image asynchronously
            pixmap = await image_loader.load_image_async(image_path, target_size)

            if pixmap and not pixmap.isNull():
                # Use QTimer to safely update UI from async context
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(0, lambda: self._on_image_loaded(pixmap, image_path))
            else:
                QTimer.singleShot(
                    0, lambda: self._on_image_load_failed(image_path, "Failed to load")
                )

        except Exception as e:
            logger.error(f"Async image loading error: {e}")
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(0, lambda: self._on_image_load_failed(image_path, str(e)))

    def _load_image_sync(self, image_path: str):
        """Synchronous image loading."""
        try:
            from PyQt6.QtGui import QPixmap

            pixmap = QPixmap(image_path)

            if pixmap.isNull():
                self._on_image_load_failed(image_path, "Failed to load")
                return

            self._on_image_loaded(pixmap, image_path)

        except Exception as e:
            logger.error(f"Sync image loading error for {image_path}: {e}")
            self._on_image_load_failed(image_path, str(e))

    def _get_image_loader(self):
        """Get the image loader service."""
        logger.debug(f"🔧 _get_image_loader() called")
        try:
            # Try to get from config first
            logger.debug(
                f"🔧 Checking config for image_loader: {hasattr(self.config, 'image_loader')}"
            )
            if hasattr(self.config, "image_loader") and self.config.image_loader:
                logger.debug(
                    f"✅ Found image_loader in config: {type(self.config.image_loader)}"
                )
                return self.config.image_loader

            # Try to get from parent browse tab
            logger.debug(f"🔧 Checking parent hierarchy for image_loader")
            parent = self.parent()
            while parent:
                logger.debug(f"🔧 Checking parent: {type(parent)}")
                if hasattr(parent, "image_loader"):
                    logger.debug(
                        f"✅ Found image_loader in parent: {type(parent.image_loader)}"
                    )
                    return parent.image_loader
                parent = parent.parent()

            # Try to import and create one
            logger.debug(f"🔧 Creating new AsyncImageLoader")
            from ..services.image_loader import AsyncImageLoader

            loader = AsyncImageLoader()
            logger.debug(f"✅ Created new AsyncImageLoader: {type(loader)}")
            return loader

        except Exception as e:
            logger.error(f"❌ Could not get image loader: {e}")
            return None

    def _on_image_loaded(self, pixmap, image_path: str):
        """Handle successful image loading."""
        try:
            self.set_thumbnail_image(pixmap)
            self.set_loading_state(False)
        except Exception as e:
            logger.error(f"Error setting loaded image for {image_path}: {e}")
            self.set_error_state("Display error")

    def _on_image_load_failed(self, image_path: str, error_msg: str):
        """Handle failed image loading."""
        logger.warning(f"Failed to load thumbnail {image_path}: {error_msg}")
        self.set_error_state("Load failed")

    def set_preloaded_thumbnail(self, thumbnail_path: str):
        """Set thumbnail from pre-loaded cache for instant display."""
        try:
            # Try to get from cache first
            from ..services.cache_service import CacheService

            cache_service = CacheService()

            # Check cache for pre-loaded image
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Use async cache access
                    asyncio.create_task(
                        self._load_from_cache_async(cache_service, thumbnail_path)
                    )
                else:
                    # Fallback to sync loading
                    self._load_from_cache_sync(cache_service, thumbnail_path)
            except Exception:
                # Final fallback to direct loading
                self._load_image_sync(thumbnail_path)

        except Exception as e:
            logger.debug(f"Preloaded thumbnail failed, using normal loading: {e}")
            self._load_image_sync(thumbnail_path)

    async def _load_from_cache_async(self, cache_service, thumbnail_path: str):
        """Load thumbnail from cache asynchronously."""
        try:
            pixmap = await cache_service.get_cached_image(thumbnail_path, (260, 220))
            if pixmap and not pixmap.isNull():
                # Use QTimer to safely update UI
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(
                    0, lambda: self._on_image_loaded(pixmap, thumbnail_path)
                )
            else:
                # Cache miss, load normally
                QTimer.singleShot(0, lambda: self._load_image_sync(thumbnail_path))
        except Exception as e:
            logger.debug(f"Cache load failed: {e}")
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(0, lambda: self._load_image_sync(thumbnail_path))

    def _load_from_cache_sync(self, cache_service, thumbnail_path: str):
        """Load thumbnail from cache synchronously."""
        try:
            # Try memory cache first
            cache_key = cache_service._get_cache_key(thumbnail_path, (260, 220))
            pixmap = cache_service.memory_cache.get(cache_key)

            if pixmap and not pixmap.isNull():
                self._on_image_loaded(pixmap, thumbnail_path)
            else:
                # Cache miss, load normally
                self._load_image_sync(thumbnail_path)
        except Exception as e:
            logger.debug(f"Sync cache load failed: {e}")
            self._load_image_sync(thumbnail_path)

    def _load_image_fast(self):
        """
        Fast image loading method expected by EfficientVirtualGrid.

        This method provides compatibility with the virtual grid's viewport rendering
        system by connecting to the ModernThumbnailCard's existing image loading.
        """
        if not hasattr(self, "_image_loaded") or not self._image_loaded:
            # Use the card's existing image loading system
            if hasattr(self.sequence, "thumbnails") and self.sequence.thumbnails:
                thumbnail_path = self.sequence.thumbnails[0]
                logger.debug(
                    f"🚀 MODERN_CARD: _load_image_fast() loading {thumbnail_path}"
                )
                self._load_image_sync(thumbnail_path)
                self._image_loaded = True
            else:
                logger.debug(
                    f"🚀 MODERN_CARD: _load_image_fast() no thumbnails for {self.sequence.id}"
                )
                self._show_placeholder()
                self._image_loaded = True

    def _toggle_favorite(self):
        """Toggle favorite status."""
        self._is_favorite = not self._is_favorite
        self.favorite_button.setText("♥" if self._is_favorite else "♡")

        # Update button styling
        if self._is_favorite:
            self.favorite_button.setStyleSheet(
                """
                QPushButton#favoriteButton {
                    color: #ff6b6b;
                    background: rgba(255, 107, 107, 0.2);
                    border: 1px solid rgba(255, 107, 107, 0.4);
                }
            """
            )
        else:
            self.favorite_button.setStyleSheet("")  # Reset to default

        self.favorite_toggled.emit(self.sequence.id, self._is_favorite)

    def set_selected(self, selected: bool):
        """Set the selection state of the card."""
        if self._is_selected == selected:
            return

        self._is_selected = selected
        self._current_state = self.STATE_SELECTED if selected else self.STATE_NORMAL

        # Animate selection change
        if self.config.enable_animations:
            self._animate_selection_change()
        else:
            self._update_selection_styling()

    def _animate_selection_change(self):
        """Animate selection state change."""
        if self._selection_animation:
            self._selection_animation.stop()

        # Create selection animation (border glow effect)
        self._selection_animation = QPropertyAnimation(self, b"glow_opacity")
        self._selection_animation.setDuration(200)
        self._selection_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        if self._is_selected:
            self._selection_animation.setStartValue(0.0)
            self._selection_animation.setEndValue(1.0)
        else:
            self._selection_animation.setStartValue(1.0)
            self._selection_animation.setEndValue(0.0)

        self._selection_animation.valueChanged.connect(self._update_selection_styling)
        self._selection_animation.start()

    def _update_selection_styling(self):
        """Update styling based on selection state."""
        if self._is_selected:
            self.setStyleSheet(
                self.styleSheet()
                + """
                ModernThumbnailCard {
                    border: 2px solid rgba(76, 175, 80, 0.8);
                    background: rgba(76, 175, 80, 0.1);
                }
            """
            )
        else:
            # Reset to default styling
            self._setup_styling()

    def enterEvent(self, event):
        """Optimized hover enter - lightweight CSS-only animation for 60fps performance."""
        super().enterEvent(event)
        # PERFORMANCE FIX: Remove complex animation system, use CSS-only transitions
        self.setProperty("hovered", True)
        self.style().polish(self)  # Force immediate style update

    def leaveEvent(self, event):
        """Optimized hover leave - immediate CSS reset."""
        super().leaveEvent(event)
        # PERFORMANCE FIX: Immediate CSS reset for responsive hover
        self.setProperty("hovered", False)
        self.style().polish(self)  # Force immediate style update

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

    def set_thumbnail_image(self, pixmap: QPixmap):
        """Set the thumbnail image with aspect-ratio-aware scaling for fixed layout."""
        if pixmap and not pixmap.isNull():
            # Get the thumbnail container size
            container_size = self.thumbnail_label.size()

            # If container size is not valid yet, use the parent card size or fallback
            if container_size.width() <= 0 or container_size.height() <= 0:
                # Try to get size from parent card
                parent_size = self.size()
                if parent_size.width() > 0 and parent_size.height() > 0:
                    # Use most of the card space for the image, leaving room for metadata
                    container_size = QSize(
                        parent_size.width() - 20, parent_size.height() - 80
                    )
                else:
                    # Use fixed dimensions as fallback
                    from PyQt6.QtCore import QSize

                    container_size = QSize(260, 200)  # Conservative fallback

            # Apply aspect-ratio-aware scaling strategy
            scaled_pixmap = self._scale_image_with_aspect_ratio_management(
                pixmap, container_size
            )

            # Set the scaled pixmap
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_label.setText("")

            # Configure label for fixed layout
            self.thumbnail_label.setScaledContents(False)  # Disable automatic scaling
            self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            logger.debug(
                f"Set thumbnail image: {pixmap.size()} -> {scaled_pixmap.size()} in container {container_size.width()}x{container_size.height()}"
            )
        else:
            self.thumbnail_label.setText("No Image")
            self.thumbnail_label.setPixmap(QPixmap())  # Clear any existing pixmap

    def _scale_image_with_aspect_ratio_management(
        self, pixmap: QPixmap, container_size
    ):
        """Scale image with width-first constraint and aspect ratio management."""
        try:
            original_size = pixmap.size()
            container_width = container_size.width()
            container_height = container_size.height()

            # Calculate aspect ratios
            original_aspect = original_size.width() / original_size.height()
            container_aspect = container_width / container_height

            # Width-first constraint: force image to fill 100% of container width
            target_width = container_width
            target_height = int(target_width / original_aspect)

            # Height management based on image orientation
            if original_aspect > 1.0:  # Landscape image (width > height)
                # For landscape images, scale to fit width and crop/letterbox height if needed
                if target_height > container_height:
                    # Image is too tall, scale down to fit height
                    target_height = container_height
                    target_width = int(target_height * original_aspect)

            elif original_aspect < 1.0:  # Portrait image (height > width)
                # For portrait images, apply maximum height constraint
                max_height = int(container_width * 1.5)  # 1.5x width maximum
                if target_height > max_height:
                    target_height = max_height
                    target_width = int(target_height * original_aspect)

            else:  # Square image (aspect ratio = 1.0)
                # For square images, use the smaller dimension to fit in container
                target_size = min(container_width, container_height)
                target_width = target_size
                target_height = target_size

            # Ensure we don't exceed container bounds
            target_width = min(target_width, container_width)
            target_height = min(target_height, container_height)

            # Scale the pixmap
            from PyQt6.QtCore import QSize

            target_size = QSize(target_width, target_height)

            scaled_pixmap = pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            logger.debug(
                f"Aspect-ratio scaling: {original_size.width()}x{original_size.height()} "
                f"(aspect {original_aspect:.2f}) -> {target_width}x{target_height} "
                f"in container {container_width}x{container_height}"
            )

            return scaled_pixmap

        except Exception as e:
            logger.error(f"Failed to scale image with aspect ratio management: {e}")
            # Fallback to simple scaling
            return pixmap.scaled(
                container_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

    def set_loading_state(self, loading: bool):
        """Set the loading state of the card."""
        if loading:
            self._current_state = self.STATE_LOADING
            self.thumbnail_label.setText("Loading...")
        else:
            self._current_state = self.STATE_NORMAL

    def set_error_state(self, error_message: str = "Error"):
        """Set the error state of the card."""
        self._current_state = self.STATE_ERROR
        self.thumbnail_label.setText(error_message)
        self.thumbnail_label.setStyleSheet(
            """
            QLabel {
                color: #ff6b6b;
                background: rgba(255, 107, 107, 0.1);
            }
        """
        )

    def get_sequence_id(self) -> str:
        """Get the sequence ID."""
        return self.sequence.id

    def is_selected(self) -> bool:
        """Check if the card is selected."""
        return self._is_selected

    def is_favorite(self) -> bool:
        """Check if the card is marked as favorite."""
        return self._is_favorite

    def set_chunked_loading_manager(self, manager):
        """Set the chunked loading manager for this card."""
        self._chunked_loading_manager = manager

    def sizeHint(self) -> QSize:
        """Provide consistent size hint for layout management."""
        from PyQt6.QtCore import QSize

        return QSize(self._fixed_width, self._fixed_height)

    def minimumSizeHint(self) -> QSize:
        """Provide consistent minimum size hint."""
        from PyQt6.QtCore import QSize

        return QSize(self._fixed_width, self._fixed_height)

    def apply_fixed_size(self, width: int, height: int):
        """Apply fixed size with responsive scaling support for 25% width layout."""
        self._fixed_width = width
        self._fixed_height = height

        # Apply size constraints that allow responsive scaling
        self.setFixedSize(width, height)
        self.setMinimumSize(width, height)
        # Remove maximum size constraint to enable proper responsive scaling
        self.setMaximumSize(16777215, 16777215)  # Qt's QWIDGETSIZE_MAX

        # Use expanding size policy for responsive behavior
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Force geometry update
        self.updateGeometry()

        # Update image container to scale proportionally
        if hasattr(self, "image_container"):
            self.image_container.setMinimumSize(width - 20, height - 80)
            self.image_container.setMaximumSize(16777215, 16777215)

        logger.debug(
            f"Applied responsive fixed size: {width}x{height} to card {self.sequence.name} (25% width scaling enabled)"
        )

    def resizeEvent(self, event):
        """Override resize event to prevent unwanted size changes and reduce excessive events."""
        # Initialize resize tracking if not exists
        if not hasattr(self, "_card_resize_count"):
            self._card_resize_count = 0
            self._last_resize_time = 0

        import time

        current_time = time.time()

        # Reset counter if more than 1 second has passed
        if current_time - self._last_resize_time > 1.0:
            self._card_resize_count = 0

        self._card_resize_count += 1
        self._last_resize_time = current_time

        old_size = event.oldSize()
        new_size = event.size()

        # Log only problematic resize events
        size_correct = (
            new_size.width() == self._fixed_width
            and new_size.height() == self._fixed_height
        )
        if not size_correct or self._card_resize_count <= 2:
            logger.debug(
                f"Card resize #{self._card_resize_count} - {self.sequence.name}: "
                f"{old_size.width()}x{old_size.height()} → {new_size.width()}x{new_size.height()} "
                f"(expected: {self._fixed_width}x{self._fixed_height})"
            )

        # Throttle excessive resize events during chunked loading
        if self._card_resize_count > 2:
            # Allow only the first 2 resize events, then throttle
            if (
                new_size.width() == self._fixed_width
                and new_size.height() == self._fixed_height
            ):
                # Size is already correct, skip this resize event
                return

        # Only allow resize if it matches our fixed dimensions
        if (
            new_size.width() != self._fixed_width
            or new_size.height() != self._fixed_height
        ):
            # Force back to fixed size
            self.setFixedSize(self._fixed_width, self._fixed_height)
            return

        super().resizeEvent(event)
