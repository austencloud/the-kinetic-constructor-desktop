"""
Enhanced page renderer that creates enhanced sequence cards with visual distinction.

This renderer extends the basic page renderer to create enhanced sequence cards
that support visual distinction between dictionary and generated sequences,
interactive selection, and management features.
"""

from typing import TYPE_CHECKING, List, Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import logging

from .page_renderer import PageRenderer
from .enhanced_sequence_card import EnhancedSequenceCard

if TYPE_CHECKING:
    from ..pages.printable_factory import PrintablePageFactory
    from .layout_calculator import LayoutCalculator
    from .sequence_display_manager import DisplayConfig
    from .sequence_card_selection_manager import SequenceCardSelectionManager


class EnhancedPageRenderer(PageRenderer):
    """
    Enhanced page renderer that creates enhanced sequence cards with visual distinction.
    
    This renderer creates EnhancedSequenceCard widgets instead of simple QLabel widgets,
    providing visual distinction between dictionary and generated sequences, interactive
    selection capabilities, and management features.
    """
    
    def __init__(
        self,
        page_factory: "PrintablePageFactory",
        layout_calculator: "LayoutCalculator", 
        config: "DisplayConfig",
        preview_grid=None,
        selection_manager: Optional["SequenceCardSelectionManager"] = None,
    ):
        super().__init__(page_factory, layout_calculator, config, preview_grid)
        self.selection_manager = selection_manager
        self.logger = logging.getLogger(__name__)
        
    def set_selection_manager(self, selection_manager: "SequenceCardSelectionManager"):
        """Set the selection manager for enhanced sequence cards."""
        self.selection_manager = selection_manager
        
    def create_enhanced_sequence_card(
        self, 
        sequence_data: Dict[str, Any], 
        pixmap: QPixmap
    ) -> EnhancedSequenceCard:
        """
        Create an enhanced sequence card with visual distinction and interactive features.
        
        Args:
            sequence_data: The sequence data dictionary
            pixmap: The sequence image
            
        Returns:
            EnhancedSequenceCard: Enhanced card widget with visual distinction
        """
        try:
            # Determine if this is a generated sequence
            metadata = sequence_data.get("metadata", {})
            is_generated = metadata.get("is_generated", False)
            
            # Calculate card dimensions based on the page scale factor
            scale_factor = self.layout_calculator.calculate_scale_factor(
                pixmap.size(), 
                self.layout_calculator.calculate_optimal_page_size()
            )
            
            # Create the enhanced sequence card
            card = EnhancedSequenceCard(
                sequence_data=sequence_data,
                is_generated=is_generated,
                card_width=int(280 * scale_factor),
                card_height=int(350 * scale_factor),
                image_width=int(250 * scale_factor),
                image_height=int(200 * scale_factor)
            )
            
            # Set the image
            card.set_image(pixmap)
            
            # Set info text
            word = sequence_data.get("word", "Unknown")
            length = metadata.get("sequence_length", metadata.get("length", 0))
            level = metadata.get("sequence_level", metadata.get("level", 1))
            
            if is_generated:
                generation_mode = metadata.get("generation_mode", "Unknown")
                info_text = (
                    f"<b>{word}</b><br>"
                    f"Length: {length} beats<br>"
                    f"Level: {level}<br>"
                    f"Mode: {generation_mode.title()}<br>"
                    f"<span style='color: #FF8C00;'>🔄 Generated</span>"
                )
            else:
                info_text = (
                    f"<b>{word}</b><br>"
                    f"Length: {length} beats<br>"
                    f"Level: {level}<br>"
                    f"<span style='color: #4CAF50;'>📚 Dictionary</span>"
                )
                
            card.set_info_text(info_text)
            
            # Register with selection manager if available
            if self.selection_manager:
                self.selection_manager.register_card(card)
                
            self.logger.debug(
                f"Created enhanced sequence card for {word} "
                f"(generated: {is_generated}, scale: {scale_factor:.2f})"
            )
            
            return card
            
        except Exception as e:
            self.logger.error(f"Error creating enhanced sequence card: {e}")
            # Fallback to basic card creation
            return self._create_fallback_card(sequence_data, pixmap)
    
    def _create_fallback_card(
        self, 
        sequence_data: Dict[str, Any], 
        pixmap: QPixmap
    ) -> EnhancedSequenceCard:
        """Create a basic enhanced sequence card as fallback."""
        try:
            card = EnhancedSequenceCard(
                sequence_data=sequence_data,
                is_generated=False,  # Default to dictionary
                card_width=280,
                card_height=350,
                image_width=250,
                image_height=200
            )
            card.set_image(pixmap)
            card.set_info_text("Sequence Card")
            return card
        except Exception as e:
            self.logger.error(f"Error creating fallback card: {e}")
            # Return a minimal card
            return EnhancedSequenceCard(sequence_data, False)
    
    def create_image_label(self, sequence_data: Dict[str, Any], pixmap: QPixmap) -> QWidget:
        """
        Override the base method to create enhanced sequence cards instead of simple labels.
        
        This method maintains compatibility with the existing page management system
        while providing enhanced functionality.
        
        Args:
            sequence_data: The sequence data dictionary
            pixmap: The sequence image
            
        Returns:
            QWidget: Enhanced sequence card widget
        """
        return self.create_enhanced_sequence_card(sequence_data, pixmap)
    
    def clear_pages(self) -> None:
        """Clear all pages and unregister cards from selection manager."""
        # Unregister all cards from selection manager
        if self.selection_manager:
            self.selection_manager.clear_all_cards()
            
        # Call parent clear method
        super().clear_pages()
        
    def add_card_to_current_page(self, card: EnhancedSequenceCard) -> bool:
        """
        Add an enhanced sequence card to the current page.
        
        Args:
            card: The enhanced sequence card to add
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            # Get the current page
            if not self.pages:
                self.create_new_page()
                
            current_page = self.pages[-1]
            page_layout = current_page.layout()
            
            if not isinstance(page_layout, QGridLayout):
                self.logger.error("Current page does not have a QGridLayout")
                return False
                
            # Calculate position in grid
            current_items = page_layout.count()
            grid_positions = self.page_factory.get_grid_positions()
            
            if current_items >= len(grid_positions):
                # Page is full, create a new one
                self.create_new_page()
                current_page = self.pages[-1]
                page_layout = current_page.layout()
                current_items = 0
                
            # Get the position for this item
            if current_items < len(grid_positions):
                row, col = grid_positions[current_items]
                page_layout.addWidget(card, row, col)
                
                self.logger.debug(
                    f"Added enhanced card to page {len(self.pages)} at position ({row}, {col})"
                )
                return True
            else:
                self.logger.error(f"No available position for card on page {len(self.pages)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding card to current page: {e}")
            return False
    
    def get_enhanced_cards_on_page(self, page_index: int) -> List[EnhancedSequenceCard]:
        """
        Get all enhanced sequence cards on a specific page.
        
        Args:
            page_index: Index of the page
            
        Returns:
            List[EnhancedSequenceCard]: List of enhanced cards on the page
        """
        cards = []
        
        try:
            if 0 <= page_index < len(self.pages):
                page = self.pages[page_index]
                layout = page.layout()
                
                if isinstance(layout, QGridLayout):
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, EnhancedSequenceCard):
                                cards.append(widget)
                                
        except Exception as e:
            self.logger.error(f"Error getting enhanced cards on page {page_index}: {e}")
            
        return cards
    
    def get_all_enhanced_cards(self) -> List[EnhancedSequenceCard]:
        """Get all enhanced sequence cards across all pages."""
        all_cards = []
        
        for page_index in range(len(self.pages)):
            cards = self.get_enhanced_cards_on_page(page_index)
            all_cards.extend(cards)
            
        return all_cards
