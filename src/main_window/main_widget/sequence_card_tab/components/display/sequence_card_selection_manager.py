"""
Selection manager for enhanced sequence cards with interactive management features.

This manager handles:
1. Multiple card selection state
2. Bulk operations (delete multiple, save multiple)
3. Keyboard shortcuts (Delete key, Ctrl+S)
4. Selection visual feedback coordination
5. Integration with page layout and reflow system
"""

from typing import List, Set, Optional, Any, Callable
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent
import logging

from .enhanced_sequence_card import EnhancedSequenceCard


class SequenceCardSelectionManager(QObject):
    """
    Manages selection state and interactions for enhanced sequence cards.
    
    Features:
    - Multiple card selection
    - Bulk operations (delete, save to dictionary)
    - Keyboard shortcuts
    - Selection state coordination
    - Integration with page reflow system
    """
    
    # Signals for bulk operations
    bulk_delete_requested = pyqtSignal(list)  # List of sequence data
    bulk_save_requested = pyqtSignal(list)    # List of sequence data
    selection_changed = pyqtSignal(int)       # Number of selected cards
    
    def __init__(self, parent_widget: QWidget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.selected_cards: Set[EnhancedSequenceCard] = set()
        self.all_cards: List[EnhancedSequenceCard] = []
        
        # Set up keyboard event handling
        self.parent_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.parent_widget.keyPressEvent = self._handle_key_press
        
        self.logger = logging.getLogger(__name__)
        
    def register_card(self, card: EnhancedSequenceCard):
        """Register a new card with the selection manager."""
        if card not in self.all_cards:
            self.all_cards.append(card)
            
            # Connect card signals
            card.card_selected.connect(self._on_card_selected)
            card.card_deselected.connect(self._on_card_deselected)
            card.delete_requested.connect(self._on_single_delete_requested)
            card.save_to_dictionary_requested.connect(self._on_single_save_requested)
            
            self.logger.debug(f"Registered card for sequence: {getattr(card.sequence_data, 'id', 'unknown')}")
    
    def unregister_card(self, card: EnhancedSequenceCard):
        """Unregister a card from the selection manager."""
        if card in self.all_cards:
            self.all_cards.remove(card)
            
        if card in self.selected_cards:
            self.selected_cards.remove(card)
            self._emit_selection_changed()
            
        # Disconnect signals
        try:
            card.card_selected.disconnect(self._on_card_selected)
            card.card_deselected.disconnect(self._on_card_deselected)
            card.delete_requested.disconnect(self._on_single_delete_requested)
            card.save_to_dictionary_requested.disconnect(self._on_single_save_requested)
        except TypeError:
            # Signals might already be disconnected
            pass
            
        self.logger.debug(f"Unregistered card for sequence: {getattr(card.sequence_data, 'id', 'unknown')}")
    
    def clear_all_cards(self):
        """Clear all registered cards."""
        for card in self.all_cards.copy():
            self.unregister_card(card)
        
        self.all_cards.clear()
        self.selected_cards.clear()
        self._emit_selection_changed()
        
    def _on_card_selected(self, card: EnhancedSequenceCard):
        """Handle when a card is selected."""
        self.selected_cards.add(card)
        self._emit_selection_changed()
        self.logger.debug(f"Card selected. Total selected: {len(self.selected_cards)}")
        
    def _on_card_deselected(self, card: EnhancedSequenceCard):
        """Handle when a card is deselected."""
        self.selected_cards.discard(card)
        self._emit_selection_changed()
        self.logger.debug(f"Card deselected. Total selected: {len(self.selected_cards)}")
        
    def _emit_selection_changed(self):
        """Emit selection changed signal with current count."""
        self.selection_changed.emit(len(self.selected_cards))
        
    def select_all(self):
        """Select all cards."""
        for card in self.all_cards:
            if not card.is_selected:
                card.set_selected(True)
                
    def deselect_all(self):
        """Deselect all cards."""
        for card in self.selected_cards.copy():
            card.set_selected(False)
            
    def select_generated_only(self):
        """Select only generated sequences."""
        self.deselect_all()
        for card in self.all_cards:
            if card.is_generated and not card.is_selected:
                card.set_selected(True)
                
    def get_selected_sequence_data(self) -> List[Any]:
        """Get sequence data for all selected cards."""
        return [card.sequence_data for card in self.selected_cards]
        
    def get_selected_generated_data(self) -> List[Any]:
        """Get sequence data for selected generated sequences only."""
        return [
            card.sequence_data 
            for card in self.selected_cards 
            if card.is_generated
        ]
        
    def _on_single_delete_requested(self, sequence_data: Any):
        """Handle delete request for a single sequence."""
        self.bulk_delete_requested.emit([sequence_data])
        
    def _on_single_save_requested(self, sequence_data: Any):
        """Handle save request for a single sequence."""
        self.bulk_save_requested.emit([sequence_data])
        
    def delete_selected(self):
        """Delete all selected sequences."""
        if not self.selected_cards:
            return
            
        # Only delete generated sequences
        generated_data = self.get_selected_generated_data()
        if generated_data:
            self.bulk_delete_requested.emit(generated_data)
            self.logger.info(f"Requested deletion of {len(generated_data)} selected generated sequences")
        
    def save_selected_to_dictionary(self):
        """Save all selected generated sequences to dictionary."""
        generated_data = self.get_selected_generated_data()
        if generated_data:
            self.bulk_save_requested.emit(generated_data)
            self.logger.info(f"Requested saving {len(generated_data)} selected generated sequences to dictionary")
            
    def _handle_key_press(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Delete:
            # Delete selected sequences
            self.delete_selected()
            event.accept()
            
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+S: Save selected to dictionary
            self.save_selected_to_dictionary()
            event.accept()
            
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+A: Select all
            self.select_all()
            event.accept()
            
        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+D: Deselect all
            self.deselect_all()
            event.accept()
            
        elif event.key() == Qt.Key.Key_G and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+G: Select generated only
            self.select_generated_only()
            event.accept()
            
        else:
            # Call the original keyPressEvent if it exists
            if hasattr(self.parent_widget, '_original_keyPressEvent'):
                self.parent_widget._original_keyPressEvent(event)
            else:
                super(QWidget, self.parent_widget).keyPressEvent(event)
                
    def get_selection_summary(self) -> dict:
        """Get a summary of current selection."""
        total_selected = len(self.selected_cards)
        generated_selected = len(self.get_selected_generated_data())
        dictionary_selected = total_selected - generated_selected
        
        return {
            'total_selected': total_selected,
            'generated_selected': generated_selected,
            'dictionary_selected': dictionary_selected,
            'can_delete': generated_selected > 0,
            'can_save': generated_selected > 0
        }
        
    def update_card_type(self, card: EnhancedSequenceCard, is_generated: bool):
        """Update a card's type (e.g., when a generated sequence is saved to dictionary)."""
        if card.is_generated != is_generated:
            card.is_generated = is_generated
            card._apply_styling()
            
            # If the card was selected and is no longer generated, update action buttons
            if card.is_selected:
                card._update_selection_styling()
                
            self.logger.debug(
                f"Updated card type: {getattr(card.sequence_data, 'id', 'unknown')} "
                f"is_generated={is_generated}"
            )
