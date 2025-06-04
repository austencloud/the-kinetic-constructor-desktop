"""
Skeleton Thumbnail Card - Modern Loading Placeholder

This component provides an elegant skeleton screen that matches the FastThumbnailCard
layout exactly (280x320px) with glassmorphic shimmer animations.

Features:
- Perfect layout matching with FastThumbnailCard
- Glassmorphic shimmer animations
- Optimized for 60fps performance
- Minimal memory footprint
- Instant creation time
"""

import logging
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
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
)
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class SkeletonThumbnailCard(QWidget):
    """
    Modern skeleton screen with glassmorphic shimmer effects.
    
    Matches FastThumbnailCard layout exactly:
    - 280x320px total size
    - 240px image area
    - Title area with proper spacing
    - Glassmorphic styling with shimmer animation
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Fixed dimensions matching FastThumbnailCard
        self._width = 280
        self._height = 320
        
        # Animation state
        self._shimmer_opacity = 0.3
        
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """Setup skeleton UI structure matching FastThumbnailCard."""
        # Apply fixed size immediately
        self.setFixedSize(self._width, self._height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Simple vertical layout matching FastThumbnailCard
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Skeleton image area - matches FastThumbnailCard image_label
        self.skeleton_image = QLabel()
        self.skeleton_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.skeleton_image.setFixedHeight(240)  # Exact match
        self._setup_skeleton_image_style()
        layout.addWidget(self.skeleton_image)

        # Skeleton title area - matches FastThumbnailCard title_label
        self.skeleton_title = QLabel()
        self.skeleton_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.skeleton_title.setFixedHeight(30)  # Approximate title height
        self._setup_skeleton_title_style()
        layout.addWidget(self.skeleton_title)

        # Card styling matching FastThumbnailCard
        self.setStyleSheet(
            """
            SkeletonThumbnailCard {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                backdrop-filter: blur(8px);
            }
        """
        )

    def _setup_skeleton_image_style(self):
        """Setup skeleton image area with shimmer effect."""
        self.skeleton_image.setStyleSheet(
            f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:0.4 rgba(255, 255, 255, {self._shimmer_opacity}),
                    stop:0.6 rgba(255, 255, 255, {self._shimmer_opacity}),
                    stop:1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }}
        """
        )

    def _setup_skeleton_title_style(self):
        """Setup skeleton title area with shimmer effect."""
        self.skeleton_title.setStyleSheet(
            f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.05),
                    stop:0.3 rgba(255, 255, 255, {self._shimmer_opacity * 0.7}),
                    stop:0.7 rgba(255, 255, 255, {self._shimmer_opacity * 0.7}),
                    stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                backdrop-filter: blur(8px);
            }}
        """
        )

    def _setup_animations(self):
        """Setup shimmer animation for skeleton elements."""
        # Create shimmer animation
        self.shimmer_animation = QPropertyAnimation(self, b"shimmer_opacity")
        self.shimmer_animation.setDuration(1500)  # 1.5 second cycle
        self.shimmer_animation.setStartValue(0.2)
        self.shimmer_animation.setEndValue(0.5)
        self.shimmer_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        # Make it loop
        self.shimmer_animation.setLoopCount(-1)  # Infinite loop
        
        # Start animation
        self.shimmer_animation.start()

    @pyqtProperty(float)
    def shimmer_opacity(self):
        """Get current shimmer opacity."""
        return self._shimmer_opacity

    @shimmer_opacity.setter
    def shimmer_opacity(self, value):
        """Set shimmer opacity and update styles."""
        self._shimmer_opacity = value
        self._setup_skeleton_image_style()
        self._setup_skeleton_title_style()

    def sizeHint(self) -> QSize:
        """Provide fixed size hint matching FastThumbnailCard."""
        return QSize(self._width, self._height)

    def minimumSizeHint(self) -> QSize:
        """Provide fixed minimum size hint matching FastThumbnailCard."""
        return QSize(self._width, self._height)

    def stop_animation(self):
        """Stop shimmer animation (useful when replacing with real content)."""
        if hasattr(self, 'shimmer_animation'):
            self.shimmer_animation.stop()

    def start_animation(self):
        """Start shimmer animation."""
        if hasattr(self, 'shimmer_animation'):
            self.shimmer_animation.start()


class FastSkeletonCard(QWidget):
    """
    Ultra-fast skeleton card with no animations for maximum performance.
    
    Use this when you need instant skeleton display without shimmer effects.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Fixed dimensions
        self.setFixedSize(280, 320)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Simple layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Static skeleton image
        skeleton_image = QLabel()
        skeleton_image.setFixedHeight(240)
        skeleton_image.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                backdrop-filter: blur(5px);
            }
        """
        )
        layout.addWidget(skeleton_image)

        # Static skeleton title
        skeleton_title = QLabel()
        skeleton_title.setFixedHeight(30)
        skeleton_title.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                backdrop-filter: blur(5px);
            }
        """
        )
        layout.addWidget(skeleton_title)

        # Card styling
        self.setStyleSheet(
            """
            FastSkeletonCard {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                backdrop-filter: blur(8px);
            }
        """
        )

    def sizeHint(self) -> QSize:
        """Provide fixed size hint."""
        return QSize(280, 320)

    def minimumSizeHint(self) -> QSize:
        """Provide fixed minimum size hint."""
        return QSize(280, 320)
