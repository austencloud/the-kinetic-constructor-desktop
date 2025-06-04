import logging
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QWidget,
    QLabel,
    QFrame,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


from ..generation.generation_controls import GenerationControlsPanel
from ..core.mode_manager import SequenceCardMode
from ..components.progressive_layout_manager import ProgressiveLayoutManager

# Enhanced sequence cards temporarily disabled for stability
from ..ui_manager import SequenceCardUIManager  # Added for type hint
from ..generation.generation_manager import GenerationManager  # Added for type hint
from ..generation.generated_sequence_store import (
    GeneratedSequenceStore,
)  # Added for type hint

from typing import (
    TYPE_CHECKING,
    List,
    Any,
)  # Added Any for sequence_data, consider a specific type

if TYPE_CHECKING:
    from main_window.main_widget.sequence_workbench.sequence_beat_frame.image_export_manager.image_export_manager import (
        ImageExportManager,
    )
    from ..tab import SequenceCardTab
    from ..generation.generation_manager import GenerationParams
    from main_window.main_widget.main_widget import (
        MainWidget,
    )  # For self.tab.main_widget
    from main_window.main_widget.sequence_workbench.sequence_workbench import (
        SequenceWorkbench,
    )  # For sequence_workbench

    # Define a type for sequence_data if possible, e.g., a TypedDict or a class
    # from .generation.generation_types import GeneratedSequenceData # Example


class SequenceCardGenerationModeController:
    def __init__(self, tab: "SequenceCardTab"):
        self.tab: "SequenceCardTab" = tab
        self.ui_manager: SequenceCardUIManager = tab.ui_manager
        self.generation_manager: GenerationManager = tab.generation_manager
        self.generated_sequence_store: GeneratedSequenceStore = (
            tab.generated_sequence_store
        )
        self.generation_controls: GenerationControlsPanel | None = None
        self._pending_batch_sequences: List[Any] = []  # Use specific type if available
        self._expected_batch_size: int = 0

        # Progressive layout manager for placeholder-based loading
        self.progressive_layout_manager = ProgressiveLayoutManager(tab)
        self._progressive_mode_active = False

        # Enhanced sequence cards temporarily disabled for stability

    def activate(self) -> None:
        """Activates generation mode."""
        if not self.generation_manager.is_available():
            self.ui_manager.set_header_description(
                "Initializing generation mode dependencies..."
            )
            QApplication.processEvents()  # Update UI immediately
            if not self.generation_manager._refresh_generate_tab_reference():
                self.tab.mode_manager.switch_mode(SequenceCardMode.DICTIONARY)  # Revert
                self.ui_manager.set_header_description(
                    "Generation mode unavailable - Could not initialize required dependencies."
                )
                return

        self.ui_manager.set_header_description("Generate new sequences on-demand")
        if self.tab.nav_sidebar.scroll_area:
            self.tab.nav_sidebar.scroll_area.setVisible(False)
        if self.tab.nav_sidebar.level_filter:
            self.tab.nav_sidebar.level_filter.setVisible(False)

        self._ensure_generation_controls()
        if self.generation_controls:
            self.generation_controls.setVisible(True)

        self.ui_manager.clear_content_area()

        # Reset page layout state for new session
        if hasattr(self, "_current_page_layout_initialized"):
            delattr(self, "_current_page_layout_initialized")

        # Show existing approved sequences if any, otherwise show empty state
        approved_sequences = self.generated_sequence_store.get_all_sequences()
        approved_count = len(
            [seq for seq in approved_sequences if getattr(seq, "approved", False)]
        )

        if approved_count > 0:
            self._display_approved_sequences_as_pages()
        else:
            self.ui_manager.set_header_description(
                "Generate sequences to see them laid out on pages for printing"
            )

    def deactivate(self) -> None:
        """Deactivates generation mode."""
        if self.generation_controls:
            self.generation_controls.setVisible(False)

    def _ensure_generation_controls(self) -> None:
        if self.generation_controls is None:
            # Pass the settings_manager from the tab to the controls panel
            settings_manager = self.tab.main_widget.app_context.settings_manager
            self.generation_controls = GenerationControlsPanel(
                settings_manager=settings_manager
            )
            self.generation_controls.generate_requested.connect(
                self.on_generate_requested
            )
            self.generation_controls.clear_requested.connect(
                self.on_clear_generated_requested
            )
            sidebar_layout = self.tab.nav_sidebar.layout()
            if sidebar_layout:
                sidebar_layout.insertWidget(
                    sidebar_layout.count() - 1, self.generation_controls
                )

    def on_generate_requested(
        self, params: "GenerationParams", batch_size: int
    ) -> None:
        if self.tab.is_initializing:
            logging.info("Ignoring generation request during initialization")
            return

        logging.info(
            f"Using generation controls parameters directly: {params.__dict__}"
        )

        # Initialize progressive layout for batch generation
        if batch_size > 1:
            self._pending_batch_sequences = []
            self._expected_batch_size = batch_size

            # Initialize placeholder-based progressive layout
            if self.progressive_layout_manager.initialize_progressive_layout(
                batch_size
            ):
                self._progressive_mode_active = True
                self.ui_manager.set_header_description(
                    f"Generating {batch_size} sequences - placeholders created, generation starting..."
                )
            else:
                self._progressive_mode_active = False
                self.ui_manager.set_header_description(
                    f"Generating {batch_size} sequences - fallback to completion display"
                )

            self.generation_manager.generate_batch(params, batch_size)
        else:
            # Single sequence generation - no progressive layout needed
            self._progressive_mode_active = False
            self.generation_manager.generate_single_sequence(params)

    def on_sequence_generated(
        self, sequence_data: Any
    ) -> None:  # Use specific type if available
        """
        Handle a newly generated sequence with placeholder-based progressive display.
        Each sequence replaces a placeholder immediately upon generation.
        """
        # Immediately add the sequence to the approved store
        self.generated_sequence_store.add_approved_sequence(sequence_data)

        # Add to pending batch for tracking
        self._pending_batch_sequences.append(sequence_data)

        # PROGRESSIVE PLACEHOLDER REPLACEMENT
        if self._progressive_mode_active:
            # Replace the next placeholder with this sequence
            success = self.progressive_layout_manager.replace_placeholder_with_sequence(
                sequence_data
            )
            if success:
                progress_info = self.progressive_layout_manager.get_progress_info()
                self.ui_manager.set_header_description(
                    f"Generated {progress_info['completed']}/{progress_info['total_expected']} sequences - "
                    f"{progress_info['placeholders_remaining']} placeholders remaining"
                )
            else:
                logging.warning(
                    "Failed to replace placeholder - falling back to completion display"
                )
                self._progressive_mode_active = False
        else:
            # Fallback to original behavior for single sequences or if progressive mode failed
            total_generated = len(self._pending_batch_sequences)
            if self._expected_batch_size > 0:
                self.ui_manager.set_header_description(
                    f"Generated {total_generated}/{self._expected_batch_size} sequences - "
                    f"Will display at completion"
                )
            else:
                self.ui_manager.set_header_description(
                    f"Generated {total_generated} sequence - Will display at completion"
                )

        # Check if batch is complete
        if (
            len(self._pending_batch_sequences) >= self._expected_batch_size
            and self._expected_batch_size > 0
        ):
            self._on_batch_generation_complete()
        elif self._expected_batch_size == 0:  # Single generation
            self._on_single_generation_complete()

    # PROGRESSIVE DISPLAY METHOD COMPLETELY REMOVED TO PREVENT DUPLICATION
    # The progressive display approach was causing each sequence to be displayed multiple times
    # because display_sequences() rebuilds the entire layout each time it's called.
    # Now using single display at batch completion only.

    # PROGRESSIVE LAYOUT INITIALIZATION METHOD ALSO REMOVED

    def _on_batch_generation_complete(self) -> None:
        """Handle completion of batch generation."""
        total_count = len(self._pending_batch_sequences)

        if self._progressive_mode_active:
            # Progressive mode: all placeholders should already be replaced
            self.ui_manager.set_header_description(
                f"Generated {total_count} sequences - All placeholders replaced, ready for printing and curation"
            )
            # Reset progressive mode
            self._progressive_mode_active = False
        else:
            # Fallback mode: display all sequences at once
            self._display_all_generated_sequences_once()
            self.ui_manager.set_header_description(
                f"Generated {total_count} sequences - Ready for printing and curation"
            )

        self._pending_batch_sequences = []
        self._expected_batch_size = 0

    def _on_single_generation_complete(self) -> None:
        """Handle completion of single sequence generation."""
        # Single sequences always use completion display (no progressive mode)
        self._display_all_generated_sequences_once()

        self.ui_manager.set_header_description(
            "Generated 1 sequence - Ready for printing"
        )
        self._pending_batch_sequences = []

    def _display_all_generated_sequences_once(self) -> None:
        """
        Display all generated sequences exactly once using the printable displayer.
        This method ensures no duplication by calling display_sequences() only once.
        """
        try:
            # Force GENERATION mode to ensure only generated sequences are shown
            from ..core.mode_manager import SequenceCardMode

            # Temporarily store the current mode
            original_mode = None
            if hasattr(self.tab, "mode_manager") and self.tab.mode_manager:
                original_mode = self.tab.mode_manager.current_mode
                # Force GENERATION mode to ensure only generated sequences are shown
                self.tab.mode_manager.current_mode = SequenceCardMode.GENERATION

            # Use the printable displayer to display all sequences ONCE
            if (
                self.tab.USE_PRINTABLE_LAYOUT
                and hasattr(self.tab, "printable_displayer")
                and self.tab.printable_displayer
            ):
                # Ensure the column count is applied from Preview Columns setting
                self._apply_preview_columns_setting()

                # Single call to display all sequences
                self.tab.printable_displayer.display_sequences()
                self.tab._sync_pages_from_displayer()
            else:
                # Fallback to card-based display if printable layout not available
                self._display_generated_sequences()

            # Restore original mode if it was changed
            if (
                original_mode
                and hasattr(self.tab, "mode_manager")
                and self.tab.mode_manager
            ):
                self.tab.mode_manager.current_mode = original_mode

        except Exception as e:
            logging.error(f"Error displaying all generated sequences: {e}")
            # Fallback to simple display
            self._display_generated_sequences()

    def on_generation_failed(self, error_message: str) -> None:
        self.ui_manager.set_header_description(f"Generation failed: {error_message}")

    def on_generation_progress(self, current: int, total: int) -> None:
        if self.generation_controls:
            self.generation_controls.show_progress(current, total)

    def on_clear_generated_requested(self) -> None:
        """Clear all generated sequences and reset the page layout."""
        self.generated_sequence_store.clear_all_sequences()

        # Reset progressive layout state
        self.progressive_layout_manager.cleanup()
        self._progressive_mode_active = False

        # Reset legacy state variables
        if hasattr(self, "_progressive_layout_initialized"):
            delattr(self, "_progressive_layout_initialized")
        if hasattr(self, "_current_page_layout_initialized"):
            delattr(self, "_current_page_layout_initialized")
        if hasattr(self, "_current_page_sequences"):
            self._current_page_sequences = []

        # Clear content area and show empty state
        self.ui_manager.clear_content_area()
        self.ui_manager.set_header_description(
            "Generate sequences to see them laid out on pages for printing"
        )

    def _display_generated_sequences(self) -> None:
        count = self.generated_sequence_store.get_sequence_count()
        if count == 0:
            self.ui_manager.set_header_description(
                "No generated sequences. Use the controls to generate some!"
            )
            self.ui_manager.clear_content_area()
        else:
            self.ui_manager.set_header_description(
                f"Showing {count} generated sequences"
            )
            self._render_generated_sequence_cards()

    def _render_generated_sequence_cards(self) -> None:
        try:
            self.ui_manager.clear_content_area()
            sequences = self.generated_sequence_store.get_all_sequences()
            if not sequences:
                return

            container_widget = QWidget()
            grid_layout = QGridLayout(container_widget)
            grid_layout.setSpacing(20)
            grid_layout.setContentsMargins(20, 20, 20, 20)

            columns = min(3, len(sequences))
            # rows = (len(sequences) + columns - 1) // columns # Not strictly needed for adding widgets

            for i, sequence_data in enumerate(sequences):
                row = i // columns
                col = i % columns
                card = self._create_sequence_card(sequence_data)
                grid_layout.addWidget(card, row, col)

            self.tab.content_area.scroll_layout.addWidget(container_widget)
        except Exception as e:
            logging.error(f"Error rendering generated sequence cards: {e}")
            self.ui_manager.set_header_description(
                f"Error displaying sequences: {str(e)}"
            )

    def _create_sequence_card(self, sequence_data: Any) -> QFrame:  # Use specific type
        try:
            card = QFrame()
            card.setFixedSize(280, 350)
            card.setStyleSheet(
                """
                QFrame {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                    padding: 10px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
            """
            )
            layout = QVBoxLayout(card)
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)

            image_label = QLabel()
            image_label.setFixedSize(250, 200)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet(
                """
                QLabel {
                    background: rgba(0, 0, 0, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                }
            """
            )
            pixmap = self._generate_sequence_card_image(sequence_data)
            if pixmap and not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("Generating...")
                image_label.setStyleSheet(
                    image_label.styleSheet()
                    + """
                    color: #e1e5e9;
                    font-size: 12px;
                """
                )
            layout.addWidget(image_label)

            info_label = QLabel()
            info_label.setText(
                f"<b>{sequence_data.word}</b><br>"
                f"Length: {sequence_data.params.length} beats<br>"
                f"Level: {sequence_data.params.level}<br>"
                f"Mode: {sequence_data.params.generation_mode.title()}"
            )
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setStyleSheet(
                """
                QLabel {
                    color: #e1e5e9;
                    font-size: 11px;
                    background: transparent;
                    border: none;
                    padding: 5px;
                }
            """
            )
            layout.addWidget(info_label)

            button_layout = QHBoxLayout()
            export_btn = QPushButton("Export")
            export_btn.setFixedSize(60, 25)
            export_btn.setStyleSheet(
                """
                QPushButton {
                    background: rgba(100, 150, 255, 0.8);
                    border: 1px solid rgba(100, 150, 255, 1.0);
                    border-radius: 4px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(100, 150, 255, 1.0);
                }
            """
            )
            export_btn.clicked.connect(
                lambda: self._export_generated_sequence(sequence_data)
            )

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedSize(60, 25)
            remove_btn.setStyleSheet(
                """
                QPushButton {
                    background: rgba(255, 100, 100, 0.8);
                    border: 1px solid rgba(255, 100, 100, 1.0);
                    border-radius: 4px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 100, 100, 1.0);
                }
            """
            )
            remove_btn.clicked.connect(
                lambda: self._remove_generated_sequence(sequence_data)
            )

            button_layout.addWidget(export_btn)
            button_layout.addWidget(remove_btn)
            button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addLayout(button_layout)
            return card
        except Exception as e:
            logging.error(f"Error creating sequence card: {e}")
            error_card = QFrame()
            error_card.setFixedSize(280, 350)
            error_layout = QVBoxLayout(error_card)
            error_label = QLabel(f"Error creating card:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_layout.addWidget(error_label)
            return error_card

    def _generate_sequence_card_image(
        self, sequence_data: Any
    ) -> QPixmap | None:  # Use specific type
        try:
            # Use the isolated SequenceCardImageExporter instead of the actual beat frame
            # This prevents contamination of the user's work in the construct/generate tabs
            if not self.tab.image_exporter:
                logging.error("No isolated image exporter available")
                return None

            # Load sequence into the isolated temp beat frame
            self.tab.image_exporter.temp_beat_frame.load_sequence(
                sequence_data.sequence_data
            )

            # Calculate optimal scale factor for consistent sizing across all display modes
            scale_factor = self._calculate_optimal_scale_factor_for_completion_display()

            # Page-optimized generation options (consistent with progressive loading)
            options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": False,  # Skip for speed
                "add_user_info": True,
                "add_word": True,
                "add_difficulty_level": True,
                "include_start_position": True,  # Enable start position for completion display
                "combined_grids": False,
                "additional_height_top": 0,  # Will be calculated by HeightDeterminer
                "additional_height_bottom": 0,  # Will be calculated by HeightDeterminer
                "dynamic_scale_factor": scale_factor,  # Apply reverse-calculated scale factor
            }

            logging.info(
                f"🎨 Completion display using scale factor: {scale_factor:.3f}"
            )

            # Use the isolated export manager to create the image with scale factor
            qimage = self.tab.image_exporter.export_manager.image_creator.create_sequence_image(
                sequence_data.sequence_data,
                options,
                dictionary=False,  # Not for dictionary storage
                fullscreen_preview=False,
                override_word=sequence_data.word,
            )
            pixmap = QPixmap.fromImage(qimage)

            logging.info(f"✅ Generated completion display image: {pixmap.size()}")
            return pixmap
        except Exception as e:
            logging.error(f"Error generating sequence card image: {e}")
            return None

    def _calculate_optimal_scale_factor_for_completion_display(self) -> float:
        """
        Calculate the optimal scale factor for completion display using the same
        reverse-calculation approach as the progressive loading system.

        This ensures consistent sizing across all generation modes.

        Returns:
            float: Scale factor to apply to the image creator
        """
        try:
            # Use the same target size as the progressive loading system
            target_size = self.tab.page_factory.get_cell_size()

            # Base pictograph size is hardcoded at 950x950 throughout the system
            BASE_PICTOGRAPH_SIZE = 950

            # Step 1: Get the actual layout that would be used for image generation
            try:
                # Use the same layout calculation as the image creator for accuracy
                layout_handler = self.tab.image_exporter.export_manager.layout_handler
                columns, rows = layout_handler.calculate_layout(
                    16,  # Typical sequence length
                    True,  # Include start position
                )
                logging.debug(f"Completion display layout: {columns}x{rows}")
            except Exception as e:
                # Fallback to safe estimates if layout calculation fails
                logging.warning(f"Layout calculation failed, using fallback: {e}")
                columns, rows = (
                    5,
                    4,
                )  # Conservative estimate for 16-beat + start position

            # Step 2: Calculate what the full-size image dimensions would be
            core_image_width = columns * BASE_PICTOGRAPH_SIZE
            core_image_height = rows * BASE_PICTOGRAPH_SIZE

            # Estimate additional heights (using standard calculations)
            estimated_additional_height_top = 300  # Standard for word label
            estimated_additional_height_bottom = 150  # Standard for user info

            full_image_width = core_image_width
            full_image_height = (
                core_image_height
                + estimated_additional_height_top
                + estimated_additional_height_bottom
            )

            # Step 3: Calculate scale ratio based on available page space
            width_scale_ratio = target_size.width() / full_image_width
            height_scale_ratio = target_size.height() / full_image_height

            # Use the smaller ratio to ensure the image fits within the target size
            scale_factor = min(width_scale_ratio, height_scale_ratio)

            # Step 4: Apply safety bounds to prevent extreme scaling
            scale_factor = max(scale_factor, 0.05)  # Minimum 5% to maintain readability
            scale_factor = min(scale_factor, 1.0)  # Maximum 100% to prevent oversizing

            logging.info(f"🎯 COMPLETION DISPLAY SCALE FACTOR: {scale_factor:.3f}")
            logging.info(
                f"   📐 Layout: {columns}x{rows}, Full size: {full_image_width}x{full_image_height}"
            )
            logging.info(
                f"   📏 Target: {target_size}, Ratios: W={width_scale_ratio:.3f}, H={height_scale_ratio:.3f}"
            )

            return scale_factor

        except Exception as e:
            logging.error(f"Error calculating completion display scale factor: {e}")
            # Fallback to a conservative default that should work in most cases
            return 0.2  # 20% of original size

    def _export_generated_sequence(
        self, sequence_data: Any
    ) -> None:  # Use specific type
        try:
            # Use the isolated SequenceCardImageExporter for export
            # This prevents contamination of the user's work in the construct/generate tabs
            if not self.tab.image_exporter:
                logging.error("No isolated image exporter available for export")
                return

            # Load sequence into the isolated temp beat frame
            self.tab.image_exporter.temp_beat_frame.load_sequence(
                sequence_data.sequence_data
            )

            # Export using the isolated export manager
            self.tab.image_exporter.export_manager.export_image_directly(
                sequence_data.sequence_data
            )
        except Exception as e:
            logging.error(f"Error exporting generated sequence: {e}")

    def _remove_generated_sequence(
        self, sequence_data: Any
    ) -> None:  # Use specific type
        try:
            self.generated_sequence_store.remove_sequence(sequence_data.id)
            self._refresh_page_display_after_deletion()
        except Exception as e:
            logging.error(f"Error removing generated sequence: {e}")

    def _display_approved_sequences_as_pages(self) -> None:
        """
        Display approved sequences using the existing pagination system.
        This replaces individual sequence cards with paginated page previews.
        """
        # Get approved sequences from the store
        approved_sequences = self.generated_sequence_store.get_all_sequences()
        approved_count = len(
            [seq for seq in approved_sequences if getattr(seq, "approved", False)]
        )

        if approved_count == 0:
            self.ui_manager.set_header_description(
                "No approved sequences yet. Generate and approve some sequences!"
            )
            self.ui_manager.clear_content_area()
            return

        # Update header to show approved sequences
        self.ui_manager.set_header_description(
            f"Showing {approved_count} approved sequences as paginated previews ready for printing"
        )

        # Use the existing printable displayer to show approved sequences in paginated layout
        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            # Ensure the column count is applied from Preview Columns setting
            self._apply_preview_columns_setting()

            # Use the printable displayer to show generated sequences
            # The SequenceLoader will automatically include generated sequences
            self.tab.printable_displayer.display_sequences()
            self.tab._sync_pages_from_displayer()
        else:
            self.ui_manager.set_header_description(
                "Printable layout not available for approved sequences"
            )

    def _initialize_page_layout(self) -> None:
        """
        Initialize the page layout system for direct sequence generation.
        This sets up the printable displayer to show sequences as they're generated.
        """
        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            # Clear any existing content
            self.ui_manager.clear_content_area()

            # Initialize the page layout tracking
            self._current_page_sequences = []
            self._sequences_per_page = self._calculate_sequences_per_page()

            # Enhanced sequence cards temporarily disabled for stability

            # Update header to show we're ready for generation
            self.ui_manager.set_header_description(
                "Ready to generate sequences - they will appear as pages below"
            )
        else:
            self.ui_manager.set_header_description(
                "Page layout not available - using fallback display"
            )

    # Bulk operation handlers temporarily disabled for stability

    def _refresh_page_display_after_deletion(self) -> None:
        """Refresh the page display to show updated sequence layout after deletions."""
        try:
            # Use the existing printable displayer to refresh the layout
            if (
                self.tab.USE_PRINTABLE_LAYOUT
                and hasattr(self.tab, "printable_displayer")
                and self.tab.printable_displayer
            ):
                # Display sequences with current filters (this will reload from the store)
                self.tab.printable_displayer.display_sequences()
                self.tab._sync_pages_from_displayer()

                # Enhanced sequence cards temporarily disabled for stability

                logging.info("Page display refreshed after sequence deletion")
            else:
                self.ui_manager.set_header_description(
                    "Could not refresh page display - printable layout not available"
                )

        except Exception as e:
            logging.error(f"Error refreshing page display: {e}")
            self.ui_manager.set_header_description(
                f"Error refreshing display: {str(e)}"
            )

    def _apply_preview_columns_setting(self) -> None:
        """
        Apply the Preview Columns setting to the printable displayer.
        This ensures that generated sequences are displayed with the correct column count.
        """
        try:
            # Get the current Preview Columns setting
            if (
                hasattr(self.tab, "settings_manager_obj")
                and self.tab.settings_manager_obj
            ):
                column_count = self.tab.settings_manager_obj.saved_column_count
            else:
                # Fallback to reading from settings manager directly
                column_count = int(
                    self.tab.settings_manager.get_setting(
                        "sequence_card_tab", "column_count", 3
                    )
                )

            # Apply the column count to the printable displayer
            if (
                self.tab.USE_PRINTABLE_LAYOUT
                and hasattr(self.tab, "printable_displayer")
                and self.tab.printable_displayer
            ):
                self.tab.printable_displayer.set_columns_per_row(column_count)
                logging.debug(
                    f"Applied Preview Columns setting: {column_count} columns for generation mode"
                )

        except Exception as e:
            logging.warning(f"Failed to apply Preview Columns setting: {e}")
            # Use default of 3 columns if setting fails
            if (
                self.tab.USE_PRINTABLE_LAYOUT
                and hasattr(self.tab, "printable_displayer")
                and self.tab.printable_displayer
            ):
                self.tab.printable_displayer.set_columns_per_row(3)

    # Progressive layout methods removed - now using single display at completion

    def _refresh_page_display(self) -> None:
        """
        Refresh the page display with all currently approved sequences.
        This uses the existing printable displayer system.
        """
        if (
            self.tab.USE_PRINTABLE_LAYOUT
            and hasattr(self.tab, "printable_displayer")
            and self.tab.printable_displayer
        ):
            # Get all approved sequences from the store
            approved_sequences = self.generated_sequence_store.get_all_sequences()
            approved_count = len(
                [seq for seq in approved_sequences if getattr(seq, "approved", False)]
            )

            if approved_count > 0:
                # Use the printable displayer to show generated sequences
                # The SequenceLoader in the display manager will automatically include
                # generated sequences from the store
                self.tab.printable_displayer.display_sequences()
                self.tab._sync_pages_from_displayer()

                # Update header with current count
                self.ui_manager.set_header_description(
                    f"Showing {approved_count} generated sequences in page layout"
                )
            else:
                # Clear display if no sequences
                self.ui_manager.clear_content_area()
                self.ui_manager.set_header_description(
                    "No generated sequences to display"
                )
