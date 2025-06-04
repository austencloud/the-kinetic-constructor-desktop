"""
Modern Progress Bar - Professional horizontal progress bar for browse tab loading.

Features:
- Glassmorphism styling with modern aesthetics
- Progress percentage and current/total counts
- Cancel button for user control
- Smooth animations and responsive design
- Top-positioned for optimal UX
"""

import logging
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame
)

from styles.glassmorphism_styler import GlassmorphismStyler


class ModernProgressBar(QFrame):
    """
    Modern horizontal progress bar for browse tab loading operations.
    
    Features:
    - Professional glassmorphism styling
    - Progress tracking with percentage and counts
    - Cancel functionality
    - Responsive design
    """
    
    # Signals
    cancelled = pyqtSignal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        self.parent_widget = parent
        self._total = 0
        self._current = 0
        
        self._setup_ui()
        self._setup_styling()
        self.hide()  # Hidden by default
        
    def _setup_ui(self):
        """Setup the UI components."""
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 10)
        self.main_layout.setSpacing(15)
        
        # Progress info layout (left side)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Status label
        self.status_label = QLabel("Loading sequences...")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        info_layout.addWidget(self.status_label)
        
        # Count label
        self.count_label = QLabel("0 / 0")
        self.count_label.setFont(QFont("Segoe UI", 9))
        info_layout.addWidget(self.count_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(80, 30)
        self.cancel_button.clicked.connect(self._on_cancel)
        
        # Layout assembly
        self.main_layout.addLayout(info_layout, 0)  # No stretch
        self.main_layout.addWidget(self.progress_bar, 1)  # Takes most space
        self.main_layout.addWidget(self.cancel_button, 0)  # No stretch
        
    def _setup_styling(self):
        """Apply modern glassmorphism styling."""
        try:
            # Main frame styling
            self.setFrameStyle(QFrame.Shape.StyledPanel)
            
            # Create glassmorphism effect
            style = GlassmorphismStyler.create_glassmorphism_card(
                self,
                blur_radius=15,
                opacity=0.12,
                border_radius=12,
            )
            
            # Enhanced styling
            enhanced_style = f"""
            QFrame {{
                {style}
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(99, 102, 241, 0.15),
                    stop: 1 rgba(139, 92, 246, 0.10)
                );
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                margin: 5px;
            }}
            
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }}
            
            QProgressBar {{
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                background: rgba(0, 0, 0, 0.2);
                text-align: center;
                color: white;
                font-weight: bold;
                min-height: 20px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(34, 197, 94, 0.8),
                    stop: 1 rgba(59, 130, 246, 0.8)
                );
                border-radius: 7px;
                margin: 1px;
            }}
            
            QPushButton {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(239, 68, 68, 0.8),
                    stop: 1 rgba(220, 38, 38, 0.8)
                );
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 9px;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(239, 68, 68, 0.9),
                    stop: 1 rgba(220, 38, 38, 0.9)
                );
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
            
            QPushButton:pressed {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(220, 38, 38, 0.9),
                    stop: 1 rgba(185, 28, 28, 0.9)
                );
            }}
            """
            
            self.setStyleSheet(enhanced_style)
            
            # Add subtle shadow effect
            GlassmorphismStyler.add_shadow_effect(
                self, offset_y=3, blur_radius=10, color="rgba(0, 0, 0, 0.15)"
            )
            
        except Exception as e:
            logging.warning(f"Failed to apply glassmorphism styling: {e}")
            # Fallback to basic styling
            self.setStyleSheet("""
                QFrame {
                    background: rgba(0, 0, 0, 0.8);
                    border: 1px solid #6366f1;
                    border-radius: 8px;
                    margin: 5px;
                }
                QLabel { color: white; }
                QPushButton {
                    background: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
    
    def set_total(self, total: int):
        """Set the total number of items to process."""
        self._total = total
        self.progress_bar.setMaximum(total)
        self._update_display()
        
    def set_current(self, current: int):
        """Set the current progress."""
        self._current = current
        self.progress_bar.setValue(current)
        self._update_display()
        
    def _update_display(self):
        """Update the display labels."""
        self.count_label.setText(f"{self._current} / {self._total}")
        
        if self._total > 0:
            percentage = int((self._current / self._total) * 100)
            self.progress_bar.setFormat(f"{percentage}%")
        else:
            self.progress_bar.setFormat("0%")
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled.emit()
        self.hide()
        
    def reset(self):
        """Reset the progress bar."""
        self._current = 0
        self._total = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self._update_display()
        
    def show_with_message(self, message: str, total: int = 0):
        """Show the progress bar with a custom message."""
        self.status_label.setText(message)
        if total > 0:
            self.set_total(total)
        self.show()
        
    def hide_progress(self):
        """Hide the progress bar."""
        self.hide()
