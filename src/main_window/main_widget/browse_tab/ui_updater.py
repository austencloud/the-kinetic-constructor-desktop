import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QApplication
from .thumbnail_box.thumbnail_box import ThumbnailBox
from src.settings_manager.global_settings.app_context import AppContext
from .sequence_picker.nav_sidebar.button.button_ui_updater import (
    SidebarButtonUIUpdater,
)
from .thumbnail_box.ui_updater import ThumbnailBoxUIUpdater

if TYPE_CHECKING:
    from main_window.main_widget.browse_tab.browse_tab import BrowseTab


class BrowseTabUIUpdater:
    """Updates the Browse Tab UI, managing thumbnails and navigation."""

    def __init__(self, browse_tab: "BrowseTab"):
        self.browse_tab = browse_tab
        self.settings_manager = AppContext.settings_manager()
        self.thumbnail_updater = ThumbnailBoxUIUpdater(browse_tab)
        self.sidebar_button_updater = SidebarButtonUIUpdater(browse_tab)
        self._resize_job_id = 0
        self._last_window_width = None

        # Loading cancellation and context tracking
        self._current_loading_context: Optional[str] = None
        self._loading_cancelled = False
        self._current_item_index = 0
        self._sequences_to_process = []
        self._skip_scaling = True

    def cancel_current_loading(self, new_context: str = None):
        """Cancel any current loading operation and set new context."""
        logger = logging.getLogger(__name__)
        if self._current_loading_context:
            logger.info(
                f"🚫 Cancelling loading context: {self._current_loading_context}"
            )

        self._loading_cancelled = True
        self._current_loading_context = new_context

        # Hide any loading indicators
        if hasattr(self.browse_tab, "hide_loading_state"):
            self.browse_tab.hide_loading_state()

        # Reset processing state
        self._current_item_index = 0
        self._sequences_to_process = []

        logger.info(f"✅ Loading cancelled. New context: {new_context}")

    def update_and_display_ui(self, total_sequences: int, skip_scaling: bool = True):
        """Updates and displays the UI based on the total number of sequences."""
        QApplication.restoreOverrideCursor()

        if total_sequences == 0:
            return

        self._sort_sequences()
        self._create_and_show_thumbnails(skip_scaling)

    def _sort_sequences(self):
        """Sorts the sequences in the sequence picker."""
        sort_method = self.settings_manager.browse_settings.get_sort_method()
        self.browse_tab.sequence_picker.sorter._sort_only(sort_method)

    def _create_and_show_thumbnails(self, skip_scaling: bool = True):
        """Creates and displays thumbnails, applying styling."""
        self.browse_tab.sequence_picker.sorter.display_sorted_sections(skip_scaling)
        background_type = self.settings_manager.global_settings.get_background_type()
        self.thumbnail_updater.apply_thumbnail_styling(background_type)

    def resize_thumbnails_top_to_bottom(self):
        """Resizes thumbnails from top to bottom, enabling navigation buttons."""

        sections_copy = dict(self.browse_tab.sequence_picker.sections)
        sort_method = self.settings_manager.browse_settings.get_sort_method()
        sorted_sections = (
            self.browse_tab.sequence_picker.section_manager.get_sorted_sections(
                sort_method, sections_copy.keys()
            )
        )

        self.sidebar_button_updater.disable_all_buttons()

        scroll_widget = self.browse_tab.sequence_picker.scroll_widget
        for section in sorted_sections:
            if section not in sections_copy:
                return
            for word, _ in self.browse_tab.sequence_picker.sections.get(section, []):
                if word not in scroll_widget.thumbnail_boxes:
                    return

                # CRITICAL FIX: Remove tab check that was preventing thumbnail loading during startup
                # The tab check was causing thumbnails to not load when the app starts in browse tab
                # because the tab state might not be properly set during initialization

                thumbnail_box = scroll_widget.thumbnail_boxes[word]

                # Use asynchronous thumbnail loading to prevent UI blocking
                self.thumbnail_updater.update_thumbnail_image_async(thumbnail_box)
            if sort_method == "date_added":
                month, day, _ = section.split("-")
                day = day.lstrip("0")
                month = month.lstrip("0")
                section = f"{month}-{day}"

            self._enable_button_for_section(section)

    def _enable_button_for_section(self, section_key: str):
        """Enables a specific navigation button by section key."""
        self.sidebar_button_updater.enable_button_for_section(section_key)

    # CRITICAL FIX: Lightweight UI update for non-blocking tab switching
    def update_and_display_ui_lightweight(self):
        """Lightweight UI update that doesn't block the main thread."""
        from PyQt6.QtWidgets import QApplication

        try:
            logger = logging.getLogger(__name__)
            logger.info("🚀 Starting lightweight UI update")

            # Only do minimal updates to prevent blocking
            if hasattr(self.browse_tab, "sequence_picker"):
                # Just ensure the UI is responsive
                QApplication.processEvents()

                # Show basic layout without thumbnails
                if hasattr(self.browse_tab.sequence_picker, "scroll_widget"):
                    scroll_widget = self.browse_tab.sequence_picker.scroll_widget
                    scroll_widget.show()

                # Enable navigation buttons without heavy processing
                if hasattr(self.browse_tab.sequence_picker, "nav_sidebar"):
                    nav_sidebar = self.browse_tab.sequence_picker.nav_sidebar
                    nav_sidebar.show()

                logger.info("✅ Lightweight UI update completed")

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error in lightweight UI update: {e}")

    def update_and_display_ui_chunked(
        self, total_sequences: int, skip_scaling: bool = True, context: str = "default"
    ):
        """
        PERFORMANCE FIX: Synchronous chunked UI update with cancellation support.

        This method processes thumbnails in small chunks with UI event processing
        between chunks to maintain responsiveness while supporting cancellation.
        """
        from PyQt6.QtWidgets import QApplication

        # FREEZE DETECTION: Add entry logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"🚀 ENTERING update_and_display_ui_chunked with {total_sequences} sequences, context: {context}"
        )

        try:
            # Set loading context and reset cancellation flag
            self._current_loading_context = context
            self._loading_cancelled = False

            QApplication.restoreOverrideCursor()

            if total_sequences == 0:
                return

            # Show modern progress bar instead of center loading message
            self._show_modern_progress_bar(total_sequences)

            # Sort sequences first (lightweight operation)
            self._sort_sequences()

            # Start synchronous chunked thumbnail creation
            self._create_and_show_thumbnails_chunked_sync(skip_scaling, total_sequences)

        except Exception as e:
            logger.error(f"Error in chunked UI update: {e}")
            # Fallback to regular update
            self.update_and_display_ui(total_sequences, skip_scaling)

    def _show_modern_progress_bar(self, total_sequences: int):
        """Show modern horizontal progress bar at top of sequence picker."""
        try:
            # Get or create progress bar widget
            if not hasattr(self.browse_tab.sequence_picker, "modern_progress_bar"):
                from .modern_progress_bar import ModernProgressBar

                self.browse_tab.sequence_picker.modern_progress_bar = ModernProgressBar(
                    self.browse_tab.sequence_picker
                )

                # Insert at top of sequence picker layout
                layout = self.browse_tab.sequence_picker.main_layout
                layout.insertWidget(
                    0, self.browse_tab.sequence_picker.modern_progress_bar
                )

            # Show and configure progress bar
            progress_bar = self.browse_tab.sequence_picker.modern_progress_bar
            progress_bar.set_total(total_sequences)
            progress_bar.set_current(0)
            progress_bar.show()

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to show modern progress bar: {e}")
            # Fallback to old loading indicator
            if hasattr(self.browse_tab, "show_loading_state"):
                self.browse_tab.show_loading_state("Loading sequences...")

    def _create_and_show_thumbnails_chunked_sync(
        self, skip_scaling: bool, total_sequences: int
    ):
        """Create and show thumbnails synchronously with enhanced caching support."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QSize

        # FREEZE DETECTION: Add entry logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"🚀 ENTERING _create_and_show_thumbnails_chunked_sync with {total_sequences} sequences"
        )

        try:
            sequences = self.browse_tab.sequence_picker.currently_displayed_sequences
            logger.info(
                f"📊 Retrieved {len(sequences) if sequences else 0} sequences from sequence_picker"
            )

            if not sequences:
                logger.info("⚠️ No sequences found - finalizing update")
                self._finalize_chunked_update()
                return

            # CRITICAL FIX: Ensure scroll widget is fully initialized before proceeding
            if not self._ensure_scroll_widget_ready():
                logger = logging.getLogger(__name__)
                logger.warning(
                    "⚠️ Scroll widget readiness check failed - attempting fallback"
                )

                # FALLBACK: Try to proceed anyway with extra safety checks
                # This prevents the UI from being completely blocked
                try:
                    scroll_widget = self.browse_tab.sequence_picker.scroll_widget
                    if scroll_widget and hasattr(scroll_widget, "clear_layout"):
                        logger.info("🔄 Proceeding with fallback thumbnail creation")
                        # Continue with the process but with extra caution
                    else:
                        logger.error(
                            "❌ Scroll widget completely unavailable - aborting"
                        )
                        self._finalize_chunked_update()
                        return
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback check failed: {fallback_error}")
                    self._finalize_chunked_update()
                    return

            # CACHE-AWARE UI UPDATE: Check for cached thumbnails before clearing layout
            logger = logging.getLogger(__name__)
            print(f"🔍 CHECKING CACHE for {len(sequences)} sequences...")
            logger.info(f"🔍 Checking cache for {len(sequences)} sequences...")

            cached_count = self._check_cached_thumbnails_available(sequences)
            cache_hit_rate = (cached_count / len(sequences) * 100) if sequences else 0

            print(
                f"📊 CACHE ANALYSIS: {cached_count}/{len(sequences)} cached ({cache_hit_rate:.1f}%)"
            )
            logger.info(
                f"📊 Cache analysis: {cached_count}/{len(sequences)} cached ({cache_hit_rate:.1f}%)"
            )

            # TEMPORARY: Lower threshold to 50% for testing and add detailed logging
            threshold = len(sequences) * 0.5  # 50% threshold for testing

            if cached_count > threshold:
                print(f"🎯 HIGH CACHE HIT RATE - using fast cached update")
                logger.info(
                    f"🎯 HIGH cache hit rate ({cached_count}/{len(sequences)}, {cache_hit_rate:.1f}%) - using fast cached update"
                )
                self._create_thumbnails_from_cache(sequences)
                self._finalize_chunked_update()
                return
            else:
                print(f"🔄 LOW CACHE HIT RATE - rebuilding thumbnails")
                print(f"   Threshold was {threshold:.1f} cached images")
                logger.info(
                    f"🔄 LOW cache hit rate ({cached_count}/{len(sequences)}, {cache_hit_rate:.1f}%) - rebuilding thumbnails"
                )
                logger.info(f"   Threshold was {threshold:.1f} cached images")

                # IMMEDIATE FEEDBACK: Show loading state immediately
                print("📢 SHOWING IMMEDIATE LOADING FEEDBACK...")
                self._show_immediate_loading_feedback(len(sequences))

                print("🧹 CLEARING SCROLL WIDGET LAYOUT...")
                self.browse_tab.sequence_picker.scroll_widget.clear_layout()

            # ULTRA RESPONSIVE: Process thumbnails in tiny chunks with frequent UI updates
            chunk_size = 2  # Very small chunks for maximum responsiveness
            total_processed = 0

            print(
                f"🚀 STARTING THUMBNAIL PROCESSING: {len(sequences)} sequences in chunks of {chunk_size}"
            )

            for i in range(0, len(sequences), chunk_size):
                # Check for cancellation
                if self._loading_cancelled:
                    print("🚫 LOADING CANCELLED during chunked processing")
                    logger.info("🚫 Loading cancelled during chunked processing")
                    return

                # Process chunk
                chunk = sequences[i : i + chunk_size]
                print(
                    f"📦 PROCESSING CHUNK {i//chunk_size + 1}: {len(chunk)} sequences"
                )

                for word, thumbnails, length in chunk:
                    if self._loading_cancelled:
                        print("🚫 LOADING CANCELLED during thumbnail creation")
                        return

                    try:
                        print(
                            f"🔄 PROCESSING SEQUENCE: {word} (#{total_processed + 1})"
                        )
                        # SIMPLIFIED: Create thumbnails normally, let caching happen in ImageLoadingManager
                        self._create_single_thumbnail(word, thumbnails, total_processed)
                        total_processed += 1
                        print(f"✅ COMPLETED SEQUENCE: {word} (#{total_processed})")

                        # Update progress bar after each thumbnail
                        if hasattr(
                            self.browse_tab.sequence_picker, "modern_progress_bar"
                        ):
                            self.browse_tab.sequence_picker.modern_progress_bar.set_current(
                                total_processed
                            )

                        # IMMEDIATE UI UPDATE: Process events after each thumbnail
                        QApplication.processEvents()

                    except Exception as e:
                        print(f"❌ ERROR creating thumbnail for {word}: {e}")
                        logger.error(f"Error creating thumbnail for {word}: {e}")

                # FREQUENT UI UPDATES: Process events after each small chunk
                QApplication.processEvents()

                # Show progress in title
                if total_processed % 10 == 0:  # Update every 10 thumbnails
                    progress_percent = (total_processed / len(sequences)) * 100
                    print(
                        f"📊 PROGRESS UPDATE: {total_processed}/{len(sequences)} ({progress_percent:.1f}%)"
                    )
                    logger.info(
                        f"📊 Progress: {total_processed}/{len(sequences)} ({progress_percent:.1f}%)"
                    )

                # No delay - maximum speed with frequent UI updates

            self._finalize_chunked_update()

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in synchronous chunked thumbnail creation: {e}")
            self._finalize_chunked_update()

    def _create_single_thumbnail(self, word: str, thumbnails: list, index: int):
        """Create a single thumbnail widget with proper parent assignment."""
        try:
            from .thumbnail_box.factory import ThumbnailBoxFactory

            # AGGRESSIVE LOGGING: Log every single thumbnail creation attempt
            print(f"🔨 CREATING THUMBNAIL #{index}: {word}")
            print(f"   Thumbnails: {thumbnails}")

            # CRITICAL FIX: Ensure scroll widget is ready before creating thumbnails
            scroll_widget = self.browse_tab.sequence_picker.scroll_widget
            if not scroll_widget:
                print(f"❌ SCROLL WIDGET NOT AVAILABLE for {word}")
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Scroll widget not available for thumbnail {word}")
                return

            # SMART SCROLL WIDGET DETECTION AND GRID LAYOUT HANDLING
            logger = logging.getLogger(__name__)
            scroll_widget_type = type(scroll_widget).__name__
            print(f"🔍 SCROLL WIDGET TYPE: {scroll_widget_type}")
            logger.info(f"🔍 Detected scroll widget type: {scroll_widget_type}")

            # DEBUGGING: Check grid layout status before processing
            print(
                f"🔧 BEFORE PROCESSING - grid_layout: {getattr(scroll_widget, 'grid_layout', 'NOT_SET')}"
            )
            print(
                f"🔧 BEFORE PROCESSING - scroll_content.layout(): {scroll_widget.scroll_content.layout() if hasattr(scroll_widget, 'scroll_content') else 'NO_SCROLL_CONTENT'}"
            )

            # Handle ModernScrollWidget differently from legacy SequencePickerScrollWidget
            if "ModernScrollWidget" in scroll_widget_type:
                print(f"🎨 USING MODERN SCROLL WIDGET for {word}")
                logger.info(
                    f"🎨 Using ModernScrollWidget - creating thumbnail and delegating to modern integration for {word}"
                )

                print(f"   Creating thumbnail box for {word}...")
                # Create thumbnail box first
                thumbnail_box = ThumbnailBoxFactory.create_thumbnail_box(
                    browse_tab=self.browse_tab,
                    word=word,
                    thumbnails=thumbnails,
                    in_sequence_viewer=False,
                    use_integrated=True,
                )
                print(f"   ✅ Thumbnail box created for {word}")

                print(f"   Adding to scroll widget for {word}...")
                # For ModernScrollWidget, use the add_thumbnail_box method which handles modern integration
                scroll_widget.add_thumbnail_box(word, thumbnail_box)
                print(f"✅ ADDED THUMBNAIL {word} TO MODERN SCROLL WIDGET")
                logger.info(f"✅ Added thumbnail {word} to ModernScrollWidget")
                return  # Modern scroll widget handles everything internally

            # Legacy SequencePickerScrollWidget handling - FIXED GRID LAYOUT ACCESS
            if not hasattr(scroll_widget, "grid_layout"):
                logger.error(
                    f"❌ CRITICAL: SequencePickerScrollWidget missing grid_layout attribute for {word}"
                )
                print(
                    f"❌ CRITICAL: No grid_layout attribute on scroll widget for {word}"
                )
                return

            if not scroll_widget.grid_layout:
                logger.error(
                    f"❌ CRITICAL: SequencePickerScrollWidget grid_layout is None for {word} - RECOVERING"
                )
                print(
                    f"❌ CRITICAL: grid_layout is None for {word} - ATTEMPTING RECOVERY"
                )

                # EMERGENCY GRID LAYOUT RECOVERY: Force re-initialization
                try:
                    print(f"🚨 EMERGENCY MAIN: Re-initializing grid layout for {word}")
                    scroll_widget._setup_layout()  # Call the setup method to recreate the grid layout

                    # DEBUGGING: Check grid layout status immediately after setup
                    print(
                        f"🔧 IMMEDIATE CHECK - grid_layout: {getattr(scroll_widget, 'grid_layout', 'NOT_SET')}"
                    )
                    print(
                        f"🔧 IMMEDIATE CHECK - hasattr: {hasattr(scroll_widget, 'grid_layout')}"
                    )
                    if hasattr(scroll_widget, "grid_layout"):
                        print(
                            f"🔧 IMMEDIATE CHECK - grid_layout value: {scroll_widget.grid_layout}"
                        )
                        print(
                            f"🔧 IMMEDIATE CHECK - grid_layout type: {type(scroll_widget.grid_layout)}"
                        )

                    # Verify recovery worked
                    print(
                        f"🔧 VERIFICATION CHECK - hasattr: {hasattr(scroll_widget, 'grid_layout')}"
                    )
                    if hasattr(scroll_widget, "grid_layout"):
                        print(
                            f"🔧 VERIFICATION CHECK - grid_layout value: {scroll_widget.grid_layout}"
                        )
                        print(
                            f"🔧 VERIFICATION CHECK - grid_layout type: {type(scroll_widget.grid_layout)}"
                        )
                        print(
                            f"🔧 VERIFICATION CHECK - grid_layout is None: {scroll_widget.grid_layout is None}"
                        )
                        print(
                            f"🔧 VERIFICATION CHECK - bool(grid_layout): {bool(scroll_widget.grid_layout)}"
                        )

                    if (
                        hasattr(scroll_widget, "grid_layout")
                        and scroll_widget.grid_layout
                    ):
                        print(
                            f"✅ MAIN RECOVERY SUCCESS: Grid layout restored for {word}"
                        )
                        logger.info(
                            f"✅ Grid layout successfully recovered in main process for {word}"
                        )
                    else:
                        print(
                            f"❌ MAIN RECOVERY FAILED: Could not restore grid layout for {word}"
                        )
                        print(
                            f"🔧 VERIFICATION FAILED - hasattr: {hasattr(scroll_widget, 'grid_layout')}"
                        )
                        if hasattr(scroll_widget, "grid_layout"):
                            print(
                                f"🔧 VERIFICATION FAILED - grid_layout: {scroll_widget.grid_layout}"
                            )
                        logger.error(
                            f"❌ Grid layout recovery failed in main process for {word}"
                        )
                        return
                except Exception as recovery_error:
                    print(f"❌ MAIN RECOVERY ERROR: {recovery_error}")
                    logger.error(
                        f"❌ Grid layout recovery error in main process for {word}: {recovery_error}"
                    )
                    return

            # GRID LAYOUT VERIFICATION: The grid layout should already exist from SequencePickerScrollWidget.__init__
            print(f"✅ GRID LAYOUT VERIFIED for {word} - using existing layout")
            logger.info(f"✅ Using existing grid layout for {word}")

            thumbnail_box = ThumbnailBoxFactory.create_thumbnail_box(
                browse_tab=self.browse_tab,
                word=word,
                thumbnails=thumbnails,
                in_sequence_viewer=False,
                use_integrated=True,
            )

            # CRITICAL FIX: Ensure proper parent assignment before adding to layout
            if not thumbnail_box.parent():
                thumbnail_box.setParent(scroll_widget.scroll_content)

            # Add to scroll widget's tracking
            scroll_widget.add_thumbnail_box(word, thumbnail_box)

            # Grid positioning with bounds checking
            columns_per_row = 3
            row = index // columns_per_row
            col = index % columns_per_row

            # CRITICAL FIX: Verify grid layout is ready before adding widget
            if scroll_widget.grid_layout:
                scroll_widget.grid_layout.addWidget(thumbnail_box, row, col)
                thumbnail_box.show()

                logger = logging.getLogger(__name__)
                logger.debug(f"✅ Added thumbnail {word} to grid at ({row}, {col})")
            else:
                logger = logging.getLogger(__name__)
                logger.error(f"❌ Grid layout not available for thumbnail {word}")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error creating single thumbnail for {word}: {e}")
            import traceback

            traceback.print_exc()

    def _create_and_show_thumbnails_chunked(self, skip_scaling: bool = True):
        """Create and show thumbnails one at a time to prevent UI blocking."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        try:
            sequences = self.browse_tab.sequence_picker.currently_displayed_sequences

            if not sequences:
                return

            self.browse_tab.sequence_picker.scroll_widget.clear_layout()

            # ULTRA RESPONSIVE: Load one thumbnail at a time
            self._current_item_index = 0
            self._sequences_to_process = sequences
            self._skip_scaling = skip_scaling

            self._process_next_single_thumbnail()

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in chunked thumbnail creation: {e}")

    def _process_next_single_thumbnail(self):
        """Process one thumbnail at a time for maximum responsiveness."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        try:
            if self._current_item_index >= len(self._sequences_to_process):
                self._finalize_chunked_update()
                return

            # Process single item
            word, thumbnails, length = self._sequences_to_process[
                self._current_item_index
            ]

            try:
                from .thumbnail_box.factory import ThumbnailBoxFactory

                thumbnail_box = ThumbnailBoxFactory.create_thumbnail_box(
                    browse_tab=self.browse_tab,
                    word=word,
                    thumbnails=thumbnails,
                    in_sequence_viewer=False,
                    use_integrated=True,
                )

                self.browse_tab.sequence_picker.scroll_widget.add_thumbnail_box(
                    word, thumbnail_box
                )

                # Grid positioning
                columns_per_row = 3
                row = self._current_item_index // columns_per_row
                col = self._current_item_index % columns_per_row

                scroll_widget = self.browse_tab.sequence_picker.scroll_widget

                # GRID LAYOUT RECOVERY: Ensure grid layout exists before adding widget
                if (
                    not hasattr(scroll_widget, "grid_layout")
                    or not scroll_widget.grid_layout
                ):
                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"❌ CRITICAL: grid_layout missing/None in chunked process for {word} - RECOVERING"
                    )
                    print(
                        f"❌ CRITICAL: grid_layout missing/None in chunked process for {word} - ATTEMPTING RECOVERY"
                    )

                    # EMERGENCY GRID LAYOUT RECOVERY: Force re-initialization
                    try:
                        print(
                            f"🚨 EMERGENCY CHUNKED: Re-initializing grid layout for {word}"
                        )
                        scroll_widget._setup_layout()  # Call the setup method to recreate the grid layout

                        # Verify recovery worked
                        if (
                            hasattr(scroll_widget, "grid_layout")
                            and scroll_widget.grid_layout
                        ):
                            print(
                                f"✅ CHUNKED RECOVERY SUCCESS: Grid layout restored for {word}"
                            )
                            logger.info(
                                f"✅ Grid layout successfully recovered in chunked process for {word}"
                            )
                        else:
                            print(
                                f"❌ CHUNKED RECOVERY FAILED: Could not restore grid layout for {word}"
                            )
                            logger.error(
                                f"❌ Grid layout recovery failed in chunked process for {word}"
                            )
                            return
                    except Exception as recovery_error:
                        print(f"❌ CHUNKED RECOVERY ERROR: {recovery_error}")
                        logger.error(
                            f"❌ Grid layout recovery error in chunked process for {word}: {recovery_error}"
                        )
                        return

                scroll_widget.grid_layout.addWidget(thumbnail_box, row, col)
                thumbnail_box.show()

                logger = logging.getLogger(__name__)
                logger.debug(f"✅ Added thumbnail {word} to grid at ({row}, {col})")

            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating thumbnail for {word}: {e}")

            QApplication.processEvents()

            self._current_item_index += 1

            # PERFORMANCE OPTIMIZATION: Ultra-responsive delay for 60fps target
            QTimer.singleShot(
                1, self._process_next_single_thumbnail
            )  # 1ms for maximum responsiveness

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing single thumbnail: {e}")
            self._finalize_chunked_update()

    def _finalize_chunked_update(self):
        """Finalize the chunked update process."""
        try:
            # Hide loading indicators
            if hasattr(self.browse_tab, "hide_loading_state"):
                self.browse_tab.hide_loading_state()

            # Hide modern progress bar
            if hasattr(self.browse_tab.sequence_picker, "modern_progress_bar"):
                self.browse_tab.sequence_picker.modern_progress_bar.hide()

            # CRITICAL FIX: Force layout update to ensure thumbnails are visible
            scroll_widget = self.browse_tab.sequence_picker.scroll_widget
            scroll_widget.grid_layout.update()
            scroll_widget.scroll_content.updateGeometry()
            scroll_widget.scroll_area.updateGeometry()

            # SIDEBAR FIX: Ensure sidebar is visible and functional after chunked loading
            nav_sidebar = self.browse_tab.sequence_picker.nav_sidebar
            nav_sidebar.show()
            nav_sidebar.setVisible(True)  # Explicitly ensure visibility
            nav_sidebar.updateGeometry()
            nav_sidebar.update()  # Force redraw

            # SIDEBAR FIX: Update sidebar content if needed
            if hasattr(nav_sidebar, "manager") and hasattr(
                nav_sidebar.manager, "update_sidebar"
            ):
                try:
                    # Refresh sidebar sections
                    sections = getattr(self.browse_tab.sequence_picker, "sections", {})
                    sort_order = self.settings_manager.browse_settings.get_sort_method()
                    nav_sidebar.manager.update_sidebar(sections, sort_order)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error updating sidebar after chunked loading: {e}")

            # LAYOUT FIX: Update the entire sequence picker layout
            self.browse_tab.sequence_picker.updateGeometry()
            self.browse_tab.sequence_picker.update()

            # LAYOUT FIX: Ensure internal stack shows sequence picker after loading
            if hasattr(self.browse_tab, "internal_left_stack"):
                self.browse_tab.internal_left_stack.setCurrentIndex(
                    1
                )  # Show sequence picker

            # Apply styling
            background_type = (
                self.settings_manager.global_settings.get_background_type()
            )
            self.thumbnail_updater.apply_thumbnail_styling(background_type)

            # Update count label
            total_count = len(
                self.browse_tab.sequence_picker.currently_displayed_sequences
            )
            if hasattr(self.browse_tab.sequence_picker, "control_panel"):
                self.browse_tab.sequence_picker.control_panel.count_label.setText(
                    f"Number of words: {total_count}"
                )

            # Clean up processing variables
            if hasattr(self, "_current_item_index"):
                delattr(self, "_current_item_index")
            if hasattr(self, "_sequences_to_process"):
                delattr(self, "_sequences_to_process")
            if hasattr(self, "_skip_scaling"):
                delattr(self, "_skip_scaling")

            logger = logging.getLogger(__name__)
            logger.info(
                f"✅ Chunked UI update completed successfully - {total_count} sequences displayed"
            )

            # Restore window title
            if hasattr(self.browse_tab, "main_widget") and hasattr(
                self.browse_tab.main_widget, "main_window"
            ):
                main_window = self.browse_tab.main_widget.main_window
                title = main_window.windowTitle()
                if "Loading" in title and "sequences..." in title:
                    # Remove loading text from title
                    original_title = (
                        title.split(" - ")[-1]
                        if " - " in title
                        else "The Kinetic Constructor"
                    )
                    main_window.setWindowTitle(original_title)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error finalizing chunked update: {e}")

    def _ensure_scroll_widget_ready(self) -> bool:
        """
        Ensure the scroll widget is fully initialized and ready to accept child widgets.

        Returns:
            True if scroll widget is ready, False otherwise
        """
        try:
            scroll_widget = self.browse_tab.sequence_picker.scroll_widget
            logger = logging.getLogger(__name__)

            # Check if scroll widget exists
            if not scroll_widget:
                logger.debug("❌ Scroll widget does not exist")
                return False

            # Check if scroll widget has a parent (is properly attached)
            if not scroll_widget.parent():
                logger.debug("❌ Scroll widget has no parent")
                return False

            # FLEXIBLE CHECK: Different scroll widget implementations have different attributes
            # Check for grid layout (most common case)
            if hasattr(scroll_widget, "grid_layout"):
                if not scroll_widget.grid_layout:
                    logger.debug("❌ Grid layout exists but is None")
                    return False
                logger.debug("✅ Grid layout found and ready")
            else:
                # Check for modern scroll widget or other implementations
                if hasattr(scroll_widget, "layout") and scroll_widget.layout():
                    logger.debug("✅ Alternative layout found")
                else:
                    logger.debug("❌ No layout found in scroll widget")
                    return False

            # FLEXIBLE CHECK: Look for scroll area or container
            has_scroll_area = (
                (hasattr(scroll_widget, "scroll_area") and scroll_widget.scroll_area)
                or (
                    hasattr(scroll_widget, "scroll_content")
                    and scroll_widget.scroll_content
                )
                or (
                    # Modern scroll widget might have different structure
                    hasattr(scroll_widget, "modern_integration")
                )
            )

            if not has_scroll_area:
                logger.debug("❌ No scroll area or content container found")
                return False

            # Force layout update to ensure everything is ready
            try:
                scroll_widget.updateGeometry()
                if hasattr(scroll_widget, "grid_layout") and scroll_widget.grid_layout:
                    scroll_widget.grid_layout.update()
                logger.debug("✅ Layout updated successfully")
            except Exception as layout_error:
                logger.debug(f"⚠️ Layout update failed but continuing: {layout_error}")

            logger.debug("✅ Scroll widget readiness check passed")
            return True

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking scroll widget readiness: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _check_cached_thumbnails_available(self, sequences: list) -> int:
        """
        Check how many thumbnails are available in cache with detailed logging.

        Args:
            sequences: List of (word, thumbnails, length) tuples

        Returns:
            Number of sequences with cached thumbnails
        """
        try:
            from .thumbnail_box.components.image_loading_manager import (
                ImageLoadingManager,
                BROWSE_CACHE_AVAILABLE,
            )
            from PyQt6.QtCore import QSize

            logger = logging.getLogger(__name__)
            logger.info(
                f"🔍 Cache availability check: BROWSE_CACHE_AVAILABLE = {BROWSE_CACHE_AVAILABLE}"
            )

            if not BROWSE_CACHE_AVAILABLE:
                logger.warning("❌ Browse cache not available - returning 0")
                return 0

            # Get browse cache and log its current state
            from main_window.main_widget.browse_tab.cache.browse_image_cache import (
                get_browse_cache,
            )

            browse_cache = get_browse_cache()
            initial_stats = browse_cache.get_cache_stats()
            logger.info(f"📊 Initial cache stats: {initial_stats}")

            target_size = QSize(200, 150)  # Standard thumbnail size
            cached_count = 0
            checked_count = 0
            sample_paths = []

            for word, thumbnails, length in sequences:
                if thumbnails and len(thumbnails) > 0:
                    checked_count += 1
                    image_path = thumbnails[0]

                    # Log first few paths for debugging
                    if len(sample_paths) < 5:
                        sample_paths.append(f"{word}: {image_path}")

                    cached_pixmap = browse_cache.get_cached_image(
                        image_path, target_size
                    )

                    if cached_pixmap and not cached_pixmap.isNull():
                        cached_count += 1
                        if cached_count <= 3:  # Log first few hits
                            logger.debug(f"✅ Cache HIT for {word}: {image_path}")
                    else:
                        if checked_count <= 3:  # Log first few misses
                            logger.debug(f"❌ Cache MISS for {word}: {image_path}")

            # Log detailed results
            logger.info(f"🔍 Cache check complete:")
            logger.info(f"   Total sequences: {len(sequences)}")
            logger.info(f"   Sequences with thumbnails: {checked_count}")
            logger.info(f"   Cache hits: {cached_count}")
            logger.info(
                f"   Cache hit rate: {(cached_count/checked_count*100) if checked_count > 0 else 0:.1f}%"
            )

            # Log sample paths for debugging
            logger.info(f"📁 Sample image paths checked:")
            for sample in sample_paths:
                logger.info(f"   {sample}")

            # Log final cache stats
            final_stats = browse_cache.get_cache_stats()
            logger.info(f"📊 Final cache stats: {final_stats}")

            return cached_count

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error checking cached thumbnails: {e}")
            import traceback

            traceback.print_exc()
            return 0

    def _create_thumbnails_from_cache(self, sequences: list):
        """
        Create thumbnails using cached images for instant display.

        Args:
            sequences: List of (word, thumbnails, length) tuples
        """
        try:
            from PyQt6.QtCore import QSize
            from .thumbnail_box.factory import ThumbnailBoxFactory

            logger = logging.getLogger(__name__)
            logger.info("🚀 Creating thumbnails from cache for instant display")

            # Clear layout first
            self.browse_tab.sequence_picker.scroll_widget.clear_layout()

            target_size = QSize(200, 150)
            scroll_widget = self.browse_tab.sequence_picker.scroll_widget

            for index, (word, thumbnails, length) in enumerate(sequences):
                try:
                    # Create thumbnail box
                    thumbnail_box = ThumbnailBoxFactory.create_thumbnail_box(
                        browse_tab=self.browse_tab,
                        word=word,
                        thumbnails=thumbnails,
                        in_sequence_viewer=False,
                        use_integrated=True,
                    )

                    # Ensure proper parent assignment
                    if not thumbnail_box.parent():
                        thumbnail_box.setParent(scroll_widget.scroll_content)

                    # Add to scroll widget tracking
                    scroll_widget.add_thumbnail_box(word, thumbnail_box)

                    # Grid positioning
                    columns_per_row = 3
                    row = index // columns_per_row
                    col = index % columns_per_row

                    # Add to layout
                    scroll_widget.grid_layout.addWidget(thumbnail_box, row, col)
                    thumbnail_box.show()

                    # The thumbnail will load its cached image automatically through ImageLoadingManager

                except Exception as e:
                    logger.error(f"Error creating cached thumbnail for {word}: {e}")

            logger.info(f"✅ Created {len(sequences)} thumbnails from cache")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating thumbnails from cache: {e}")
            # Fallback to regular creation
            self.browse_tab.sequence_picker.scroll_widget.clear_layout()
            self._create_thumbnails_normally(sequences)

    def _create_thumbnails_normally(self, sequences: list):
        """
        Create thumbnails using the normal chunked process.

        Args:
            sequences: List of (word, thumbnails, length) tuples
        """
        try:
            logger = logging.getLogger(__name__)
            logger.info("🔄 Creating thumbnails using normal process")

            # Process thumbnails in small chunks
            chunk_size = 5
            total_processed = 0

            for i in range(0, len(sequences), chunk_size):
                # Check for cancellation
                if self._loading_cancelled:
                    logger.info("🚫 Loading cancelled during normal thumbnail creation")
                    return

                # Process chunk
                chunk = sequences[i : i + chunk_size]
                for word, thumbnails, length in chunk:
                    if self._loading_cancelled:
                        return

                    try:
                        self._create_single_thumbnail(word, thumbnails, total_processed)
                        total_processed += 1

                        # Update progress bar
                        if hasattr(
                            self.browse_tab.sequence_picker, "modern_progress_bar"
                        ):
                            self.browse_tab.sequence_picker.modern_progress_bar.set_current(
                                total_processed
                            )

                    except Exception as e:
                        logger.error(f"Error creating thumbnail for {word}: {e}")

                # Process events to keep UI responsive
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()

                # Small delay
                if i + chunk_size < len(sequences):
                    import time

                    time.sleep(0.001)

            logger.info(f"✅ Created {total_processed} thumbnails normally")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in normal thumbnail creation: {e}")

    def _show_immediate_loading_feedback(self, total_count: int):
        """Show immediate loading feedback to prevent UI freeze appearance."""
        try:
            logger = logging.getLogger(__name__)
            logger.info(
                f"🚀 Starting immediate loading feedback for {total_count} sequences"
            )

            # Show progress bar immediately
            if hasattr(self.browse_tab.sequence_picker, "modern_progress_bar"):
                self.browse_tab.sequence_picker.modern_progress_bar.set_maximum(
                    total_count
                )
                self.browse_tab.sequence_picker.modern_progress_bar.set_current(0)
                self.browse_tab.sequence_picker.modern_progress_bar.show()

            # Update window title to show loading
            if hasattr(self.browse_tab, "main_widget") and hasattr(
                self.browse_tab.main_widget, "main_window"
            ):
                main_window = self.browse_tab.main_widget.main_window
                original_title = main_window.windowTitle()
                main_window.setWindowTitle(
                    f"Loading {total_count} sequences... - {original_title}"
                )

            # Force immediate UI update
            from PyQt6.QtWidgets import QApplication

            QApplication.processEvents()

            logger.info("✅ Immediate loading feedback displayed")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error showing immediate loading feedback: {e}")
