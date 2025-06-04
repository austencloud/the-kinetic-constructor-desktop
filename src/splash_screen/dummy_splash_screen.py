"""
Dummy Splash Screen - No-op splash screen for instant startup.

This provides a minimal splash screen interface that does nothing,
allowing the application to start instantly without any splash screen delays.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication
    from main_window.settings_manager.settings_manager import SettingsManager


class DummySplashUpdater:
    """Dummy splash updater that does nothing."""
    
    def update_progress(self, widget_name: str):
        """No-op progress update."""
        pass


class DummySplashScreen:
    """
    Dummy splash screen that provides the same interface as SplashScreen
    but does nothing, allowing for instant startup.
    """
    
    def __init__(self, app: "QApplication", settings_manager: "SettingsManager"):
        # Create dummy updater
        self.updater = DummySplashUpdater()
        
        # Store references for compatibility
        self.app = app
        self.settings_manager = settings_manager
    
    def show(self):
        """No-op show method."""
        pass
    
    def hide(self):
        """No-op hide method."""
        pass
    
    def close(self):
        """No-op close method."""
        pass
    
    def update(self):
        """No-op update method."""
        pass
