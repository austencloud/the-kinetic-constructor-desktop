from typing import TYPE_CHECKING

from main_window.main_widget.tab_indices import RightStackIndex

if TYPE_CHECKING:
    from .beat_deleter import BeatDeleter


class AllBeatsDeleter:
    def __init__(self, deleter: "BeatDeleter"):
        self.deleter = deleter
        self.main_widget = deleter.main_widget
        self.beat_frame = deleter.beat_frame

    def _remove_adjustment_panel_items(self, widgets: list) -> None:
        """Removes adjustment panel items from the given list of widgets."""
        adjustment_panel_items = (
            self.deleter.widget_collector.get_adjustment_panel_items()
        )
        for item in adjustment_panel_items:
            if item in widgets:
                widgets.remove(item)

    def _fade_and_reset(self, widgets, show_indicator):
        """Fades and resets the given widgets."""
        self.deleter.fade_and_reset_widgets(widgets, show_indicator)

    def _fade_widgets_and_stack(self, widgets, show_indicator):
        """Fades widgets and stack with a callback to reset widgets."""
        self.main_widget.fade_manager.widget_and_stack_fader.fade_widgets_and_stack(
            widgets,
            self.main_widget.right_stack,
            RightStackIndex.START_POS_PICKER,
            300,
            lambda: self.deleter.reset_widgets(show_indicator),
        )

    def _is_generate_tab_current(self) -> bool:
        """Check if the generate tab is currently active using the new MVVM architecture."""
        try:
            # Try to get generate tab through the new coordinator pattern
            generate_tab = self.main_widget.tab_manager.get_tab_widget("generate")
            if (
                generate_tab
                and self.main_widget.right_stack.currentWidget() == generate_tab
            ):
                return True
        except AttributeError:
            # Fallback: try through tab_manager for backward compatibility
            try:
                generate_tab = self.main_widget.tab_manager.get_tab_widget("generate")
                if (
                    generate_tab
                    and self.main_widget.right_stack.currentWidget() == generate_tab
                ):
                    return True
            except AttributeError:
                # Final fallback: try direct access for legacy compatibility
                try:
                    if hasattr(self.main_widget, "generate_tab"):
                        return (
                            self.main_widget.right_stack.currentWidget()
                            == self.main_widget.generate_tab
                        )
                except AttributeError:
                    pass
        return False

    def delete_all_beats(self, show_indicator=True) -> None:
        """Deletes all beats based on certain conditions."""
        beats = self.beat_frame.beat_views
        widgets = self.deleter.widget_collector.collect_shared_widgets()
        beats_filled = any(beat.is_filled for beat in beats)
        start_pos_filled = self.beat_frame.start_pos_view.is_filled

        if not beats_filled and not start_pos_filled:
            self._remove_adjustment_panel_items(widgets)
            self._fade_and_reset(widgets, show_indicator)

        elif not beats_filled and start_pos_filled:
            self._remove_adjustment_panel_items(widgets)
            self._fade_widgets_and_stack(widgets, show_indicator)

        elif self._is_generate_tab_current():
            self._fade_and_reset(widgets, show_indicator)
        else:
            self._fade_widgets_and_stack(widgets, show_indicator)
        # Update image export preview through the new dependency injection system
        try:
            settings_dialog = self.main_widget.widget_manager.get_widget(
                "settings_dialog"
            )
            if (
                settings_dialog
                and hasattr(settings_dialog, "ui")
                and hasattr(settings_dialog.ui, "image_export_tab")
            ):
                settings_dialog.ui.image_export_tab.update_preview()
        except AttributeError:
            # Fallback: settings dialog not available or not properly initialized
            pass
