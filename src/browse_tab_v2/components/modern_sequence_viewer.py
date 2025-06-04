"""
Modern Sequence Viewer Component - Critical Missing Component Implementation

This component displays selected sequences in the right panel (1/3 width) with:
- Large image display with progressive loading
- Navigation controls for variations
- Action buttons (Edit, Save, Delete, Full Screen)
- Modern glassmorphism styling
- Smooth transitions and animations
- Integration with workbench for editing
"""

import logging
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap

from ..core.interfaces import BrowseTabConfig
from ..core.state import SequenceModel
from .loading_states import LoadingIndicator
from .animation_system import AnimationManager, AnimationType
from .modern_image_display import ModernImageDisplay
from .navigation_controls import NavigationControls
from .modern_action_panel import ModernActionPanel

logger = logging.getLogger(__name__)


class ModernSequenceViewer(QWidget):
    """
    Modern sequence viewer for the right panel of browse tab.

    Features:
    - Large image display with smooth loading
    - Navigation controls for variations
    - Action buttons with modern styling
    - Glassmorphism effects and animations
    - Integration with workbench
    """

    # Signals
    edit_requested = pyqtSignal(str)  # sequence_id
    save_requested = pyqtSignal(str)  # sequence_id
    delete_requested = pyqtSignal(str, int)  # sequence_id, variation_index
    fullscreen_requested = pyqtSignal(str)  # image_path
    variation_changed = pyqtSignal(int)  # new_variation_index

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State
        self.current_sequence: Optional[SequenceModel] = None
        self.current_variation_index: int = 0
        self.variation_paths: List[str] = []

        # Components
        self.image_display: Optional["ModernImageDisplay"] = None
        self.navigation_controls: Optional["NavigationControls"] = None
        self.action_panel: Optional["ModernActionPanel"] = None
        self.metadata_display: Optional["MetadataDisplay"] = None
        self.loading_indicator: Optional[LoadingIndicator] = None

        # Animation system - use pre-initialized global manager if available
        from .animation_system import get_global_animation_manager, AnimationManager

        self.animation_manager = get_global_animation_manager() or AnimationManager()

        # Loading state
        self.is_loading = False

        self._setup_ui()
        self._setup_styling()

        logger.info("ModernSequenceViewer initialized")

    def _setup_ui(self):
        """Setup the sequence viewer UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins
        layout.setSpacing(8)  # Reduced spacing to fit action panel

        # Header with sequence info
        self.header_frame = self._create_header()
        layout.addWidget(self.header_frame)

        # Main content area
        self.content_frame = QFrame()
        self.content_frame.setObjectName("sequenceViewerContent")
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)  # Reduced spacing

        # Image display area
        from .modern_image_display import ModernImageDisplay

        self.image_display = ModernImageDisplay(self.config, self)
        content_layout.addWidget(self.image_display, 1)  # Takes most space

        # Navigation controls
        from .navigation_controls import NavigationControls

        self.navigation_controls = NavigationControls(self)
        self.navigation_controls.previous_requested.connect(self._navigate_previous)
        self.navigation_controls.next_requested.connect(self._navigate_next)
        content_layout.addWidget(self.navigation_controls)

        # Metadata display (compact)
        self.metadata_display = MetadataDisplay(self)
        content_layout.addWidget(self.metadata_display)

        layout.addWidget(self.content_frame, 1)

        # Action buttons panel (reserve adequate space)
        from .modern_action_panel import ModernActionPanel

        self.action_panel = ModernActionPanel(self)
        self.action_panel.edit_requested.connect(self.edit_requested.emit)
        self.action_panel.save_requested.connect(self.save_requested.emit)
        self.action_panel.delete_requested.connect(self._handle_delete_request)
        self.action_panel.fullscreen_requested.connect(self._handle_fullscreen_request)
        layout.addWidget(self.action_panel, 0)  # Fixed size, don't stretch

        # Loading indicator (initially hidden)
        self.loading_indicator = LoadingIndicator(size=64, show_text=True, parent=self)
        self.loading_indicator.hide()

        # Set size policy for right panel
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # Initially show empty state
        self._show_empty_state()

    def _create_header(self) -> QFrame:
        """Create header with sequence title and info."""
        header = QFrame()
        header.setObjectName("sequenceViewerHeader")
        header.setFixedHeight(60)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title label
        self.title_label = QLabel("Select a sequence")
        self.title_label.setObjectName("sequenceTitle")
        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Info label (difficulty, length, etc.)
        self.info_label = QLabel("")
        self.info_label.setObjectName("sequenceInfo")
        font = QFont("Segoe UI", 10)
        self.info_label.setFont(font)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        return header

    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet(
            """
            ModernSequenceViewer {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
            }
            
            QFrame#sequenceViewerHeader {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }
            
            QFrame#sequenceViewerContent {
                background: transparent;
                border: none;
            }
            
            QLabel#sequenceTitle {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                border: none;
            }
            
            QLabel#sequenceInfo {
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
            }
        """
        )

    def display_sequence(self, sequence: SequenceModel, variation_index: int = 0):
        """Display a sequence with smooth transition animation."""
        if not sequence:
            self._show_empty_state()
            return

        logger.info(
            f"Displaying sequence: {sequence.name} (variation {variation_index})"
        )

        # Update state
        self.current_sequence = sequence
        self.current_variation_index = variation_index
        # SequenceModel uses 'thumbnails' attribute, not 'image_paths'
        self.variation_paths = getattr(sequence, "thumbnails", [])

        # Fallback to other possible attributes
        if not self.variation_paths:
            self.variation_paths = getattr(sequence, "image_paths", [])
        if not self.variation_paths and hasattr(sequence, "metadata"):
            # Check if paths are in metadata
            metadata = sequence.metadata or {}
            self.variation_paths = metadata.get(
                "thumbnails", metadata.get("image_paths", [])
            )

        # Update header
        self.title_label.setText(sequence.name)
        info_text = f"Difficulty: {sequence.difficulty} | Length: {sequence.length}"
        if len(self.variation_paths) > 1:
            info_text += (
                f" | Variation {variation_index + 1}/{len(self.variation_paths)}"
            )
        self.info_label.setText(info_text)

        # Update navigation controls
        self.navigation_controls.set_variation_info(
            variation_index, len(self.variation_paths)
        )

        # Load image with animation
        if self.variation_paths and variation_index < len(self.variation_paths):
            image_path = self.variation_paths[variation_index]
            self._load_image_with_animation(image_path)

        # Update metadata
        self.metadata_display.update_metadata(sequence)

        # Enable action buttons and set sequence ID
        self.action_panel.set_sequence_id(sequence.id)
        self.action_panel.set_enabled(True)

        # Show content with fade-in animation
        self._show_content_with_animation()

    def navigate_to_variation(self, index: int):
        """Navigate to specific variation with smooth transition."""
        if not self.current_sequence or not self.variation_paths:
            return

        if 0 <= index < len(self.variation_paths):
            self.current_variation_index = index

            # Update info
            info_text = f"Difficulty: {self.current_sequence.difficulty} | Length: {self.current_sequence.length}"
            info_text += f" | Variation {index + 1}/{len(self.variation_paths)}"
            self.info_label.setText(info_text)

            # Update navigation
            self.navigation_controls.set_variation_info(
                index, len(self.variation_paths)
            )

            # Load new image
            image_path = self.variation_paths[index]
            self._load_image_with_animation(image_path)

            # Emit signal
            self.variation_changed.emit(index)

            logger.debug(f"Navigated to variation {index}")

    def _navigate_previous(self):
        """Navigate to previous variation."""
        if self.current_variation_index > 0:
            self.navigate_to_variation(self.current_variation_index - 1)

    def _navigate_next(self):
        """Navigate to next variation."""
        if self.current_variation_index < len(self.variation_paths) - 1:
            self.navigate_to_variation(self.current_variation_index + 1)

    def _load_image_with_animation(self, image_path: str):
        """Load image with smooth transition animation."""
        if self.image_display:
            self.image_display.load_image_with_transition(image_path)

    def _show_content_with_animation(self):
        """Show content with fade-in animation."""
        if self.config.enable_animations:
            # Fade in the content frame
            fade_id = self.animation_manager.create_fade_animation(
                self.content_frame, AnimationType.FADE_IN, duration=300
            )
            self.animation_manager.start_animation(fade_id)

    def _show_empty_state(self):
        """Show empty state when no sequence is selected."""
        self.title_label.setText("Select a sequence")
        self.info_label.setText("Click on a thumbnail to view sequence details")

        if self.image_display:
            self.image_display.show_empty_state()

        if self.navigation_controls:
            self.navigation_controls.set_enabled(False)

        if self.action_panel:
            self.action_panel.set_enabled(False)

        if self.metadata_display:
            self.metadata_display.clear()

    def _handle_delete_request(self):
        """Handle delete variation request."""
        if self.current_sequence:
            self.delete_requested.emit(
                self.current_sequence.id, self.current_variation_index
            )

    def _handle_fullscreen_request(self):
        """Handle fullscreen view request."""
        if self.variation_paths and self.current_variation_index < len(
            self.variation_paths
        ):
            image_path = self.variation_paths[self.current_variation_index]
            self.fullscreen_requested.emit(image_path)

    def clear(self):
        """Clear the sequence viewer."""
        self.current_sequence = None
        self.current_variation_index = 0
        self.variation_paths = []
        self._show_empty_state()


class MetadataDisplay(QWidget):
    """Simple metadata display for sequence information."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup metadata display UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        self.metadata_label = QLabel("")
        self.metadata_label.setObjectName("metadataLabel")
        font = QFont("Segoe UI", 9)
        self.metadata_label.setFont(font)
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.metadata_label)

        self.setStyleSheet(
            """
            QLabel#metadataLabel {
                color: rgba(255, 255, 255, 0.6);
                background: transparent;
                border: none;
            }
        """
        )

    def update_metadata(self, sequence: SequenceModel):
        """Update metadata display."""
        metadata_text = f"Created: {getattr(sequence, 'created_date', 'Unknown')}"
        if hasattr(sequence, "tags") and sequence.tags:
            try:
                # Handle both list and non-list tags
                if isinstance(sequence.tags, (list, tuple)):
                    metadata_text += f" | Tags: {', '.join(sequence.tags)}"
                else:
                    metadata_text += f" | Tags: {sequence.tags}"
            except (TypeError, AttributeError):
                # Skip tags if there's an error
                pass
        self.metadata_label.setText(metadata_text)

    def clear(self):
        """Clear metadata display."""
        self.metadata_label.setText("")
