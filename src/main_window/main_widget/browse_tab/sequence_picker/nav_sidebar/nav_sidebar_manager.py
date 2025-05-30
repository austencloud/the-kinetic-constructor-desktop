from PyQt6.QtWidgets import QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint
from typing import TYPE_CHECKING

from .sidebar_length_section import SidebarLengthSection
from .level_section import SidebarLevelSection
from .button.sidebar_button import SidebarButton
from .base_sidebar_section import BaseSidebarSection
from .sidebar_date_added_section import SidebarDateAddedSection
from .sidebar_generic_section import SidebarGenericSection
from .letter_section import SidebarLetterSection
from src.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from ..sequence_picker import SequencePickerNavSidebar


class NavSidebarManager:
    def __init__(self, sidebar: "SequencePickerNavSidebar"):
        self.sidebar = sidebar
        self.layout = sidebar.layout
        self.sequence_picker = sidebar.sequence_picker
        self.settings_manager = AppContext.settings_manager()
        self.buttons: list[SidebarButton] = []
        self.current_section_obj: BaseSidebarSection | None = None
        self.selected_button: QPushButton | None = None

    def update_sidebar(self, sections, sort_order: str):
        """Update sidebar sections and determine max button width."""
        self.clear_sidebar()

        if sort_order == "sequence_length":
            section_obj = SidebarLengthSection(self)
        elif sort_order == "alphabetical":
            section_obj = SidebarLetterSection(self)
        elif sort_order == "date_added":
            section_obj = SidebarDateAddedSection(self)
        elif sort_order == "level":
            section_obj = SidebarLevelSection(self)
        else:
            section_obj = SidebarGenericSection(self)

        section_obj.create_widgets(sections)
        self.current_section_obj = section_obj

        # Pass sidebar width for accurate font measurement
        SidebarButton.calculate_max_width(self.buttons, self.sidebar.width())
        self.apply_button_widths()

        self.set_button_styles()
        self.sidebar.resize_sidebar()

    def apply_button_widths(self):
        """☢️ NUCLEAR ANNIHILATION: OBLITERATE FIXED WIDTH APPLICATION! ☢️"""

        # COMPLETELY OBLITERATED:
        # for button in self.buttons:
        #     button.setFixedWidth(SidebarButton._max_button_width)  # ☢️ OBLITERATED!

        pass

    def resize_sidebar(self):
        """Handle sidebar resizing and reapply button widths."""
        SidebarButton.calculate_max_width(self.buttons)
        self.apply_button_widths()

    def clear_sidebar(self):
        """Clear all sidebar widgets and reset buttons."""
        if self.current_section_obj:
            self.current_section_obj.clear()
            self.current_section_obj = None

        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item and item.widget() is None:
                self.layout.removeItem(item)

        self.buttons.clear()
        self.selected_button = None

    def style_button(self, button: SidebarButton, selected: bool = False, enabled=True):
        """Update button selection and reapply styles."""
        button.set_selected(selected)
        button.setEnabled(enabled)

    def set_button_styles(self):
        """Apply styles to all buttons."""
        for button in self.buttons:
            selected = button == self.selected_button
            self.style_button(button, selected=selected)

    def scroll_to_section(self, section: str, button: QPushButton):
        """Scroll sidebar to the corresponding section."""
        if self.selected_button:
            self.style_button(self.selected_button, selected=False)

        self.selected_button = button
        self.style_button(button, selected=True)

        sort_method = self.settings_manager.browse_settings.get_sort_method()
        if sort_method == "level":
            section = f"Level {section}"
        elif sort_method == "date_added":
            parts = section.split("-")
            section = f"{int(parts[0])}-{int(parts[1])}"

        header = self.sequence_picker.scroll_widget.section_headers.get(section)
        if header:
            scroll_area = self.sequence_picker.scroll_widget.scroll_area
            header_global_pos = header.mapToGlobal(QPoint(0, 0))
            content_widget_pos = scroll_area.widget().mapFromGlobal(header_global_pos)
            vertical_pos = content_widget_pos.y()
            scroll_area.verticalScrollBar().setValue(vertical_pos)

    def style_header_label(self, label: QLabel):
        font_color = self._get_font_color(
            self.settings_manager.global_settings.get_background_type()
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"""
            QLabel {{
                color: {font_color};
                padding: 5px;
                font-weight: bold;
            }}
        """
        )

        # Start with a reasonable font size
        font_size = self.sidebar.sequence_picker.main_widget.width() // 80
        label_font = label.font()
        label_font.setPointSize(font_size)
        label.setFont(label_font)

        # Adjust font size to fit within the sidebar width
        while label.sizeHint().width() > self.sidebar.width() and font_size > 1:
            font_size -= 1
            label_font.setPointSize(font_size)
            label.setFont(label_font)

    def _get_font_color(self, bg_type: str) -> str:
        """Get the appropriate font color using the new MVVM architecture with graceful fallbacks."""
        try:
            # Try to get font_color_updater through the new coordinator pattern
            font_color_updater = self.sequence_picker.main_widget.get_widget(
                "font_color_updater"
            )
            if font_color_updater and hasattr(font_color_updater, "get_font_color"):
                return font_color_updater.get_font_color(bg_type)
        except AttributeError:
            # Fallback: try through widget_manager for backward compatibility
            try:
                font_color_updater = (
                    self.sequence_picker.main_widget.widget_manager.get_widget(
                        "font_color_updater"
                    )
                )
                if font_color_updater and hasattr(font_color_updater, "get_font_color"):
                    return font_color_updater.get_font_color(bg_type)
            except AttributeError:
                # Final fallback: try direct access for legacy compatibility
                try:
                    if hasattr(self.sequence_picker.main_widget, "font_color_updater"):
                        return self.sequence_picker.main_widget.font_color_updater.get_font_color(
                            bg_type
                        )
                except AttributeError:
                    pass

        # Ultimate fallback: use the static method directly from FontColorUpdater
        try:
            from main_window.main_widget.font_color_updater.font_color_updater import (
                FontColorUpdater,
            )

            return FontColorUpdater.get_font_color(bg_type)
        except ImportError:
            # If all else fails, return a sensible default
            return (
                "black"
                if bg_type in ["Rainbow", "AuroraBorealis", "Aurora"]
                else "white"
            )

