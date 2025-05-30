"""
Dialog styling manager for the modern settings dialog.

Handles glassmorphism styling and theming.
"""

from typing import TYPE_CHECKING, Dict, Any
from PyQt6.QtWidgets import QDialog, QWidget
import logging

if TYPE_CHECKING:
    from src.core.application_context import ApplicationContext

logger = logging.getLogger(__name__)


class DialogStylingManager:
    """
    Manages dialog styling and theming.

    Responsibilities:
    - Apply glassmorphism styling to dialog
    - Style individual components
    - Handle shadow effects
    - Manage tab content styling
    """

    def __init__(self, dialog: QDialog, app_context: "ApplicationContext" = None):
        self.dialog = dialog
        self.app_context = app_context

    def apply_styling(
        self, components: Dict[str, Any], tabs: Dict[str, QWidget] = None
    ):
        """
        Apply complete styling to the dialog and its components.

        Args:
            components: Dictionary of dialog components
            tabs: Dictionary of tab widgets
        """
        try:
            # Apply main dialog styling
            self._apply_dialog_styling()

            # Apply shadow effects
            self._apply_shadow_effects(components)

            # Apply tab content styling
            if tabs:
                self._apply_tab_content_styling(tabs)

            logger.debug("Dialog styling applied successfully")

        except Exception as e:
            logger.error(f"Error applying styling: {e}")

    def _apply_dialog_styling(self):
        """Apply glassmorphism styling to the main dialog."""
        dialog_style = """
        /* Main dialog - transparent background for frameless effect */
        QDialog {
            background: transparent;
        }

        /* Main container with glassmorphism background */
        QWidget#main_container {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(30, 41, 59, 0.95),
                stop:0.5 rgba(51, 65, 85, 0.95),
                stop:1 rgba(30, 41, 59, 0.95));
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 24px;
        }

        /* Beautiful Modern Sidebar Styling */
        QListWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 255, 255, 0.08),
                stop:0.5 rgba(255, 255, 255, 0.12),
                stop:1 rgba(255, 255, 255, 0.08));
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 16px;
            padding: 12px 8px;
            outline: none;
            font-size: 14px;
            font-weight: 500;
        }

        QListWidget::item {
            background-color: transparent;
            color: rgba(255, 255, 255, 0.8);
            padding: 12px 16px;
            border-radius: 12px;
            margin: 2px 0;
            min-height: 20px;
            font-weight: 500;
        }

        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(99, 102, 241, 0.4),
                stop:1 rgba(139, 92, 246, 0.3));
            color: rgba(255, 255, 255, 1.0);
            border: 1px solid rgba(99, 102, 241, 0.6);
            font-weight: 600;
        }

        QListWidget::item:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 255, 255, 0.15),
                stop:1 rgba(255, 255, 255, 0.10));
            color: rgba(255, 255, 255, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.25);
        }

        QListWidget::item:focus {
            outline: none;
        }

        /* General label styling */
        QLabel {
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            background: transparent;
        }

        /* Content area styling */
        QStackedWidget {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 8px;
        }
        """

        self.dialog.setStyleSheet(dialog_style)

    def _apply_shadow_effects(self, components: Dict[str, Any]):
        """Apply shadow effects to components."""
        try:
            # Import glassmorphism styler
            from styles.glassmorphism_styler import GlassmorphismStyler

            # Add shadow effect to main container for depth
            if "main_container" in components:
                GlassmorphismStyler.add_shadow_effect(
                    components["main_container"], offset_y=12, blur_radius=32
                )

            # Add shadow effect to sidebar for additional depth
            if "sidebar" in components:
                GlassmorphismStyler.add_shadow_effect(
                    components["sidebar"], offset_x=2, offset_y=4, blur_radius=12
                )

        except ImportError:
            logger.warning("GlassmorphismStyler not available, skipping shadow effects")
        except Exception as e:
            logger.error(f"Error applying shadow effects: {e}")

    def _apply_tab_content_styling(self, tabs: Dict[str, QWidget]):
        """Apply styling to tab content widgets."""
        try:
            # Import glassmorphism styler
            from styles.glassmorphism_styler import GlassmorphismStyler

            # Apply unified tab content styling only to settings dialog tabs
            # This prevents glassmorphism styling from affecting browse tab image quality
            tab_content_style = GlassmorphismStyler.create_unified_tab_content_style()

            for tab_name, tab_widget in tabs.items():
                if tab_widget:
                    # Set object name for styling
                    tab_widget.setObjectName("tab_content")
                    # Apply the unified styling only to settings dialog tabs
                    current_style = tab_widget.styleSheet()
                    if current_style:
                        # Preserve existing styles and add new ones
                        combined_style = current_style + "\n" + tab_content_style
                    else:
                        combined_style = tab_content_style
                    tab_widget.setStyleSheet(combined_style)

        except ImportError:
            logger.warning(
                "GlassmorphismStyler not available, skipping tab content styling"
            )
        except Exception as e:
            logger.error(f"Error applying tab content styling: {e}")
