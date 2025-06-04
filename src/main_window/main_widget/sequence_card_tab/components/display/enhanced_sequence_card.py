"""
Enhanced sequence card widget with visual distinction and interactive management features.

This widget provides:
1. Visual distinction between dictionary and generated sequences
2. Clickable selection with visual feedback
3. Delete and save-to-dictionary functionality
4. Print-friendly styling (borders only visible on screen, not in print)
"""

from typing import Optional, Any, Callable
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
import logging


class EnhancedSequenceCard(QFrame):
    """
    Enhanced sequence card with visual distinction and interactive features.
    
    Features:
    - Visual distinction between dictionary and generated sequences
    - Clickable selection with border highlighting
    - Delete functionality for generated sequences
    - Save to dictionary functionality for generated sequences
    - Print-friendly styling (screen-only visual indicators)
    """
    
    # Signals for interaction
    card_selected = pyqtSignal(object)  # Emits the card instance
    card_deselected = pyqtSignal(object)
    delete_requested = pyqtSignal(object)  # Emits sequence data
    save_to_dictionary_requested = pyqtSignal(object)  # Emits sequence data
    
    def __init__(
        self, 
        sequence_data: Any,
        is_generated: bool = False,
        card_width: int = 280,
        card_height: int = 350,
        image_width: int = 250,
        image_height: int = 200
    ):
        super().__init__()
        self.sequence_data = sequence_data
        self.is_generated = is_generated
        self.is_selected = False
        
        # Set up the card
        self.setFixedSize(card_width, card_height)
        self.setObjectName("enhancedSequenceCard")
        
        # Make the card clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._setup_ui(image_width, image_height)
        self._apply_styling()
        
    def _setup_ui(self, image_width: int, image_height: int):
        """Set up the card UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Image container with visual distinction
        self.image_container = QFrame()
        self.image_container.setFixedSize(image_width + 10, image_height + 10)
        self.image_container.setObjectName("imageContainer")
        
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setContentsMargins(5, 5, 5, 5)
        
        # Main image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(image_width, image_height)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setObjectName("sequenceImage")
        self.image_label.setStyleSheet("""
            QLabel#sequenceImage {
                background: rgba(240, 240, 240, 0.1);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 4px;
            }
        """)
        
        image_layout.addWidget(self.image_label)
        layout.addWidget(self.image_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Info section
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setObjectName("sequenceInfo")
        layout.addWidget(self.info_label)
        
        # Action buttons (only for generated sequences)
        if self.is_generated:
            self._create_action_buttons(layout)
        
        layout.addStretch()
        
    def _create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons for generated sequences."""
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.setSpacing(5)
        
        # Save to dictionary button
        self.save_button = QPushButton("💾 Save")
        self.save_button.setObjectName("saveButton")
        self.save_button.setToolTip("Save this sequence to your dictionary")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setVisible(False)  # Hidden by default, shown when selected
        
        # Delete button
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setToolTip("Remove this sequence from the page")
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.delete_button.setVisible(False)  # Hidden by default, shown when selected
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addWidget(button_container)
        
    def _apply_styling(self):
        """Apply visual styling based on sequence type."""
        if self.is_generated:
            # Generated sequences get orange/yellow border
            self.setStyleSheet("""
                QFrame#enhancedSequenceCard {
                    background: rgba(255, 255, 255, 0.05);
                    border: 2px solid #FF8C00;  /* Orange border for generated */
                    border-radius: 8px;
                    padding: 5px;
                }
                QFrame#enhancedSequenceCard:hover {
                    background: rgba(255, 140, 0, 0.1);
                    border: 2px solid #FF6600;
                }
                QFrame#imageContainer {
                    border: 1px solid #FF8C00;
                    border-radius: 4px;
                    background: rgba(255, 140, 0, 0.05);
                }
            """)
        else:
            # Dictionary sequences get subtle styling
            self.setStyleSheet("""
                QFrame#enhancedSequenceCard {
                    background: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(200, 200, 200, 0.3);
                    border-radius: 8px;
                    padding: 5px;
                }
                QFrame#enhancedSequenceCard:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(200, 200, 200, 0.5);
                }
                QFrame#imageContainer {
                    border: 1px solid rgba(200, 200, 200, 0.2);
                    border-radius: 4px;
                    background: rgba(255, 255, 255, 0.02);
                }
            """)
            
    def _update_selection_styling(self):
        """Update styling based on selection state."""
        if self.is_selected:
            # Add selection highlight
            selection_style = """
                QFrame#enhancedSequenceCard {
                    border: 3px solid #0078D4 !important;  /* Blue selection border */
                    background: rgba(0, 120, 212, 0.1) !important;
                }
            """
            current_style = self.styleSheet()
            self.setStyleSheet(current_style + selection_style)
            
            # Show action buttons for generated sequences
            if self.is_generated:
                if hasattr(self, 'save_button'):
                    self.save_button.setVisible(True)
                if hasattr(self, 'delete_button'):
                    self.delete_button.setVisible(True)
        else:
            # Remove selection styling and reapply base styling
            self._apply_styling()
            
            # Hide action buttons
            if self.is_generated:
                if hasattr(self, 'save_button'):
                    self.save_button.setVisible(False)
                if hasattr(self, 'delete_button'):
                    self.delete_button.setVisible(False)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_selection()
        super().mousePressEvent(event)
        
    def toggle_selection(self):
        """Toggle the selection state of this card."""
        self.is_selected = not self.is_selected
        self._update_selection_styling()
        
        if self.is_selected:
            self.card_selected.emit(self)
        else:
            self.card_deselected.emit(self)
            
    def set_selected(self, selected: bool):
        """Programmatically set the selection state."""
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_selection_styling()
            
            if selected:
                self.card_selected.emit(self)
            else:
                self.card_deselected.emit(self)
    
    def set_image(self, pixmap: QPixmap):
        """Set the sequence image."""
        if pixmap and not pixmap.isNull():
            # Scale the pixmap to fit the label
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Image not available")
            
    def set_info_text(self, text: str):
        """Set the info text below the image."""
        self.info_label.setText(text)
        
    def _on_save_clicked(self):
        """Handle save to dictionary button click."""
        self.save_to_dictionary_requested.emit(self.sequence_data)
        
    def _on_delete_clicked(self):
        """Handle delete button click."""
        self.delete_requested.emit(self.sequence_data)
        
    def get_print_stylesheet(self) -> str:
        """
        Get stylesheet for printing that removes screen-only visual indicators.
        
        Returns:
            str: CSS stylesheet for print media
        """
        return """
            @media print {
                QFrame#enhancedSequenceCard {
                    border: none !important;
                    background: white !important;
                }
                QFrame#imageContainer {
                    border: none !important;
                    background: white !important;
                }
                QPushButton {
                    display: none !important;
                }
            }
        """
