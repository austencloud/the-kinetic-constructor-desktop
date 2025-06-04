"""
Sequence Viewer Component - Modular Architecture

Extracted from browse_tab_view.py to provide focused sequence viewing functionality.
Handles sequence display, viewer integration, and sequence-related operations.

Responsibilities:
- Sequence viewer integration and management
- Sequence display and navigation
- Edit/save/delete operation coordination
- Fullscreen image viewing
- Sequence data conversion for workbench
"""

import logging
from typing import Optional, Dict, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.interfaces import SequenceModel, BrowseTabConfig
from ..debug.window_resize_tracker import track_component, log_main_window_change
from .modern_sequence_viewer import ModernSequenceViewer

logger = logging.getLogger(__name__)


class SequenceViewerComponent(QWidget):
    """
    Modular sequence viewer component handling sequence display and operations.
    
    This component encapsulates all sequence viewer related operations and provides
    a clean interface for the main view to interact with sequence viewing features.
    """
    
    # Signals for parent coordination
    edit_requested = pyqtSignal(str)  # sequence_id
    save_requested = pyqtSignal(str)  # sequence_id
    delete_requested = pyqtSignal(str)  # sequence_id
    fullscreen_requested = pyqtSignal(str)  # image_path
    
    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)
        
        self.config = config or BrowseTabConfig()
        
        # State management
        self._current_sequence: Optional[SequenceModel] = None
        self._current_variation_index = 0
        
        # UI components
        self.sequence_viewer: Optional[ModernSequenceViewer] = None
        
        # Performance tracking
        self._last_size = (0, 0)
        
        track_component("SequenceViewerComponent_Initial", self, "Constructor start")
        log_main_window_change("SequenceViewerComponent constructor start")
        
        self._setup_ui()
        self._connect_signals()
        
        track_component("SequenceViewerComponent_Complete", self, "Constructor complete")
        log_main_window_change("SequenceViewerComponent constructor complete")
        logger.info("SequenceViewerComponent initialized")
    
    def _setup_ui(self):
        """Setup the sequence viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create sequence viewer for right panel (1/3 width)
        track_component("SequenceViewerComponent_BeforeViewer", self, "Before creating ModernSequenceViewer")
        
        self.sequence_viewer = ModernSequenceViewer(self.config, self)
        
        track_component("SequenceViewerComponent_AfterViewer", self, "After creating ModernSequenceViewer")
        
        layout.addWidget(self.sequence_viewer)
        
        # Set responsive size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Expanding,  # Allow vertical expansion
        )
        
        track_component("SequenceViewerComponent_SizeIsolation", self, "Complete size isolation applied")
        log_main_window_change("After SequenceViewerComponent size isolation applied")
    
    def _connect_signals(self):
        """Connect ModernSequenceViewer signals to component signals."""
        if self.sequence_viewer:
            self.sequence_viewer.edit_requested.connect(self._on_edit_requested)
            self.sequence_viewer.save_requested.connect(self._on_save_requested)
            self.sequence_viewer.delete_requested.connect(self._on_delete_requested)
            self.sequence_viewer.fullscreen_requested.connect(self._on_fullscreen_requested)
    
    def _on_edit_requested(self, sequence_id: str):
        """Handle edit request from sequence viewer."""
        logger.info(f"Edit requested for sequence: {sequence_id}")
        self.edit_requested.emit(sequence_id)
    
    def _on_save_requested(self, sequence_id: str):
        """Handle save request from sequence viewer."""
        logger.info(f"Save requested for sequence: {sequence_id}")
        self.save_requested.emit(sequence_id)
    
    def _on_delete_requested(self):
        """Handle delete request from sequence viewer."""
        if self.sequence_viewer and self.sequence_viewer.current_sequence:
            sequence_id = self.sequence_viewer.current_sequence.id
            logger.info(f"Delete requested for sequence: {sequence_id}")
            self.delete_requested.emit(sequence_id)
    
    def _on_fullscreen_requested(self, image_path: str):
        """Handle fullscreen request from sequence viewer."""
        logger.info(f"Fullscreen requested for image: {image_path}")
        self.fullscreen_requested.emit(image_path)
    
    # Public interface methods
    def display_sequence(self, sequence: SequenceModel, variation_index: int = 0):
        """Display a sequence in the viewer."""
        self._current_sequence = sequence
        self._current_variation_index = variation_index
        
        if self.sequence_viewer:
            self.sequence_viewer.display_sequence(sequence, variation_index)
            logger.info(f"Displayed sequence {sequence.id} in viewer")
    
    def clear_sequence(self):
        """Clear the current sequence from the viewer."""
        self._current_sequence = None
        self._current_variation_index = 0
        
        if self.sequence_viewer:
            self.sequence_viewer.clear_sequence()
    
    def get_current_sequence(self) -> Optional[SequenceModel]:
        """Get the currently displayed sequence."""
        return self._current_sequence
    
    def get_current_variation_index(self) -> int:
        """Get the current variation index."""
        return self._current_variation_index
    
    def convert_sequence_for_workbench(self, sequence: SequenceModel) -> list:
        """Convert SequenceModel to workbench format."""
        try:
            # Try to get sequence data from metadata first
            if hasattr(sequence, "metadata") and sequence.metadata:
                if "sequence_data" in sequence.metadata:
                    return sequence.metadata["sequence_data"]
                elif "beats" in sequence.metadata:
                    return sequence.metadata["beats"]
            
            # Try direct attributes
            if hasattr(sequence, "beats") and sequence.beats:
                return sequence.beats
            elif hasattr(sequence, "sequence_data") and sequence.sequence_data:
                return sequence.sequence_data
            else:
                logger.warning(f"No sequence data found for {sequence.name}")
                return []
        
        except Exception as e:
            logger.error(f"Failed to convert sequence for workbench: {e}")
            return []
    
    def load_sequence_to_workbench(self, sequence_id: str, sequences: List[SequenceModel]):
        """Load sequence into the main workbench for editing."""
        try:
            # Find the sequence in provided sequences
            sequence = None
            for seq in sequences:
                if seq.id == sequence_id:
                    sequence = seq
                    break
            
            if sequence:
                # Get main widget reference to load sequence
                from src.settings_manager.global_settings.app_context import AppContext
                
                try:
                    main_window = AppContext.main_window()
                except Exception as e:
                    logger.error(f"Failed to get main window: {e}")
                    main_window = None
                
                if main_window:
                    if hasattr(main_window, "main_widget"):
                        main_widget = main_window.main_widget
                        
                        # Load sequence into workbench
                        if hasattr(main_widget, "sequence_workbench"):
                            workbench = main_widget.sequence_workbench
                            # Convert sequence model to workbench format
                            sequence_data = self.convert_sequence_for_workbench(sequence)
                            workbench.load_sequence(sequence_data)
                            
                            logger.info(f"Loaded sequence {sequence_id} into workbench")
                        else:
                            logger.warning("Sequence workbench not found")
                    else:
                        logger.warning("Main widget not found")
                else:
                    logger.warning("Main window not available")
            else:
                logger.warning(f"Sequence {sequence_id} not found")
        
        except Exception as e:
            logger.error(f"Failed to load sequence to workbench: {e}")
    
    def find_sequence_by_id(self, sequence_id: str, sequences: List[SequenceModel]) -> Optional[SequenceModel]:
        """Find sequence by ID in provided sequences."""
        for sequence in sequences:
            if hasattr(sequence, "id") and sequence.id == sequence_id:
                return sequence
        return None
    
    def sizeHint(self):
        """Provide size hint for responsive layout."""
        from PyQt6.QtCore import QSize
        return QSize(600, 800)  # 1/3 width panel
    
    def minimumSizeHint(self):
        """Provide minimum size hint."""
        from PyQt6.QtCore import QSize
        return QSize(300, 400)
    
    def hasHeightForWidth(self):
        """Disable height-for-width calculations."""
        return False
