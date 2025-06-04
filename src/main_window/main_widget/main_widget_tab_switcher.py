from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QApplication
from main_window.main_widget.browse_tab.sequence_picker.filter_stack.sequence_picker_filter_stack import (
    BrowseTabSection,
)
from main_window.main_widget.tab_index import TAB_INDEX
from main_window.main_widget.tab_indices import LeftStackIndex, RightStackIndex
from main_window.main_widget.tab_name import TabName

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget
    from core.application_context import ApplicationContext


class MainWidgetTabSwitcher:
    def __init__(
        self, main_widget: "MainWidget", app_context: "ApplicationContext" = None
    ):
        self.mw = main_widget
        self.app_context = app_context or getattr(main_widget, "app_context", None)

        self.tab_to_right_stack = {
            TAB_INDEX[TabName.GENERATE]: RightStackIndex.GENERATE_TAB,
            TAB_INDEX[TabName.LEARN]: RightStackIndex.LEARN_TAB,
            TAB_INDEX[TabName.SEQUENCE_CARD]: RightStackIndex.SEQUENCE_CARD_TAB,
        }

        self.tab_to_left_stack = {
            TAB_INDEX[TabName.LEARN]: LeftStackIndex.LEARN_CODEX,
            TAB_INDEX[TabName.GENERATE]: LeftStackIndex.WORKBENCH,
            TAB_INDEX[TabName.CONSTRUCT]: LeftStackIndex.WORKBENCH,
            TAB_INDEX[TabName.SEQUENCE_CARD]: LeftStackIndex.WORKBENCH,
        }

        self.index_to_tab_name = {v: k for k, v in TAB_INDEX.items()}

    def on_tab_changed(self, new_tab: TabName):
        """Handle tab changes with INSTANT visual feedback for browse tab."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        # CRITICAL: If switching to browse tab, do it INSTANTLY
        if new_tab == TabName.BROWSE:
            self._instant_browse_tab_switch()
            return

        # For other tabs, use the existing logic with immediate layout switching
        index = TAB_INDEX[new_tab]
        left_new_index, right_new_index = self.get_stack_indices_for_tab(new_tab)
        original_new_tab = new_tab
        new_tab = self.index_to_tab_name.get(index, TabName.CONSTRUCT)
        current_tab_str = self._get_current_tab()
        self._set_current_tab(new_tab.value)

        # CRITICAL: Immediate layout switching for non-browse tabs
        self._switch_layout_immediately(new_tab, left_new_index, right_new_index)
        QApplication.processEvents()

    def _instant_browse_tab_switch(self):
        """Instantly switch to browse tab with zero delay."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        try:
            # INSTANT: Update tab state immediately
            self._set_current_tab("browse")

            # INSTANT: Get browse tab indices
            left_new_index, right_new_index = self.get_stack_indices_for_tab(
                TabName.BROWSE
            )

            # INSTANT: Switch layout without any animations or delays
            self._disable_fades_temporarily()
            self._switch_layout_immediately(
                TabName.BROWSE, left_new_index, right_new_index
            )

            # INSTANT: Force immediate visual update
            QApplication.processEvents()

            # INSTANT: Ensure browse tab is visible and responsive
            browse_tab = self._get_browse_tab()
            if browse_tab:
                browse_tab.setEnabled(True)
                browse_tab.show()
                browse_tab.update()

            # INSTANT: Process events again for immediate responsiveness
            QApplication.processEvents()

            # BACKGROUND: Schedule content loading after visual switch
            QTimer.singleShot(1, self._load_browse_content_background)

            print("✅ Browse tab switched INSTANTLY")

        except Exception as e:
            print(f"❌ Error in instant browse switch: {e}")
            # Fallback to regular switching if instant fails
            self._switch_layout_immediately(
                TabName.BROWSE,
                LeftStackIndex.SEQUENCE_PICKER,
                RightStackIndex.SEQUENCE_CARD_TAB,
            )

    def _disable_fades_temporarily(self):
        """Temporarily disable fade animations for instant switching."""
        try:
            fade_manager = getattr(self.mw, "fade_manager", None)
            if fade_manager and hasattr(fade_manager, "set_fades_enabled"):
                fade_manager.set_fades_enabled(False)
                # Re-enable after a short delay
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(100, lambda: fade_manager.set_fades_enabled(True))
        except Exception as e:
            print(f"Error disabling fades: {e}")

    def _load_browse_content_background(self):
        """Load browse tab content in background after instant switch."""
        try:
            browse_tab = self._get_browse_tab()
            if browse_tab:
                # Initialize async content loading
                if hasattr(browse_tab, "initialize_content_async"):
                    browse_tab.initialize_content_async()
                else:
                    # Fallback to lightweight activation
                    self._simple_browse_tab_activation()

        except Exception as e:
            print(f"Error loading browse content in background: {e}")

    def _switch_layout_immediately(
        self, new_tab: TabName, left_new_index, right_new_index
    ):
        """Switch the layout immediately without heavy processing."""
        if new_tab == TabName.BROWSE:
            width_ratio = (2, 1)
        elif new_tab == TabName.SEQUENCE_CARD:
            width_ratio = (0, 1)
        else:
            width_ratio = (1, 1)

        left_idx = (
            left_new_index.value if hasattr(left_new_index, "value") else left_new_index
        )
        right_idx = (
            right_new_index.value
            if hasattr(right_new_index, "value")
            else right_new_index
        )

        # Immediate layout changes
        self.mw.left_stack.setCurrentIndex(left_idx)
        self.mw.right_stack.setCurrentIndex(right_idx)

        if new_tab == TabName.BROWSE:
            self.mw.content_layout.setStretch(0, 1)
            self.mw.content_layout.setStretch(1, 0)
            self.mw.right_stack.hide()
        else:
            self.mw.content_layout.setStretch(0, 1)
            self.mw.content_layout.setStretch(1, 1)
            self.mw.right_stack.show()

    def _show_browse_loading_indicator(self):
        """Show immediate loading feedback for browse tab."""
        try:
            browse_tab = self._get_browse_tab()
            if browse_tab and hasattr(browse_tab, "show_loading_state"):
                browse_tab.show_loading_state("Loading browse tab...")
            else:
                # Fallback: show in status or create simple indicator
                self._show_simple_loading_indicator()
        except Exception as e:
            print(f"Failed to show loading indicator: {e}")

    def _show_simple_loading_indicator(self):
        """Show a simple loading indicator as fallback."""
        try:
            # Create a simple loading overlay or status message
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import Qt

            browse_tab = self._get_browse_tab()
            if browse_tab:
                # Create temporary loading label
                if not hasattr(browse_tab, "_loading_label"):
                    browse_tab._loading_label = QLabel(
                        "Loading browse tab...", browse_tab
                    )
                    browse_tab._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    browse_tab._loading_label.setStyleSheet(
                        """
                        QLabel {
                            background-color: rgba(0, 0, 0, 0.7);
                            color: white;
                            font-size: 16px;
                            padding: 20px;
                            border-radius: 10px;
                        }
                    """
                    )
                    browse_tab._loading_label.resize(200, 60)

                # Position in center
                browse_tab._loading_label.move(
                    browse_tab.width() // 2 - 100, browse_tab.height() // 2 - 30
                )
                browse_tab._loading_label.show()
                browse_tab._loading_label.raise_()
        except Exception as e:
            print(f"Failed to show simple loading indicator: {e}")

    def _activate_browse_tab_async(self):
        """Activate browse tab asynchronously to prevent UI blocking."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        try:
            # Hide loading indicator
            self._hide_browse_loading_indicator()

            # Perform lightweight activation
            self._simple_browse_tab_activation()

            # Process events to keep UI responsive
            QApplication.processEvents()

            # Schedule heavy operations for later
            QTimer.singleShot(100, self._perform_heavy_browse_operations)

        except Exception as e:
            print(f"Error in async browse tab activation: {e}")
            self._hide_browse_loading_indicator()

    def _hide_browse_loading_indicator(self):
        """Hide the loading indicator."""
        try:
            browse_tab = self._get_browse_tab()
            if browse_tab:
                if hasattr(browse_tab, "hide_loading_state"):
                    browse_tab.hide_loading_state()
                elif hasattr(browse_tab, "_loading_label"):
                    browse_tab._loading_label.hide()
        except Exception as e:
            print(f"Failed to hide loading indicator: {e}")

    def _perform_heavy_browse_operations(self):
        """Perform heavy browse tab operations in background."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        try:
            browse_tab = self._get_browse_tab()
            if not browse_tab:
                return

            # Chunk heavy operations to prevent blocking
            operations = [
                self._ensure_thumbnails_loaded_chunk,
                self._update_browse_filters_chunk,
                self._finalize_browse_activation_chunk,
            ]

            self._current_operation_index = 0
            self._operations_queue = operations

            # Start processing operations with delays
            self._process_next_operation()

        except Exception as e:
            print(f"Error in heavy browse operations: {e}")

    def _process_next_operation(self):
        """Process the next operation in the queue."""
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        if self._current_operation_index >= len(self._operations_queue):
            return  # All operations completed

        try:
            # Execute current operation
            operation = self._operations_queue[self._current_operation_index]
            operation()

            # Process events to keep UI responsive
            QApplication.processEvents()

            # Move to next operation
            self._current_operation_index += 1

            # Schedule next operation with small delay
            QTimer.singleShot(50, self._process_next_operation)

        except Exception as e:
            print(f"Error in operation {self._current_operation_index}: {e}")
            # Continue with next operation even if current fails
            self._current_operation_index += 1
            QTimer.singleShot(50, self._process_next_operation)

    def _ensure_thumbnails_loaded_chunk(self):
        """Load thumbnails in small chunks to prevent blocking."""
        try:
            browse_tab = self._get_browse_tab()
            if browse_tab and hasattr(
                browse_tab, "_ensure_visible_thumbnails_loaded_async"
            ):
                browse_tab._ensure_visible_thumbnails_loaded_async()
        except Exception as e:
            print(f"Error loading thumbnails chunk: {e}")

    def _update_browse_filters_chunk(self):
        """Update browse filters without blocking."""
        try:
            browse_tab = self._get_browse_tab()
            if browse_tab and hasattr(browse_tab, "sequence_picker"):
                # Light filter update
                if hasattr(browse_tab.sequence_picker, "update_filters_lightweight"):
                    browse_tab.sequence_picker.update_filters_lightweight()
        except Exception as e:
            print(f"Error updating filters chunk: {e}")

    def _finalize_browse_activation_chunk(self):
        """Finalize browse tab activation."""
        try:
            browse_tab = self._get_browse_tab()
            if browse_tab and hasattr(browse_tab, "finalize_activation"):
                browse_tab.finalize_activation()
        except Exception as e:
            print(f"Error finalizing activation: {e}")

    def _get_browse_tab(self):
        """Get the browse tab instance."""
        try:
            if hasattr(self.mw, "browse_tab"):
                return self.mw.browse_tab
            elif hasattr(self.mw, "left_stack"):
                # Try to find browse tab in the stack
                for i in range(self.mw.left_stack.count()):
                    widget = self.mw.left_stack.widget(i)
                    if hasattr(
                        widget, "sequence_picker"
                    ):  # Browse tab has sequence_picker
                        return widget
            return None
        except Exception as e:
            print(f"Error getting browse tab: {e}")
            return None

    def debug_layout_state(self, main_widget, context=""):
        try:
            left_w = main_widget.left_stack.width()
            right_w = main_widget.right_stack.width()
            total_w = main_widget.width()
            ratio = left_w / right_w if right_w > 0 else 0

            left_stretch = main_widget.content_layout.stretch(0)
            right_stretch = main_widget.content_layout.stretch(1)

            print(f"🔍 LAYOUT DEBUG [{context}]:")
            print(f"   Total width: {total_w}px")
            print(f"   Left: {left_w}px ({left_w/total_w*100:.1f}%)")
            print(f"   Right: {right_w}px ({right_w/total_w*100:.1f}%)")
            print(f"   Ratio: {ratio:.2f} (target: 2.0)")
            print(f"   Stretch factors: Left={left_stretch}, Right={right_stretch}")
            print(f"   Left max width: {main_widget.left_stack.maximumWidth()}")
            print(f"   Right max width: {main_widget.right_stack.maximumWidth()}")

        except Exception as e:
            print(f"🔍 LAYOUT DEBUG ERROR: {e}")

    def _nuclear_meltdown_browse_tab_enforcement(self):
        try:
            main_widget = self.mw
            if hasattr(main_widget, "content_layout"):
                for i in range(10):
                    main_widget.content_layout.setStretch(0, 2)
                    main_widget.content_layout.setStretch(1, 1)
                    QApplication.processEvents()

                main_widget.left_stack.setMaximumWidth(16777215)
                main_widget.left_stack.setMinimumWidth(0)
                main_widget.right_stack.setMaximumWidth(16777215)
                main_widget.right_stack.setMinimumWidth(0)

                browse_tab = self._get_browse_tab()
                if browse_tab:
                    self._nuclear_meltdown_browse_components(browse_tab)

                for i in range(10):
                    QApplication.processEvents()
                    main_widget.content_layout.update()
                    main_widget.updateGeometry()
                    main_widget.update()
                    main_widget.repaint()

                self._setup_nuclear_meltdown_monitoring()

                self.debug_layout_state(main_widget, "after_nuclear_meltdown")

        except Exception as e:
            import traceback

            traceback.print_exc()

    def _enforce_browse_tab_layout_constraints(self):
        try:
            main_widget = self.mw
            if hasattr(main_widget, "content_layout"):
                main_widget.content_layout.setStretch(0, 2)
                main_widget.content_layout.setStretch(1, 1)

                main_widget.left_stack.setMaximumWidth(16777215)
                main_widget.left_stack.setMinimumWidth(0)
                main_widget.right_stack.setMaximumWidth(16777215)
                main_widget.right_stack.setMinimumWidth(0)

                browse_tab = self._get_browse_tab()
                if browse_tab:
                    self._nuclear_strike_browse_components(browse_tab)

                for _ in range(3):
                    QApplication.processEvents()
                    main_widget.content_layout.update()
                    main_widget.updateGeometry()

                self._setup_continuous_enforcement()

                self.debug_layout_state(main_widget, "after_targeted_nuclear_strike")

        except Exception as e:
            import traceback

            traceback.print_exc()

    def _nuclear_meltdown_browse_components(self, browse_tab):
        from PyQt6.QtWidgets import QSizePolicy

        fixed_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        preferred_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        expanding_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        if hasattr(browse_tab, "sequence_picker"):
            picker = browse_tab.sequence_picker
            picker.setSizePolicy(expanding_policy)

            if hasattr(picker, "scroll_widget"):
                picker.scroll_widget.setSizePolicy(expanding_policy)

            if hasattr(picker, "nav_sidebar"):
                picker.nav_sidebar.setSizePolicy(fixed_policy)
                picker.nav_sidebar.setMaximumWidth(100)
                picker.nav_sidebar.setMinimumWidth(50)

        if hasattr(browse_tab, "sequence_viewer"):
            viewer = browse_tab.sequence_viewer
            viewer.setSizePolicy(preferred_policy)

            total_width = self.mw.width()
            max_viewer_width = int(total_width / 3)
            viewer.setMaximumWidth(max_viewer_width)
            viewer.setMinimumWidth(max_viewer_width // 2)

            if hasattr(viewer, "thumbnail_box"):
                viewer.thumbnail_box.setSizePolicy(preferred_policy)
                viewer.thumbnail_box.setMaximumWidth(max_viewer_width - 20)

                if hasattr(viewer.thumbnail_box, "image_label"):
                    viewer.thumbnail_box.image_label.setSizePolicy(preferred_policy)

    def _nuclear_strike_browse_components(self, browse_tab):
        from PyQt6.QtWidgets import QSizePolicy

        expanding_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        preferred_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )

        if hasattr(browse_tab, "sequence_picker"):
            picker = browse_tab.sequence_picker
            picker.setSizePolicy(expanding_policy)

            if hasattr(picker, "scroll_widget"):
                picker.scroll_widget.setSizePolicy(expanding_policy)
            if hasattr(picker, "nav_sidebar"):
                picker.nav_sidebar.setSizePolicy(preferred_policy)
                if hasattr(picker.nav_sidebar, "setFixedWidth"):
                    max_sidebar_width = int(self.mw.width() / 12)
                    picker.nav_sidebar.setMaximumWidth(max_sidebar_width)

        if hasattr(browse_tab, "sequence_viewer"):
            viewer = browse_tab.sequence_viewer
            viewer.setSizePolicy(preferred_policy)

            if hasattr(viewer, "thumbnail_box"):
                viewer.thumbnail_box.setSizePolicy(preferred_policy)
                if hasattr(viewer.thumbnail_box, "image_label"):
                    viewer.thumbnail_box.image_label.setSizePolicy(preferred_policy)

    def _setup_nuclear_meltdown_monitoring(self):
        if not hasattr(self, "_meltdown_timer"):
            from PyQt6.QtCore import QTimer

            self._meltdown_timer = QTimer()
            self._meltdown_timer.timeout.connect(self._nuclear_meltdown_monitoring)
            self._meltdown_timer.start(500)

    def _nuclear_meltdown_monitoring(self):
        try:
            if hasattr(self.mw, "content_layout"):
                current_left_stretch = self.mw.content_layout.stretch(0)
                current_right_stretch = self.mw.content_layout.stretch(1)

                if current_left_stretch != 2 or current_right_stretch != 1:
                    for i in range(5):
                        self.mw.content_layout.setStretch(0, 2)
                        self.mw.content_layout.setStretch(1, 1)
                        QApplication.processEvents()

                    browse_tab = self._get_browse_tab()
                    if browse_tab and hasattr(browse_tab, "sequence_viewer"):
                        viewer = browse_tab.sequence_viewer
                        total_width = self.mw.width()
                        max_viewer_width = int(total_width / 3)
                        viewer.setMaximumWidth(max_viewer_width)

        except Exception as e:
            print(f"☢️ NUCLEAR MELTDOWN MONITORING ERROR: {e}")

    def _setup_continuous_enforcement(self):
        if not hasattr(self, "_enforcement_timer"):
            from PyQt6.QtCore import QTimer

            self._enforcement_timer = QTimer()
            self._enforcement_timer.timeout.connect(self._continuous_enforcement)
            self._enforcement_timer.start(1000)

    def _continuous_enforcement(self):
        try:
            if hasattr(self.mw, "content_layout"):
                current_left_stretch = self.mw.content_layout.stretch(0)
                current_right_stretch = self.mw.content_layout.stretch(1)

                if current_left_stretch != 2 or current_right_stretch != 1:
                    self.mw.content_layout.setStretch(0, 2)
                    self.mw.content_layout.setStretch(1, 1)
        except Exception as e:
            print(f"🚨 CONTINUOUS ENFORCEMENT ERROR: {e}")

    def set_stacks_silently(self, left_index, right_index):
        tab_name_str = self._get_current_tab()

        if tab_name_str == "browse":
            stretch_ratio = (2, 1)
        elif tab_name_str == "sequence_card":
            stretch_ratio = (0, 1)
        else:
            stretch_ratio = (1, 1)

        if hasattr(self.mw, "content_layout"):
            self.mw.content_layout.setStretch(0, stretch_ratio[0])
            self.mw.content_layout.setStretch(1, stretch_ratio[1])

            self.mw.left_stack.setMaximumWidth(16777215)
            self.mw.right_stack.setMaximumWidth(16777215)
            self.mw.left_stack.setMinimumWidth(0)
            self.mw.right_stack.setMinimumWidth(0)

        left_idx = left_index.value if hasattr(left_index, "value") else left_index
        right_idx = right_index.value if hasattr(right_index, "value") else right_index

        self.mw.left_stack.setCurrentIndex(left_idx)
        self.mw.right_stack.setCurrentIndex(right_idx)

    def get_stack_indices_for_tab(
        self, tab_name: TabName
    ) -> tuple[LeftStackIndex, RightStackIndex]:
        index = TAB_INDEX[tab_name]
        left_index = self.tab_to_left_stack.get(index, LeftStackIndex.WORKBENCH)
        if tab_name == TabName.CONSTRUCT:
            current_sequence = self.mw.json_manager.loader_saver.load_current_sequence()
            right_index = (
                RightStackIndex.OPTION_PICKER
                if len(current_sequence) > 1
                else RightStackIndex.START_POS_PICKER
            )
        elif tab_name == TabName.BROWSE:
            current_section_str = (
                self.mw.browse_tab.browse_settings.get_current_section()
            )

            filter_section_strs = [section.value for section in BrowseTabSection]
            if current_section_str in filter_section_strs:
                if current_section_str == BrowseTabSection.FILTER_SELECTOR.value:
                    left_index = LeftStackIndex.FILTER_SELECTOR
                    right_index = RightStackIndex.SEQUENCE_CARD_TAB
                else:
                    left_index = LeftStackIndex.SEQUENCE_PICKER
                    right_index = RightStackIndex.SEQUENCE_CARD_TAB
            else:
                left_index = LeftStackIndex.SEQUENCE_PICKER
                right_index = RightStackIndex.SEQUENCE_CARD_TAB

        elif tab_name == TabName.SEQUENCE_CARD:
            left_index = LeftStackIndex.WORKBENCH
            right_index = RightStackIndex.SEQUENCE_CARD_TAB
        else:
            right_index = self.tab_to_right_stack.get(index, index)

        return left_index, right_index

    def _get_current_tab(self) -> str:
        try:
            if self.app_context and hasattr(self.app_context, "settings_manager"):
                return (
                    self.app_context.settings_manager.global_settings.get_current_tab()
                )
        except (AttributeError, RuntimeError):
            pass

        try:
            from src.settings_manager.global_settings.app_context import AppContext

            return AppContext.settings_manager().global_settings.get_current_tab()
        except (AttributeError, RuntimeError):
            return "construct"

    def _set_current_tab(self, tab_name: str) -> None:
        try:
            if self.app_context and hasattr(self.app_context, "settings_manager"):
                self.app_context.settings_manager.global_settings.set_current_tab(
                    tab_name
                )
                return
        except (AttributeError, RuntimeError):
            pass

        try:
            from src.settings_manager.global_settings.app_context import AppContext

            AppContext.settings_manager().global_settings.set_current_tab(tab_name)
        except (AttributeError, RuntimeError):
            pass

    def _get_browse_tab(self):
        try:
            return self.mw.get_tab_widget("browse")
        except AttributeError:
            try:
                return self.mw.tab_manager.get_tab_widget("browse")
            except AttributeError:
                try:
                    if hasattr(self.mw, "browse_tab"):
                        return self.mw.browse_tab
                except AttributeError:
                    pass
        return None

    def _get_sequence_card_tab(self):
        try:
            return self.mw.get_tab_widget("sequence_card")
        except AttributeError:
            try:
                return self.mw.tab_manager.get_tab_widget("sequence_card")
            except AttributeError:
                try:
                    if hasattr(self.mw, "sequence_card_tab"):
                        return self.mw.sequence_card_tab
                except AttributeError:
                    pass
        return None

    def _simple_browse_tab_activation(self):
        """
        Simple browse tab activation when switched to.
        """
        try:
            # Get the browse tab from the left stack
            browse_tab = None
            for i in range(self.mw.left_stack.count()):
                widget = self.mw.left_stack.widget(i)
                if (
                    hasattr(widget, "__class__")
                    and "BrowseTab" in widget.__class__.__name__
                ):
                    browse_tab = widget
                    break

            if browse_tab:
                # Simple activation
                browse_tab.setEnabled(True)
                browse_tab.update()

                # Process events
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error in simple browse tab activation: {e}")
