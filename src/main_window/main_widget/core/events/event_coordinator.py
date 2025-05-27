"""
Event Coordinator - Manages all signal connections and event forwarding.

This coordinator extracts event handling logic from MainWidgetCoordinator
following the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tab_manager import TabManager
    from ..widget_manager import WidgetManager
    from ..state_manager import StateManager
    from ..image_drag_drop_handler import ImageDragDropHandler


class EventCoordinator:
    """
    Manages all signal connections and event forwarding.
    
    Responsibilities:
    - Connect signals between components
    - Handle event forwarding/delegation
    - Manage event-driven communication
    - Coordinate navigation highlighting updates
    """
    
    def __init__(
        self,
        coordinator: "MainWidgetCoordinator",
        tab_manager: "TabManager",
        widget_manager: "WidgetManager",
        state_manager: "StateManager",
        image_drag_drop_handler: "ImageDragDropHandler"
    ):
        self.coordinator = coordinator
        self.tab_manager = tab_manager
        self.widget_manager = widget_manager
        self.state_manager = state_manager
        self.image_drag_drop_handler = image_drag_drop_handler
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("EventCoordinator initialized")
    
    def connect_all_signals(self) -> None:
        """Connect all signals between components."""
        self.logger.debug("Connecting all signals")
        
        self._connect_manager_signals()
        self._connect_image_drop_signals()
        
        self.logger.debug("All signals connected")
    
    def _connect_manager_signals(self) -> None:
        """Connect signals between managers."""
        # Tab manager signals
        self.tab_manager.tab_changed.connect(self.handle_tab_changed)
        
        # Widget manager signals
        self.widget_manager.widget_ready.connect(self.handle_widget_ready)
        
        # State manager signals
        self.state_manager.state_changed.connect(self.coordinator.state_changed.emit)
    
    def _connect_image_drop_signals(self) -> None:
        """Connect image drag and drop signals."""
        self.image_drag_drop_handler.image_dropped.connect(self.handle_image_dropped)
        self.image_drag_drop_handler.images_dropped.connect(self.handle_images_dropped)
        self.image_drag_drop_handler.drop_error.connect(self.handle_drop_error)
    
    def handle_tab_changed(self, tab_name: str) -> None:
        """Handle tab change events."""
        self.logger.debug(f"Handling tab change to: {tab_name}")
        
        # Update state
        self.state_manager.set_current_tab(tab_name)
        
        # Update widget visibility
        self.widget_manager.update_for_tab(tab_name)
        
        # Update layout for the new tab
        if hasattr(self.coordinator, 'layout_coordinator'):
            self.coordinator.layout_coordinator.update_layout_for_tab(tab_name)
        
        # Update navigation widget highlighting
        self.update_navigation_highlighting(tab_name)
        
        # Emit signal for external listeners
        self.coordinator.tab_changed.emit(tab_name)
        
        self.logger.debug(f"Tab change handling completed for: {tab_name}")
    
    def update_navigation_highlighting(self, tab_name: str) -> None:
        """Update the navigation widget to highlight the correct tab."""
        try:
            # Get the menu bar widget
            menu_bar = self.widget_manager.get_widget("menu_bar")
            if menu_bar and hasattr(menu_bar, "navigation_widget"):
                navigation_widget = menu_bar.navigation_widget
                if hasattr(navigation_widget, "on_tab_changed_programmatically"):
                    navigation_widget.on_tab_changed_programmatically(tab_name)
                    self.logger.debug(f"Navigation highlighting updated for: {tab_name}")
                else:
                    self.logger.warning(
                        "Navigation widget does not have on_tab_changed_programmatically method"
                    )
            else:
                self.logger.warning(
                    "Menu bar or navigation widget not available for highlighting update"
                )
        except Exception as e:
            self.logger.error(f"Failed to update navigation highlighting: {e}")
    
    def handle_widget_ready(self, widget_name: str) -> None:
        """Handle widget ready events."""
        self.logger.debug(f"Handling widget ready: {widget_name}")
        
        # Update tab manager when widgets are ready
        self.tab_manager.on_widget_ready(widget_name)
        
        self.logger.debug(f"Widget ready handling completed for: {widget_name}")
    
    def handle_image_dropped(self, image_path: str) -> None:
        """Handle single image drop events."""
        self.logger.info(f"Single image dropped: {image_path}")
        # Additional handling can be added here if needed
    
    def handle_images_dropped(self, image_paths: list) -> None:
        """Handle multiple images drop events."""
        self.logger.info(f"Multiple images dropped: {len(image_paths)} files")
        # Additional handling can be added here if needed
    
    def handle_drop_error(self, error_message: str) -> None:
        """Handle drag and drop errors."""
        self.logger.error(f"Drag and drop error: {error_message}")
        # Additional error handling can be added here if needed
    
    def disconnect_all_signals(self) -> None:
        """Disconnect all signals for cleanup."""
        self.logger.debug("Disconnecting all signals")
        
        try:
            # Disconnect manager signals
            self.tab_manager.tab_changed.disconnect()
            self.widget_manager.widget_ready.disconnect()
            self.state_manager.state_changed.disconnect()
            
            # Disconnect image drop signals
            self.image_drag_drop_handler.image_dropped.disconnect()
            self.image_drag_drop_handler.images_dropped.disconnect()
            self.image_drag_drop_handler.drop_error.disconnect()
            
            self.logger.debug("All signals disconnected")
        except Exception as e:
            self.logger.warning(f"Error disconnecting signals: {e}")
    
    def get_connection_status(self) -> dict:
        """
        Get status of signal connections for debugging.
        
        Returns:
            Dictionary with connection status information
        """
        return {
            "tab_manager_connected": self.tab_manager.tab_changed.receivers() > 0,
            "widget_manager_connected": self.widget_manager.widget_ready.receivers() > 0,
            "state_manager_connected": self.state_manager.state_changed.receivers() > 0,
            "image_drop_connected": self.image_drag_drop_handler.image_dropped.receivers() > 0,
        }
