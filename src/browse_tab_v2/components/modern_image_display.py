"""
Modern Image Display Component

Large image display with glassmorphism effects, progressive loading,
and smooth transitions for the sequence viewer.

Features:
- Progressive image loading with placeholders
- Smooth transition animations
- Glassmorphism styling
- Zoom controls (future enhancement)
- Error handling with fallback states
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor

from ..core.interfaces import BrowseTabConfig
from .loading_states import LoadingIndicator

logger = logging.getLogger(__name__)


class ImageLoader(QThread):
    """Background thread for loading images without blocking UI."""
    
    image_loaded = pyqtSignal(QPixmap)
    loading_failed = pyqtSignal(str)  # error_message
    
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        """Load image in background thread."""
        try:
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                self.image_loaded.emit(pixmap)
            else:
                self.loading_failed.emit(f"Failed to load image: {self.image_path}")
        except Exception as e:
            self.loading_failed.emit(f"Error loading image: {str(e)}")


class ModernImageDisplay(QWidget):
    """
    Modern image display with progressive loading and smooth transitions.
    
    Features:
    - Background image loading
    - Smooth fade transitions
    - Loading indicators
    - Error states with retry
    - Glassmorphism styling
    - Responsive scaling
    """
    
    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)
        
        self.config = config or BrowseTabConfig()
        
        # State
        self.current_image_path: Optional[str] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.is_loading = False
        
        # Components
        self.image_label: Optional[QLabel] = None
        self.loading_indicator: Optional[LoadingIndicator] = None
        self.error_label: Optional[QLabel] = None
        
        # Background loader
        self.image_loader: Optional[ImageLoader] = None
        
        # Animation
        self.fade_animation: Optional[QPropertyAnimation] = None
        
        self._setup_ui()
        self._setup_styling()
        
        logger.debug("ModernImageDisplay initialized")
    
    def _setup_ui(self):
        """Setup the image display UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main container frame
        self.container_frame = QFrame()
        self.container_frame.setObjectName("imageContainer")
        container_layout = QVBoxLayout(self.container_frame)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(0)
        
        # Image label (main display)
        self.image_label = QLabel()
        self.image_label.setObjectName("imageLabel")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)  # We'll handle scaling manually
        self.image_label.setMinimumHeight(300)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        container_layout.addWidget(self.image_label, 1)
        
        # Loading indicator (overlay)
        self.loading_indicator = LoadingIndicator(size=48, show_text=True, parent=self)
        self.loading_indicator.set_loading_text("Loading image...")
        self.loading_indicator.hide()
        
        # Error label (for failed loads)
        self.error_label = QLabel("Failed to load image")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 12)
        self.error_label.setFont(font)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)
        
        layout.addWidget(self.container_frame)
        
        # Show empty state initially
        self.show_empty_state()
    
    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet("""
            QFrame#imageContainer {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 15px;
            }
            
            QLabel#imageLabel {
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;
            }
            
            QLabel#emptyLabel {
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
                border: none;
                font-size: 14px;
            }
            
            QLabel#errorLabel {
                color: rgba(255, 107, 107, 0.8);
                background: transparent;
                border: none;
            }
        """)
    
    def load_image_with_transition(self, image_path: str):
        """Load image with smooth transition animation."""
        if self.current_image_path == image_path:
            return  # Already loaded
        
        logger.debug(f"Loading image: {image_path}")
        
        self.current_image_path = image_path
        self.is_loading = True
        
        # Hide error state
        self.error_label.hide()
        
        # Show loading indicator
        self._show_loading_state()
        
        # Start background loading
        self._start_background_loading(image_path)
    
    def _start_background_loading(self, image_path: str):
        """Start loading image in background thread."""
        # Clean up previous loader
        if self.image_loader and self.image_loader.isRunning():
            self.image_loader.terminate()
            self.image_loader.wait()
        
        # Create new loader
        self.image_loader = ImageLoader(image_path)
        self.image_loader.image_loaded.connect(self._on_image_loaded)
        self.image_loader.loading_failed.connect(self._on_loading_failed)
        self.image_loader.start()
    
    def _on_image_loaded(self, pixmap: QPixmap):
        """Handle successful image loading."""
        self.is_loading = False
        self.current_pixmap = pixmap
        
        # Hide loading indicator
        self._hide_loading_state()
        
        # Scale pixmap to fit label while maintaining aspect ratio
        scaled_pixmap = self._scale_pixmap_to_fit(pixmap)
        
        # Apply with fade transition
        if self.config.enable_animations:
            self._fade_in_image(scaled_pixmap)
        else:
            self.image_label.setPixmap(scaled_pixmap)
        
        logger.debug(f"Image loaded successfully: {self.current_image_path}")
    
    def _on_loading_failed(self, error_message: str):
        """Handle failed image loading."""
        self.is_loading = False
        
        # Hide loading indicator
        self._hide_loading_state()
        
        # Show error state
        self.error_label.setText(f"Failed to load image\n{error_message}")
        self.error_label.show()
        
        logger.error(f"Failed to load image: {error_message}")
    
    def _scale_pixmap_to_fit(self, pixmap: QPixmap) -> QPixmap:
        """Scale pixmap to fit the label while maintaining aspect ratio."""
        label_size = self.image_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return pixmap
        
        # Scale to fit within label bounds
        scaled_pixmap = pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        return scaled_pixmap
    
    def _fade_in_image(self, pixmap: QPixmap):
        """Apply image with fade-in animation."""
        # Set the new pixmap
        self.image_label.setPixmap(pixmap)
        
        # Create fade-in animation
        self.fade_animation = QPropertyAnimation(self.image_label, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animation
        self.image_label.setWindowOpacity(0.0)
        self.fade_animation.start()
    
    def _show_loading_state(self):
        """Show loading indicator."""
        # Position loading indicator in center
        self._position_loading_indicator()
        self.loading_indicator.show()
        self.loading_indicator.start_animation()
    
    def _hide_loading_state(self):
        """Hide loading indicator."""
        self.loading_indicator.stop_animation()
        self.loading_indicator.hide()
    
    def _position_loading_indicator(self):
        """Position loading indicator in center of image area."""
        if self.loading_indicator:
            # Calculate center position
            container_rect = self.container_frame.rect()
            indicator_size = self.loading_indicator.size()
            
            x = (container_rect.width() - indicator_size.width()) // 2
            y = (container_rect.height() - indicator_size.height()) // 2
            
            self.loading_indicator.move(x, y)
    
    def show_empty_state(self):
        """Show empty state when no image is selected."""
        self.image_label.clear()
        self.image_label.setText("No image selected")
        self.image_label.setObjectName("emptyLabel")
        self.error_label.hide()
        self._hide_loading_state()
        
        self.current_image_path = None
        self.current_pixmap = None
    
    def resizeEvent(self, event):
        """Handle resize events to reposition loading indicator."""
        super().resizeEvent(event)
        
        # Reposition loading indicator
        if self.loading_indicator and self.loading_indicator.isVisible():
            self._position_loading_indicator()
        
        # Rescale current image if available
        if self.current_pixmap and not self.is_loading:
            scaled_pixmap = self._scale_pixmap_to_fit(self.current_pixmap)
            self.image_label.setPixmap(scaled_pixmap)
    
    def get_current_image_path(self) -> Optional[str]:
        """Get currently displayed image path."""
        return self.current_image_path
    
    def clear(self):
        """Clear the image display."""
        self.show_empty_state()
        
        # Stop any running loader
        if self.image_loader and self.image_loader.isRunning():
            self.image_loader.terminate()
            self.image_loader.wait()
    
    def __del__(self):
        """Cleanup when widget is destroyed."""
        if self.image_loader and self.image_loader.isRunning():
            self.image_loader.terminate()
            self.image_loader.wait()
