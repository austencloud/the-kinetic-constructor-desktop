from datetime import datetime
from typing import TYPE_CHECKING, Union

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

from data.constants import GRID_MODE
from src.settings_manager.global_settings.app_context import AppContext

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class BrowseTabFilterController:
    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.filter_manager = browse_tab.filter_manager
        self.ui_updater = browse_tab.ui_updater
        fade_manager = browse_tab.main_widget.get_widget("fade_manager")
        if fade_manager:
            self.fade_manager = fade_manager
        else:
            # Fallback: try direct access for backward compatibility
            self.fade_manager = getattr(browse_tab.main_widget, "fade_manager", None)
        self.metadata_extractor = browse_tab.metadata_extractor

    def apply_filter(self, filter_criteria: Union[str, dict], fade=True):
        # AGGRESSIVE LOGGING: Track filter application
        print(f"🎯 APPLY_FILTER CALLED: {filter_criteria}")
        print(f"   fade: {fade}")

        # FILTER RESPONSIVENESS FIX: Check actual current tab state, not just settings
        current_tab = self._get_actual_current_tab()
        description = self._get_filter_description(filter_criteria)

        print(f"   current_tab: {current_tab}")
        print(f"   description: {description}")

        # CRITICAL FIX: Cancel any current loading before applying new filter
        if hasattr(self.browse_tab, "ui_updater"):
            context = f"filter_{filter_criteria}"
            self.browse_tab.ui_updater.cancel_current_loading(context)

        # INSTANT SWITCHING: Disable fades for instant filter operations
        instant_filter = self._is_instant_filter_operation(filter_criteria)
        if instant_filter and self.fade_manager:
            self.fade_manager.set_fades_enabled(False)

        self.browse_tab.browse_settings.set_current_filter(filter_criteria)
        widgets_to_fade = [
            self.browse_tab.sequence_picker.filter_stack,
            self.browse_tab.sequence_picker,
        ]
        if current_tab == "browse" and fade and not instant_filter:
            # FILTER BUTTON DELAY FIX: Switch to sequence picker immediately for responsive UI
            if hasattr(self.browse_tab, "internal_left_stack"):
                sequence_picker_index = (
                    1  # Sequence picker is at index 1 in internal stack
                )
                self.browse_tab.internal_left_stack.setCurrentIndex(
                    sequence_picker_index
                )

            self.fade_manager.widget_fader.fade_and_update(
                widgets_to_fade,
                (
                    lambda: self._apply_filter_after_fade(filter_criteria, description),
                    lambda: self.browse_tab.ui_updater.resize_thumbnails_top_to_bottom(),
                ),
            )

        else:
            self._apply_filter_after_fade(filter_criteria, description)
            if current_tab == "browse":
                self.browse_tab.ui_updater.resize_thumbnails_top_to_bottom()

        # INSTANT SWITCHING: Re-enable fades after instant operation
        if instant_filter and self.fade_manager:
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(100, lambda: self.fade_manager.set_fades_enabled(True))

        self.browse_tab.browse_settings.set_current_section("sequence_picker")

    def _get_actual_current_tab(self) -> str:
        """
        Get the actual current tab state, checking multiple sources for accuracy.

        This fixes the issue where settings may not be updated yet but the browse tab
        is actually the active tab.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Method 1: Check if browse tab is currently visible and active
            if self._is_browse_tab_currently_active():
                logger.debug("Browse tab detected as currently active")
                return "browse"

            # Method 2: Check main widget's current tab state
            if hasattr(self.browse_tab, "main_widget"):
                main_widget = self.browse_tab.main_widget

                # Try to get current tab from tab manager
                if hasattr(main_widget, "coordinator") and hasattr(
                    main_widget.coordinator, "get_current_tab"
                ):
                    current_tab = main_widget.coordinator.get_current_tab()
                    if current_tab:
                        logger.debug(f"Current tab from coordinator: {current_tab}")
                        return current_tab

                # Try to get from tab switcher
                if hasattr(main_widget, "tab_switcher"):
                    current_tab = main_widget.tab_switcher._get_current_tab()
                    if current_tab:
                        logger.debug(f"Current tab from tab switcher: {current_tab}")
                        return current_tab

            # Method 3: Fallback to settings (original method)
            from src.settings_manager.global_settings.app_context import AppContext

            current_tab = (
                AppContext.settings_manager().global_settings.get_current_tab()
            )
            logger.debug(f"Current tab from settings (fallback): {current_tab}")
            return current_tab

        except Exception as e:
            logger.warning(f"Error determining current tab: {e}")
            # Ultimate fallback
            return (
                "browse"  # Assume browse since this is the browse tab filter controller
            )

    def _is_browse_tab_currently_active(self) -> bool:
        """
        Check if the browse tab is currently the active/visible tab.
        """
        try:
            # Check if browse tab widget is visible
            if hasattr(self.browse_tab, "isVisible") and self.browse_tab.isVisible():
                # Check if browse tab is the current widget in the stack
                if hasattr(self.browse_tab, "main_widget"):
                    main_widget = self.browse_tab.main_widget

                    # Check left stack current widget
                    if hasattr(main_widget, "left_stack"):
                        current_widget = main_widget.left_stack.currentWidget()
                        if current_widget == self.browse_tab:
                            return True

                        # Check if browse tab is a child of the current widget
                        if hasattr(current_widget, "findChild"):
                            browse_child = current_widget.findChild(
                                type(self.browse_tab)
                            )
                            if browse_child == self.browse_tab:
                                return True

                return True  # If browse tab is visible, assume it's active

            return False

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error checking browse tab active state: {e}")
            return False

    def _apply_filter_after_fade(self, filter_criteria, description: str):
        # AGGRESSIVE LOGGING: Track filter after fade
        print(f"🔥 _APPLY_FILTER_AFTER_FADE CALLED: {filter_criteria}")
        print(f"   description: {description}")

        self._prepare_ui_for_filtering(description)
        print(f"   UI prepared for filtering")

        if isinstance(filter_criteria, str):
            print(f"   Handling STRING filter: {filter_criteria}")
            results = self._handle_string_filter(filter_criteria)
        elif isinstance(filter_criteria, dict):
            print(f"   Handling DICT filter: {filter_criteria}")
            results = self._handle_dict_filter(filter_criteria)
        else:
            raise ValueError(
                f"Invalid filter type: {type(filter_criteria)} (must be str or dict)."
            )

        print(f"   Filter results: {len(results)} sequences")
        self.browse_tab.sequence_picker.currently_displayed_sequences = results

        if not self.browse_tab.sequence_picker.initialized:
            skip_scaling = False
        else:
            skip_scaling = True
        print(f"   skip_scaling: {skip_scaling}")

        # CONTEXT-AWARE LOADING: Only load if user explicitly requested this filter
        should_load = self._should_load_sequences(filter_criteria, len(results))
        print(f"   should_load_sequences: {should_load}")

        if should_load:
            # PERFORMANCE FIX: Use chunked UI update for medium+ result sets
            if len(results) > 50:  # Lowered threshold for better responsiveness
                print(f"   Using CHUNKED UI update for {len(results)} sequences")
                if hasattr(self.ui_updater, "update_and_display_ui_chunked"):
                    context = f"filter_{filter_criteria}"
                    print(
                        f"   Calling update_and_display_ui_chunked with context: {context}"
                    )
                    self.ui_updater.update_and_display_ui_chunked(
                        len(results), skip_scaling, context=context
                    )
                else:
                    print(f"   Fallback to regular update_and_display_ui")
                    self.ui_updater.update_and_display_ui(len(results), skip_scaling)
            else:
                print(f"   Using REGULAR UI update for {len(results)} sequences")
                self.ui_updater.update_and_display_ui(len(results), skip_scaling)
        else:
            print(f"   NOT loading sequences - showing placeholder")
            # Don't load sequences if user didn't explicitly request them
            self._show_filter_placeholder(filter_criteria, len(results))
        # FILTER RESPONSIVENESS FIX: Use actual current tab check here too
        if self._get_actual_current_tab() == "browse":
            # ARCHITECTURAL FIX: Switch to sequence picker in browse tab's internal stack
            if hasattr(self.browse_tab, "internal_left_stack"):
                sequence_picker_index = (
                    1  # Sequence picker is at index 1 in internal stack
                )
                self.browse_tab.internal_left_stack.setCurrentIndex(
                    sequence_picker_index
                )
                import logging

                logger = logging.getLogger(__name__)
                logger.info(
                    f"✅ Switched to sequence picker in internal stack (index {sequence_picker_index})"
                )

    def _prepare_ui_for_filtering(self, description: str):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        control_panel = self.browse_tab.sequence_picker.control_panel
        control_panel.currently_displaying_label.setText(f"Displaying {description}")
        control_panel.count_label.setText("")
        self.browse_tab.sequence_picker.scroll_widget.clear_layout()

        # PROGRESS BAR FIX: Clear any leftover progress bar state
        self._clear_progress_bar_state()

    def _clear_progress_bar_state(self):
        """Clear any leftover progress bar state from previous operations."""
        try:
            # Clear progress bar if it exists in the UI updater
            if hasattr(self.browse_tab.ui_updater, "progress_bar"):
                progress_bar = self.browse_tab.ui_updater.progress_bar
                if progress_bar and hasattr(progress_bar, "hide"):
                    progress_bar.hide()
                    progress_bar.setValue(0)

            # Clear progress state in the UI updater
            if hasattr(self.browse_tab.ui_updater, "current_progress"):
                self.browse_tab.ui_updater.current_progress = 0

            # Clear any progress labels showing loading status
            if hasattr(self.browse_tab.ui_updater, "progress_label"):
                progress_label = self.browse_tab.ui_updater.progress_label
                if progress_label and hasattr(progress_label, "hide"):
                    progress_label.hide()

            # Cancel any ongoing loading operations
            if hasattr(self.browse_tab.ui_updater, "cancel_current_loading"):
                self.browse_tab.ui_updater.cancel_current_loading("filter_switch")

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error clearing progress bar state: {e}")

    def _handle_string_filter(self, filter_name: str):
        fm = self.filter_manager
        if filter_name == "favorites":
            return fm.filter_favorites()
        elif filter_name == "all":
            return fm.filter_all_sequences()
        elif filter_name == "most_recent":
            return fm.filter_most_recent(datetime.now())
        elif filter_name.startswith("tag:"):
            tag = filter_name.split("tag:")[1].strip()
            return fm.filter_by_tag(tag)
        else:
            raise ValueError(f"Unknown string filter: {filter_name}")

    def _handle_dict_filter(self, criteria: dict):
        if len(criteria) != 1:
            raise ValueError(
                "Dictionary filter must contain exactly one key-value pair."
            )
        (filter_key, filter_value) = next(iter(criteria.items()))
        dispatch_map = {
            "starting_letter": self._dict_filter_starting_letter,
            "contains_letters": self._dict_filter_contains_letters,
            "length": self._dict_filter_length,
            "level": self._dict_filter_level,
            "author": self._dict_filter_author,
            "starting_position": self._dict_filter_starting_pos,
            "favorites": self._dict_filter_favorites,
            "most_recent": self._dict_filter_most_recent,
            "difficulty": self._dict_filter_difficulty,
            "grid_mode": self._dict_filter_grid_mode,
            "show_all": self._dict_filter_show_all,
        }
        if filter_key not in dispatch_map:
            raise ValueError(f"Unknown dictionary filter key: {filter_key}")
        return dispatch_map[filter_key](filter_value)

    def _dict_filter_starting_letter(self, letter):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (word, thumbs, fm._get_sequence_length(thumbs[0]))
            for word, thumbs in base_words
            if word.startswith(letter)
        ]

    def _dict_filter_difficulty(self, _unused):
        return self.filter_manager.filter_by_difficulty()

    def _dict_filter_contains_letters(self, letters):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (word, thumbs, fm._get_sequence_length(thumbs[0]))
            for word, thumbs in base_words
            if any(char in word for char in letters)
        ]

    def _dict_filter_length(self, length_value):
        base_words = self._base_words()
        fm = self.filter_manager
        try:
            target_length = int(length_value)
        except ValueError:
            raise ValueError(f"Invalid length '{length_value}'; expected integer.")
        return [
            (word, thumbs, fm._get_sequence_length(thumbs[0]))
            for word, thumbs in base_words
            if fm._get_sequence_length(thumbs[0]) == target_length
        ]

    def _dict_filter_level(self, level_value):
        base_words = self._base_words()
        filter_manager = self.filter_manager

        results = []
        for word, thumbs in base_words:
            # If thumbs is empty or None, skip it
            if not thumbs:
                continue

            # Otherwise, safe to do thumbs[0]
            if self.metadata_extractor.get_level(thumbs[0]) == level_value:
                seq_length = filter_manager._get_sequence_length(thumbs[0])
                results.append((word, thumbs, seq_length))

        return results

    def _dict_filter_author(self, author_value):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (w, t, fm._get_sequence_length(t[0]))
            for w, t in base_words
            if self.metadata_extractor.get_author(t[0]) == author_value
        ]

    def _dict_filter_starting_pos(self, pos_value):
        base_words = self._base_words()
        fm = self.filter_manager
        result = []
        for w, t in base_words:
            if self.metadata_extractor.get_start_pos(t[0]) == pos_value.lower():
                result.append((w, t, fm._get_sequence_length(t[0])))
        return result

    def _dict_filter_favorites(self, _unused):
        return self.filter_manager.filter_favorites()

    def _dict_filter_most_recent(self, _unused):
        return self.filter_manager.filter_most_recent()

    def _dict_filter_grid_mode(self, grid_mode_value):
        base_words = self._base_words()
        fm = self.filter_manager
        return [
            (w, t, fm._get_sequence_length(t[0]))
            for w, t in base_words
            if self.metadata_extractor.get_grid_mode(t[0]) == grid_mode_value
        ]

    def _dict_filter_show_all(self, _unused):
        # PERFORMANCE FIX: Use chunked loading for "Show All" to prevent UI freezing
        return self._filter_all_sequences_chunked()

    def _filter_all_sequences_chunked(self):
        """
        PERFORMANCE FIX: Filter all sequences with chunked processing to prevent UI freezing.

        This method processes sequences in small chunks and yields control back to the UI
        between chunks to maintain responsiveness.
        """
        from PyQt6.QtWidgets import QApplication

        try:
            # Get all base words
            all_words = self.browse_tab.get.base_words()
            sequences = []

            # Process in chunks of 50 sequences to prevent UI blocking
            chunk_size = 50
            processed_count = 0

            for word, thumbnails in all_words:
                if not thumbnails:
                    continue

                try:
                    sequence_length = self.filter_manager._get_sequence_length(
                        thumbnails[0]
                    )
                    sequences.append((word, thumbnails, sequence_length))
                    processed_count += 1

                    # Process events every chunk_size items to keep UI responsive
                    if processed_count % chunk_size == 0:
                        QApplication.processEvents()

                except Exception as e:
                    print(f"Error processing {word}: {e}")
                    continue

            return sequences

        except Exception as e:
            print(f"Error in chunked sequence filtering: {e}")
            # Fallback to original method if chunked processing fails
            return self.filter_manager.filter_all_sequences()

    def _base_words(self) -> list[tuple[str, list[str]]]:
        all_words = self.browse_tab.get.base_words()
        base_words = []
        for w, thumbs in all_words:
            if thumbs:  # only store if thumbs is non-empty
                base_words.append((w, thumbs))
        return base_words

    def _get_filter_description(self, filter_criteria: Union[str, dict]) -> str:
        if isinstance(filter_criteria, str):
            if filter_criteria == "all":
                return "all sequences"
            elif filter_criteria.startswith("tag:"):
                tag_name = filter_criteria.split("tag:")[1].strip()
                return f"sequences with tag '{tag_name}'"
            return filter_criteria.replace("_", " ").capitalize()
        return self._description_for_dict_filter(filter_criteria)

    def _description_for_dict_filter(self, filter_criteria: dict) -> str:
        if len(filter_criteria) != 1:
            return "Unknown Filter"
        key, value = list(filter_criteria.items())[0]
        desc_map = {
            "starting_letter": f"sequences starting with {value}",
            "contains_letters": f"sequences containing {value}",
            "length": f"sequences with length {value}",
            "level": f"sequences with level {value}",
            "author": f"sequences by {value}",
            "starting_position": f"sequences starting at position {value}",
            "favorites": "favorite sequences",
            "most_recent": "most recent sequences",
            GRID_MODE: f"sequences in {value} mode",
            "show_all": "all sequences",
        }
        return desc_map.get(key, "Unknown Filter")

    def _should_load_sequences(self, filter_criteria, result_count: int) -> bool:
        """
        CONTEXT-AWARE LOADING: Determine if sequences should be loaded based on context.

        Args:
            filter_criteria: The filter that was applied
            result_count: Number of sequences that would be loaded

        Returns:
            True if sequences should be loaded, False if they should be deferred
        """
        # Always load small result sets (under 100 sequences)
        if result_count < 100:
            return True

        # Check if this is an explicit "Show All" request
        if isinstance(filter_criteria, dict) and "show_all" in filter_criteria:
            return True  # User explicitly requested "Show All"

        # Check if this is a specific filter request (not background loading)
        if isinstance(filter_criteria, dict):
            # These are explicit user selections, should load
            explicit_filters = [
                "starting_letter",
                "starting_position",
                "length",
                "level",
                "favorites",
                "author",
            ]
            if any(key in filter_criteria for key in explicit_filters):
                return True

        # For string filters, check if they're explicit requests
        if isinstance(filter_criteria, str):
            explicit_string_filters = ["favorites", "most_recent"]
            if filter_criteria in explicit_string_filters:
                return True

        # Default: don't load large result sets unless explicitly requested
        return False

    def _show_filter_placeholder(self, filter_criteria, result_count: int):
        """
        Show a placeholder instead of loading sequences when appropriate.

        Args:
            filter_criteria: The filter that was applied
            result_count: Number of sequences available
        """
        try:
            # Clear the current layout
            self.browse_tab.sequence_picker.scroll_widget.clear_layout()

            # Update control panel with placeholder message
            control_panel = self.browse_tab.sequence_picker.control_panel
            filter_description = self._get_filter_description(filter_criteria)

            if result_count > 500:
                message = f"Found {result_count} sequences for '{filter_description}'. Click 'Load All' to display them."
            else:
                message = f"Found {result_count} sequences for '{filter_description}'. Loading..."
                # Auto-load medium-sized result sets after a short delay
                QTimer.singleShot(
                    100, lambda: self._load_deferred_sequences(filter_criteria)
                )

            control_panel.currently_displaying_label.setText(message)
            control_panel.count_label.setText(f"Available: {result_count}")

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error showing filter placeholder: {e}")

    def _load_deferred_sequences(self, filter_criteria):
        """Load sequences that were deferred due to size."""
        try:
            # Re-apply the filter to load the sequences
            self.apply_filter(filter_criteria, fade=False)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error loading deferred sequences: {e}")

    def _is_instant_filter_operation(self, filter_criteria) -> bool:
        """
        Determine if the filter operation should be instant (no fade) based on criteria.

        Returns True for operations that should switch instantly without fade delays.
        """
        # Instant for specific dictionary keys that represent user selections
        if isinstance(filter_criteria, dict):
            instant_keys = [
                "starting_letter",
                "level",
                "length",
                "contains_letters",
                "favorites",
                "most_recent",
                "show_all",
                "author",
                "starting_position",
            ]
            if any(key in filter_criteria for key in instant_keys):
                return True

        # Instant for string filters
        if isinstance(filter_criteria, str):
            instant_strings = ["favorites", "most_recent", "all"]
            return filter_criteria in instant_strings

        return False
