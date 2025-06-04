"""
Modern Scroll Widget - Drop-in replacement for legacy scroll widget with modern components

MODERNIZATION LOG:
- Date: 2025-01-27
- Changes Made: Created modern scroll widget that integrates seamlessly with existing browse tab
- Performance Impact: Improved performance with modern grid layout and optimized rendering
- Breaking Changes: None (maintains existing API compatibility)
- Migration Notes: Drop-in replacement for SequencePickerScrollWidget
- Visual Changes: Modern grid layout with glassmorphism and smooth animations
"""

import logging
from typing import TYPE_CHECKING, Optional, Dict, List, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import pyqtSignal

from .modern_browse_integration import ModernBrowseIntegration
from .utils.change_logger import modernization_logger

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.sequence_picker.sequence_picker import SequencePicker
    from main_window.main_widget.browse_tab.lazy_loading.browse_tab_lazy_loader import BrowseTabLazyLoader


class ModernScrollWidget(QWidget):
    """
    Modern scroll widget that replaces the legacy SequencePickerScrollWidget.
    
    This widget provides a seamless integration point for modern components
    while maintaining full compatibility with the existing browse tab architecture.
    
    Features:
    - Drop-in replacement for legacy scroll widget
    - Modern grid layout with responsive columns
    - Glassmorphism effects and smooth animations
    - Maintains existing API for compatibility
    - Enhanced performance with optimized rendering
    """
    
    # Signals for compatibility
    thumbnail_clicked = pyqtSignal(str, int)  # word, index
    favorite_toggled = pyqtSignal(str, bool)  # word, is_favorite
    
    def __init__(self, sequence_picker: "SequencePicker"):
        super().__init__(sequence_picker)
        self.sequence_picker = sequence_picker
        self.logger = logging.getLogger(__name__)
        
        # Initialize modern integration
        self.modern_integration = ModernBrowseIntegration(sequence_picker.browse_tab)
        
        # Legacy compatibility properties
        self.thumbnail_boxes: Dict[str, Any] = {}  # Compatibility with legacy code
        self.section_headers: Dict[int, Any] = {}  # Compatibility with legacy code
        
        # Lazy loading support (for compatibility)
        self._lazy_loader: Optional["BrowseTabLazyLoader"] = None
        self._lazy_loading_enabled = False
        
        # Setup
        self._setup_ui()
        self._setup_connections()
        
        self.logger.info("🔄 ModernScrollWidget initialized as legacy replacement")
        
        # Log the modernization
        modernization_logger.log_component_update(
            component_name="ModernScrollWidget",
            changes_made=[
                "Created modern scroll widget replacement",
                "Integrated modern components with legacy API",
                "Maintained full compatibility with existing code",
                "Added modern grid layout and animations"
            ],
            old_version="legacy_scroll_widget",
            new_version="modern_2025_scroll_widget"
        )
    
    def _setup_ui(self):
        """Setup the modern UI."""
        # Set size policy for compatibility
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Initialize modern UI and add to layout
        modern_container = self.modern_integration.initialize_modern_ui(self)
        self.layout.addWidget(modern_container)
        
        # Apply modern styling
        self.setStyleSheet("background: transparent;")
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Connect modern integration signals to legacy signals
        self.modern_integration.thumbnail_clicked.connect(self.thumbnail_clicked.emit)
        self.modern_integration.favorite_toggled.connect(self.favorite_toggled.emit)
        
        # Connect layout changes
        self.modern_integration.layout_updated.connect(self._on_layout_updated)
    
    def _on_layout_updated(self, column_count: int):
        """Handle layout updates."""
        self.logger.debug(f"📐 Modern layout updated to {column_count} columns")
    
    # Legacy API compatibility methods
    def clear_layout(self):
        """Clear the layout (legacy compatibility)."""
        # Clear modern components
        if hasattr(self.modern_integration, 'grid_layout') and self.modern_integration.grid_layout:
            self.modern_integration.grid_layout.clear_items(animate=False)
        
        # Clear legacy references
        self.thumbnail_boxes.clear()
        self.section_headers.clear()
        
        self.logger.debug("🧹 Modern layout cleared")
    
    def add_thumbnail_box(self, word: str, thumbnail_box: Any) -> None:
        """Add a thumbnail box (legacy compatibility)."""
        # Store reference for legacy compatibility
        self.thumbnail_boxes[word] = thumbnail_box
        
        # Extract thumbnails from legacy thumbnail box
        if hasattr(thumbnail_box, 'state') and hasattr(thumbnail_box.state, 'thumbnails'):
            thumbnails = thumbnail_box.state.thumbnails
            
            # Create modern card through integration
            self.modern_integration._create_modern_card(word, thumbnails, animate=True)
            
            self.logger.debug(f"🎴 Added modern card for legacy thumbnail box: {word}")
        
        # Configure lazy loading if enabled (legacy compatibility)
        if self._lazy_loading_enabled and self._lazy_loader:
            if hasattr(thumbnail_box, 'image_label') and hasattr(thumbnail_box.image_label, 'enable_lazy_loading'):
                thumbnail_box.image_label.enable_lazy_loading(self._lazy_loader)
    
    def update_sequences(self, sequences: List[tuple], animate: bool = True):
        """
        Update sequences with modern components.
        
        Args:
            sequences: List of (word, thumbnails, length) tuples
            animate: Whether to animate the update
        """
        # Clear existing content
        self.clear_layout()
        
        # Update through modern integration
        self.modern_integration.update_sequences(sequences, animate)
        
        # Update legacy references for compatibility
        for word, thumbnails, length in sequences:
            # Create mock legacy thumbnail box for compatibility
            class MockThumbnailBox:
                def __init__(self, word, thumbnails):
                    self.word = word
                    self.state = MockState(thumbnails)
                    
                class MockState:
                    def __init__(self, thumbnails):
                        self.thumbnails = thumbnails
                        self.current_index = 0
            
            mock_box = MockThumbnailBox(word, thumbnails)
            self.thumbnail_boxes[word] = mock_box
        
        self.logger.info(f"📋 Updated {len(sequences)} sequences with modern components")
    
    # Lazy loading compatibility methods
    def enable_lazy_loading(self, lazy_loader: "BrowseTabLazyLoader") -> None:
        """Enable lazy loading (legacy compatibility)."""
        self._lazy_loader = lazy_loader
        self._lazy_loading_enabled = True
        
        # Note: Modern components handle their own optimized loading
        # This is maintained for compatibility with existing code
        
        self.logger.info("✅ Lazy loading enabled (compatibility mode)")
    
    def disable_lazy_loading(self) -> None:
        """Disable lazy loading (legacy compatibility)."""
        self._lazy_loading_enabled = False
        self._lazy_loader = None
        
        self.logger.info("✅ Lazy loading disabled (compatibility mode)")
    
    def get_lazy_loading_stats(self) -> dict:
        """Get lazy loading statistics (legacy compatibility)."""
        if not self._lazy_loader:
            return {"lazy_loading_enabled": False}
        
        # Combine legacy stats with modern stats
        modern_stats = self.modern_integration.get_integration_stats()
        
        return {
            "lazy_loading_enabled": self._lazy_loading_enabled,
            "total_thumbnails": len(self.thumbnail_boxes),
            "modern_integration_stats": modern_stats,
            "legacy_compatibility": True
        }
    
    # Sizing and layout methods for compatibility
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        # The modern grid layout handles responsive resizing automatically
        # This maintains compatibility with legacy resize handling
        
        # Calculate scrollbar width for compatibility (though modern components handle this)
        scrollbar_width = self.calculate_scrollbar_width()
        
        # Modern components automatically handle responsive layout
        self.logger.debug(f"📐 Modern scroll widget resized - calculated scrollbar width: {scrollbar_width}")
    
    def calculate_scrollbar_width(self):
        """Calculate scrollbar width (legacy compatibility)."""
        try:
            return self.sequence_picker.main_widget.width() * 0.01
        except:
            return 10  # Fallback width
    
    # Modern component access methods
    def get_modern_card_for_word(self, word: str):
        """Get the modern card for a specific word."""
        return self.modern_integration.get_card_for_word(word)
    
    def set_modern_theme(self, theme_name: str):
        """Set the modern theme."""
        if hasattr(self.modern_integration, 'theme_manager'):
            self.modern_integration.theme_manager.switch_theme(theme_name)
    
    def enable_modern_masonry_layout(self, enable: bool = True):
        """Enable or disable modern masonry layout."""
        self.modern_integration.enable_masonry_layout(enable)
    
    def get_modern_stats(self) -> Dict[str, Any]:
        """Get comprehensive modern component statistics."""
        return self.modern_integration.get_integration_stats()
    
    # Cleanup methods
    def cleanup(self):
        """Clean up modern components."""
        if self.modern_integration:
            self.modern_integration.cleanup()
        
        self.thumbnail_boxes.clear()
        self.section_headers.clear()
        
        self.logger.info("🧹 ModernScrollWidget cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction


# Factory function for easy integration
def create_modern_scroll_widget(sequence_picker: "SequencePicker") -> ModernScrollWidget:
    """
    Factory function to create a modern scroll widget.
    
    This function can be used to easily replace the legacy scroll widget
    in existing code with minimal changes.
    
    Args:
        sequence_picker: The sequence picker instance
        
    Returns:
        ModernScrollWidget instance ready for use
    """
    modern_widget = ModernScrollWidget(sequence_picker)
    
    # Log the creation
    modernization_logger.log_component_update(
        component_name="create_modern_scroll_widget",
        changes_made=["Created modern scroll widget via factory function"],
        new_version="factory_created"
    )
    
    return modern_widget
