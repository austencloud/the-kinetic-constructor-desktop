"""
Widget Access Facade - Provides clean, organized access to widgets and services.

This facade centralizes widget access patterns and provides type-safe access
following the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from ..widget_manager import WidgetManager
    from ..tab_manager import TabManager


class WidgetAccessFacade:
    """
    Provides clean, organized access to widgets and services.
    
    Responsibilities:
    - Centralize widget access patterns
    - Provide type-safe widget access
    - Abstract away widget location details
    - Provide convenience methods for common operations
    """
    
    def __init__(self, widget_manager: "WidgetManager", tab_manager: "TabManager"):
        self.widget_manager = widget_manager
        self.tab_manager = tab_manager
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("WidgetAccessFacade initialized")
    
    def get_widget(self, widget_name: str) -> Optional[QWidget]:
        """
        Get a specific widget by name.
        
        Args:
            widget_name: Name of the widget to retrieve
            
        Returns:
            Widget instance or None if not found
        """
        widget = self.widget_manager.get_widget(widget_name)
        if not widget:
            self.logger.warning(f"Widget '{widget_name}' not found")
        return widget
    
    def get_tab_widget(self, tab_name: str) -> Optional[QWidget]:
        """
        Get a specific tab widget by name.
        
        Args:
            tab_name: Name of the tab to retrieve
            
        Returns:
            Tab widget instance or None if not found
        """
        tab_widget = self.tab_manager.get_tab_widget(tab_name)
        if not tab_widget:
            self.logger.warning(f"Tab widget '{tab_name}' not found")
        return tab_widget
    
    def show_settings_dialog(self) -> bool:
        """
        Show the settings dialog.
        
        Returns:
            True if dialog was shown, False if not available
        """
        settings_dialog = self.get_widget("settings_dialog")
        if settings_dialog and hasattr(settings_dialog, "show"):
            settings_dialog.show()
            self.logger.debug("Settings dialog shown")
            return True
        else:
            self.logger.warning("Settings dialog not available or cannot be shown")
            return False
    
    def show_full_screen_overlay(self, image_data) -> bool:
        """
        Show the full screen image overlay.
        
        Args:
            image_data: Image data to display
            
        Returns:
            True if overlay was shown, False if not available
        """
        overlay = self.get_widget("full_screen_overlay")
        if overlay and hasattr(overlay, "show_image"):
            overlay.show_image(image_data)
            self.logger.debug("Full screen overlay shown")
            return True
        else:
            self.logger.warning("Full screen overlay not available or cannot show image")
            return False
    
    def get_construct_tab(self) -> Optional[QWidget]:
        """
        Get the construct tab widget.
        
        Returns:
            Construct tab widget or None if not found
        """
        return self.get_tab_widget("construct")
    
    def get_learn_tab(self) -> Optional[QWidget]:
        """
        Get the learn tab widget.
        
        Returns:
            Learn tab widget or None if not found
        """
        return self.get_tab_widget("learn")
    
    def get_browse_tab(self) -> Optional[QWidget]:
        """
        Get the browse tab widget.
        
        Returns:
            Browse tab widget or None if not found
        """
        return self.get_tab_widget("browse")
    
    def get_sequence_card_tab(self) -> Optional[QWidget]:
        """
        Get the sequence card tab widget.
        
        Returns:
            Sequence card tab widget or None if not found
        """
        return self.get_tab_widget("sequence_card")
    
    def get_menu_bar(self) -> Optional[QWidget]:
        """
        Get the menu bar widget.
        
        Returns:
            Menu bar widget or None if not found
        """
        return self.get_widget("menu_bar")
    
    def get_fade_manager(self) -> Optional[QWidget]:
        """
        Get the fade manager widget.
        
        Returns:
            Fade manager widget or None if not found
        """
        return self.get_widget("fade_manager")
    
    def get_sequence_workbench(self) -> Optional[QWidget]:
        """
        Get the sequence workbench widget.
        
        Returns:
            Sequence workbench widget or None if not found
        """
        return self.get_widget("sequence_workbench")
    
    def is_widget_available(self, widget_name: str) -> bool:
        """
        Check if a widget is available.
        
        Args:
            widget_name: Name of the widget to check
            
        Returns:
            True if widget is available, False otherwise
        """
        return self.get_widget(widget_name) is not None
    
    def is_tab_available(self, tab_name: str) -> bool:
        """
        Check if a tab is available.
        
        Args:
            tab_name: Name of the tab to check
            
        Returns:
            True if tab is available, False otherwise
        """
        return self.get_tab_widget(tab_name) is not None
    
    def get_available_widgets(self) -> list:
        """
        Get list of available widget names.
        
        Returns:
            List of available widget names
        """
        # This would need to be implemented in WidgetManager
        if hasattr(self.widget_manager, "get_available_widgets"):
            return self.widget_manager.get_available_widgets()
        else:
            self.logger.warning("WidgetManager does not support listing available widgets")
            return []
    
    def get_available_tabs(self) -> list:
        """
        Get list of available tab names.
        
        Returns:
            List of available tab names
        """
        # This would need to be implemented in TabManager
        if hasattr(self.tab_manager, "get_available_tabs"):
            return self.tab_manager.get_available_tabs()
        else:
            self.logger.warning("TabManager does not support listing available tabs")
            return []
    
    def get_widget_status(self) -> dict:
        """
        Get status of commonly used widgets.
        
        Returns:
            Dictionary with widget availability status
        """
        common_widgets = [
            "menu_bar", "settings_dialog", "full_screen_overlay",
            "fade_manager", "sequence_workbench"
        ]
        
        common_tabs = [
            "construct", "learn", "browse", "sequence_card"
        ]
        
        status = {
            "widgets": {name: self.is_widget_available(name) for name in common_widgets},
            "tabs": {name: self.is_tab_available(name) for name in common_tabs}
        }
        
        return status
