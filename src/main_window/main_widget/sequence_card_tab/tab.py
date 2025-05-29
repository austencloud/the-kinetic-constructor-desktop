# src/main_window/main_widget/sequence_card_tab/tab.py
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QApplication
from PyQt6.QtCore import Qt, QTimer
from src.interfaces.settings_manager_interface import ISettingsManager
from src.interfaces.json_manager_interface import IJsonManager
from .content_area import SequenceCardContentArea
from .header import SequenceCardHeader
from .initializer import USE_PRINTABLE_LAYOUT, SequenceCardInitializer
from .resource_manager import SequenceCardResourceManager
from .settings_handler import SequenceCardSettingsHandler
from .components.navigation.sidebar import SequenceCardNavSidebar
from .components.pages.factory import SequenceCardPageFactory
from .core.refresher import SequenceCardRefresher
from .components.pages.printable_factory import PrintablePageFactory
from .components.pages.printable_layout import PaperSize, PaperOrientation
from .export.image_exporter import SequenceCardImageExporter
from .export.page_exporter import SequenceCardPageExporter
from .components.display.printable_displayer import PrintableDisplayer
from .core.mode_manager import SequenceCardModeManager, SequenceCardMode
from .generation.generation_manager import GenerationManager
from .generation.generation_controls import GenerationControlsPanel
from .generation.generated_sequence_store import GeneratedSequenceStore
from .generation.approval_dialog.approval_dialog import SequenceApprovalDialog
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class SequenceCardTab(QWidget):
    def __init__(
        self,
        main_widget: "MainWidget",
        settings_manager: ISettingsManager,
        json_manager: IJsonManager,
    ):
        super().__init__(main_widget)
        self.main_widget = main_widget
        self.settings_manager = settings_manager
        self.json_manager = json_manager
        self.global_settings = settings_manager.get_global_settings()

        self.pages = []
        self.initialized = False
        self.currently_displayed_length = 16
        self.is_initializing = True  # Start in initializing state
        self.load_start_time = 0

        self.settings_manager_obj = SequenceCardSettingsHandler(settings_manager)
        self.resource_manager = SequenceCardResourceManager(self)
        self.initializer = SequenceCardInitializer(self)
        self.content_area = SequenceCardContentArea(self)

        self._create_components()
        self.init_ui()

    def _create_components(self):
        self.nav_sidebar = SequenceCardNavSidebar(self)

        # Ensure sidebar length is properly initialized from settings
        saved_length = int(
            self.settings_manager.get_setting("sequence_card_tab", "last_length", 16)
        )
        self.nav_sidebar.selected_length = saved_length
        self.currently_displayed_length = saved_length

        # Update the sidebar UI to reflect the correct length
        if hasattr(self.nav_sidebar, "scroll_area"):
            self.nav_sidebar.scroll_area.update_selection(saved_length)

        if hasattr(self.settings_manager_obj, "saved_length"):
            self.nav_sidebar.selected_length = self.settings_manager_obj.saved_length
            self.currently_displayed_length = self.settings_manager_obj.saved_length

        # Load and set saved level preferences
        if (
            hasattr(self.settings_manager_obj, "saved_levels")
            and self.nav_sidebar.level_filter
        ):
            self.nav_sidebar.level_filter.set_selected_levels(
                self.settings_manager_obj.saved_levels
            )

        # Connect level filter changes
        self.nav_sidebar.level_filter_changed.connect(self._on_level_filter_changed)

        # Connect mode change requests
        self.nav_sidebar.mode_change_requested.connect(self._on_mode_change_requested)

        # Initialize generation components
        self.mode_manager = SequenceCardModeManager(self)
        self.generation_manager = GenerationManager(self)
        self.generated_sequence_store = GeneratedSequenceStore(self)
        self.generation_controls = None  # Will be created when needed

        # Connect generation signals
        self.generation_manager.sequence_generated.connect(self._on_sequence_generated)
        self.generation_manager.generation_failed.connect(self._on_generation_failed)
        self.generation_manager.batch_generation_progress.connect(
            self._on_generation_progress
        )

        if USE_PRINTABLE_LAYOUT:
            self.page_factory = PrintablePageFactory(self)
        else:
            self.page_factory = SequenceCardPageFactory(self)

        if USE_PRINTABLE_LAYOUT:
            self.printable_displayer = PrintableDisplayer(self)
            self.printable_displayer.set_paper_size(PaperSize.A4)
            self.printable_displayer.set_orientation(PaperOrientation.PORTRAIT)

            if hasattr(self.settings_manager_obj, "saved_column_count"):
                self.printable_displayer.columns_per_row = (
                    self.settings_manager_obj.saved_column_count
                )

        self.image_exporter = SequenceCardImageExporter(self)
        self.page_exporter = SequenceCardPageExporter(self)
        self.refresher = SequenceCardRefresher(self)
        self.pages = []

    def init_ui(self):
        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        self.header = SequenceCardHeader(self)
        self.layout.addWidget(self.header)

        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)

        sidebar_width = 200
        self.nav_sidebar.setFixedWidth(sidebar_width)
        self.nav_sidebar.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        self.content_layout.addWidget(self.nav_sidebar, 0)
        self.content_layout.addWidget(self.content_area.scroll_area, 1)

        self.layout.addLayout(self.content_layout, 1)

        if hasattr(self.nav_sidebar, "length_selected"):
            self.nav_sidebar.length_selected.connect(self._on_length_selected)

        # Complete mode manager initialization after sidebar is properly set up
        self.mode_manager.complete_initialization()

        # Complete initialization - now safe to trigger generation
        self.is_initializing = False

    def update_column_count(self, column_count: int):
        if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
            self.printable_displayer.set_columns_per_row(column_count)

    def _on_length_selected(self, length: int):
        self.currently_displayed_length = length
        self.settings_manager_obj.save_length(length)

        if self.is_initializing:
            return

        self.content_area.clear_layout()
        self.header.description_label.setText(
            f"Loading {length if length > 0 else 'all'}-step sequences..."
        )

        if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
            if (
                hasattr(self.printable_displayer, "manager")
                and self.printable_displayer.manager.is_loading
            ):
                logging.debug(
                    f"Cancelling in-progress loading operation before loading length {length}"
                )
                self.printable_displayer.manager.cancel_loading()

            self.printable_displayer.display_sequences(length)
            self._sync_pages_from_displayer()

    def _on_level_filter_changed(self, selected_levels: list):
        """Handle level filter changes and refresh the display."""
        # Save the level preferences
        self.settings_manager_obj.save_levels(selected_levels)

        if self.is_initializing:
            return

        # Clear current display
        self.content_area.clear_layout()

        # Update header to show loading state
        length_text = (
            f"{self.currently_displayed_length}-step"
            if self.currently_displayed_length > 0
            else "all"
        )
        if len(selected_levels) < 3:
            level_names = {1: "Basic", 2: "Intermediate", 3: "Advanced"}
            level_text = ", ".join(
                [level_names[lvl] for lvl in sorted(selected_levels)]
            )
            self.header.description_label.setText(
                f"Loading {length_text} sequences (Levels: {level_text})..."
            )
        else:
            self.header.description_label.setText(f"Loading {length_text} sequences...")

        # Refresh display with new level filter
        if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
            if (
                hasattr(self.printable_displayer, "manager")
                and self.printable_displayer.manager.is_loading
            ):
                logging.debug(
                    "Cancelling in-progress loading operation before applying level filter"
                )
                self.printable_displayer.manager.cancel_loading()

            # Pass both length and level filters to the display manager
            self.printable_displayer.display_sequences(
                self.currently_displayed_length, selected_levels
            )
            self._sync_pages_from_displayer()

    def _on_mode_change_requested(self, mode: SequenceCardMode):
        """Handle mode change requests from the sidebar."""
        # If switching to generation mode, ensure generate tab is available
        if mode == SequenceCardMode.GENERATION:
            # Force refresh of generate tab reference
            if not self.generation_manager.is_available():
                self.header.description_label.setText(
                    "Initializing generation mode... Please wait."
                )
                # Try to refresh again - this will attempt to create the tab
                self.generation_manager._refresh_generate_tab_reference()

        if self.mode_manager.switch_mode(mode):
            # Update UI based on new mode
            self._update_ui_for_mode(mode)

            # Update mode toggle state
            if self.nav_sidebar.mode_toggle:
                self.nav_sidebar.mode_toggle.set_current_mode(mode)

    def _update_ui_for_mode(self, mode: SequenceCardMode):
        """Update UI elements based on the current mode."""
        if mode == SequenceCardMode.DICTIONARY:
            # Show dictionary-specific controls
            if self.nav_sidebar.scroll_area:
                self.nav_sidebar.scroll_area.setVisible(True)
            if self.nav_sidebar.level_filter:
                self.nav_sidebar.level_filter.setVisible(True)

            # Hide generation controls
            if self.generation_controls:
                self.generation_controls.setVisible(False)

            # Update header
            self.header.description_label.setText(
                "Browse sequences from the dictionary"
            )

            # Reload dictionary sequences
            self.load_sequences()

        elif mode == SequenceCardMode.GENERATION:
            # Check if generation is available
            if not self.generation_manager.is_available():
                # Try to refresh dependencies first
                self.header.description_label.setText(
                    "Initializing generation mode dependencies..."
                )
                QApplication.processEvents()  # Update UI immediately

                # Force refresh of all dependencies
                if not self.generation_manager._refresh_generate_tab_reference():
                    # Revert to dictionary mode if generation still not available
                    self.mode_manager.switch_mode(SequenceCardMode.DICTIONARY)
                    self.header.description_label.setText(
                        "Generation mode unavailable - Could not initialize required dependencies."
                    )
                    return

            # Hide dictionary-specific controls
            if self.nav_sidebar.scroll_area:
                self.nav_sidebar.scroll_area.setVisible(False)
            if self.nav_sidebar.level_filter:
                self.nav_sidebar.level_filter.setVisible(False)

            # Show generation controls
            self._ensure_generation_controls()
            if self.generation_controls:
                self.generation_controls.setVisible(True)

            # Update header
            self.header.description_label.setText("Generate new sequences on-demand")

            # Clear current display and show generated sequences
            self.content_area.clear_layout()
            self._display_generated_sequences()

        # Update mode toggle availability
        self._update_mode_toggle_availability()

    def _ensure_generation_controls(self):
        """Ensure generation controls are created and added to the sidebar."""
        if self.generation_controls is None:
            self.generation_controls = GenerationControlsPanel()
            self.generation_controls.generate_requested.connect(
                self._on_generate_requested
            )
            self.generation_controls.clear_requested.connect(
                self._on_clear_generated_requested
            )

            # Add to sidebar layout
            sidebar_layout = self.nav_sidebar.layout()
            if sidebar_layout:
                # Insert before the column selector (last item)
                sidebar_layout.insertWidget(
                    sidebar_layout.count() - 1, self.generation_controls
                )

    def _on_generate_requested(self, params, batch_size: int):
        """Handle generation requests from the controls panel."""
        # Prevent generation during initialization
        if self.is_initializing:
            logging.info("Ignoring generation request during initialization")
            return

        # Use sidebar parameters instead of generation controls parameters
        sidebar_params = self._get_sidebar_parameters()

        if batch_size == 1:
            self.generation_manager.generate_single_sequence(sidebar_params)
        else:
            # For batch generation, collect all sequences before showing approval dialog
            self._pending_batch_sequences = []
            self._expected_batch_size = batch_size
            self.generation_manager.generate_batch(sidebar_params, batch_size)

    def _get_sidebar_parameters(self):
        """Get generation parameters from sidebar controls instead of generation controls."""
        from .generation.generation_manager import GenerationParams

        # Get parameters from sidebar with better fallback logic
        selected_length = self.nav_sidebar.selected_length

        import logging

        # Enhanced debugging for length parameter
        logging.info(f"DEBUG: nav_sidebar.selected_length = {selected_length}")
        logging.info(
            f"DEBUG: currently_displayed_length = {self.currently_displayed_length}"
        )

        # Try multiple sources for the length
        if not selected_length or selected_length == 0:
            # Try currently displayed length first
            if (
                hasattr(self, "currently_displayed_length")
                and self.currently_displayed_length > 0
            ):
                selected_length = self.currently_displayed_length
                logging.info(
                    f"DEBUG: Using currently_displayed_length: {selected_length}"
                )
            else:
                # If no length is selected, try to get from settings or use default
                try:
                    selected_length = int(
                        self.settings_manager.get_setting(
                            "sequence_card_tab", "last_length", 16
                        )
                    )
                    logging.info(f"DEBUG: Using settings length: {selected_length}")
                except:
                    selected_length = 16
                    logging.info(f"DEBUG: Using default length: {selected_length}")

        selected_levels = getattr(self.nav_sidebar.level_filter, "selected_levels", [1])
        selected_level = selected_levels[0] if selected_levels else 1

        logging.info(
            f"FINAL Sidebar parameters: length={selected_length}, level={selected_level}"
        )

        # Use default values for other parameters that should vary in batch generation
        return GenerationParams(
            length=selected_length,
            level=selected_level,
            turn_intensity=1,  # Will be varied in batch generation
            prop_continuity="continuous",  # Will be varied in batch generation
            generation_mode="freeform",  # Will be varied in batch generation
            rotation_type="halved",
            CAP_type="strict_rotated",
        )

    def _on_sequence_generated(self, sequence_data):
        """Handle newly generated sequences."""
        if hasattr(self, "_pending_batch_sequences"):
            # Batch generation mode - collect sequences
            self._pending_batch_sequences.append(sequence_data)

            # Check if batch is complete
            if len(self._pending_batch_sequences) >= self._expected_batch_size:
                # Show single approval dialog for all sequences
                dialog = SequenceApprovalDialog(self._pending_batch_sequences, self)
                dialog.sequences_approved.connect(self._on_sequences_approved)
                dialog.sequences_rejected.connect(self._on_sequences_rejected)
                dialog.show()

                # Clean up batch tracking
                delattr(self, "_pending_batch_sequences")
                delattr(self, "_expected_batch_size")
        else:
            # Single sequence generation - show approval dialog immediately
            dialog = SequenceApprovalDialog([sequence_data], self)
            dialog.sequences_approved.connect(self._on_sequences_approved)
            dialog.sequences_rejected.connect(self._on_sequences_rejected)
            dialog.show()

    def _on_sequences_approved(self, approved_sequences):
        """Handle batch sequence approval."""
        for sequence_data in approved_sequences:
            self.generated_sequence_store.add_approved_sequence(sequence_data)
        # Display only generated sequences - no dictionary integration
        self._display_generated_sequences()

    def _on_sequences_rejected(self, rejected_sequences):
        """Handle batch sequence rejection."""
        # Just ignore rejected sequences
        pass

    def _on_generation_failed(self, error_message: str):
        """Handle generation failures."""
        self.header.description_label.setText(f"Generation failed: {error_message}")

    def _on_generation_progress(self, current: int, total: int):
        """Handle generation progress updates."""
        if self.generation_controls:
            self.generation_controls.show_progress(current, total)

    def _on_clear_generated_requested(self):
        """Handle requests to clear generated sequences."""
        self.generated_sequence_store.clear_all_sequences()
        self._display_generated_sequences()

    def _display_generated_sequences(self):
        """Display the currently generated sequences."""
        count = self.generated_sequence_store.get_sequence_count()
        if count == 0:
            self.header.description_label.setText(
                "No generated sequences. Use the controls to generate some!"
            )
            self.content_area.clear_layout()
        else:
            self.header.description_label.setText(
                f"Showing {count} generated sequences"
            )

            # Display the actual sequence images
            self._render_generated_sequence_cards()

    def _render_generated_sequence_cards(self):
        """Render visual cards for generated sequences."""
        try:
            # Clear existing content
            self.content_area.clear_layout()

            # Get all generated sequences
            sequences = self.generated_sequence_store.get_all_sequences()
            if not sequences:
                return

            # Create a grid layout for the sequence cards
            from PyQt6.QtWidgets import QGridLayout, QWidget, QLabel, QVBoxLayout
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QPixmap

            # Create container widget and layout
            container_widget = QWidget()
            grid_layout = QGridLayout(container_widget)
            grid_layout.setSpacing(20)
            grid_layout.setContentsMargins(20, 20, 20, 20)

            # Calculate grid dimensions (3 columns max)
            columns = min(3, len(sequences))
            rows = (len(sequences) + columns - 1) // columns

            # Create cards for each sequence
            for i, sequence_data in enumerate(sequences):
                row = i // columns
                col = i % columns

                # Create sequence card
                card = self._create_sequence_card(sequence_data)
                grid_layout.addWidget(card, row, col)

            # Add the container to the content area
            self.content_area.scroll_layout.addWidget(container_widget)

        except Exception as e:
            print(f"Error rendering generated sequence cards: {e}")
            self.header.description_label.setText(
                f"Error displaying sequences: {str(e)}"
            )

    def _create_sequence_card(self, sequence_data):
        """Create a visual card for a generated sequence."""
        try:
            from PyQt6.QtWidgets import (
                QFrame,
                QVBoxLayout,
                QLabel,
                QPushButton,
                QHBoxLayout,
            )
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont, QPixmap

            # Create card frame
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

            # Create layout
            layout = QVBoxLayout(card)
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)

            # Generate and add sequence image
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

            # Generate the sequence image
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

            # Add sequence info
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

            # Add action buttons
            button_layout = QHBoxLayout()

            # Export button
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

            # Remove button
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
            print(f"Error creating sequence card: {e}")
            # Return a simple error card
            from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

            error_card = QFrame()
            error_card.setFixedSize(280, 350)
            error_layout = QVBoxLayout(error_card)
            error_label = QLabel(f"Error creating card:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_layout.addWidget(error_label)
            return error_card

    def _generate_sequence_card_image(self, sequence_data):
        """Generate a QPixmap for the sequence card."""
        try:
            # Get the sequence workbench for image generation
            sequence_workbench = self.main_widget.widget_manager.get_widget(
                "sequence_workbench"
            )
            if not sequence_workbench:
                return None

            # Get the image export manager
            image_export_manager = sequence_workbench.beat_frame.image_export_manager
            if not image_export_manager:
                return None

            # Prepare export options for dictionary-style image
            options = {
                "add_beat_numbers": True,
                "add_reversal_symbols": True,
                "add_user_info": False,
                "add_word": False,
                "add_difficulty_level": False,
                "include_start_position": False,
                "combined_grids": False,
                "additional_height_top": 0,
                "additional_height_bottom": 0,
            }

            # Generate the image using the image creator
            qimage = image_export_manager.image_creator.create_sequence_image(
                sequence_data.sequence_data,
                options,
                dictionary=True,
                fullscreen_preview=False,
            )

            # Convert QImage to QPixmap
            from PyQt6.QtGui import QPixmap

            pixmap = QPixmap.fromImage(qimage)
            return pixmap

        except Exception as e:
            print(f"Error generating sequence card image: {e}")
            return None

    def _export_generated_sequence(self, sequence_data):
        """Export a generated sequence to file."""
        try:
            # Use the image export manager to export the sequence
            sequence_workbench = self.main_widget.widget_manager.get_widget(
                "sequence_workbench"
            )
            if sequence_workbench:
                image_export_manager = (
                    sequence_workbench.beat_frame.image_export_manager
                )
                if image_export_manager:
                    image_export_manager.export_image_directly(
                        sequence_data.sequence_data
                    )
        except Exception as e:
            print(f"Error exporting generated sequence: {e}")

    def _remove_generated_sequence(self, sequence_data):
        """Remove a generated sequence from the store."""
        try:
            self.generated_sequence_store.remove_sequence(sequence_data.id)
            self._display_generated_sequences()
        except Exception as e:
            print(f"Error removing generated sequence: {e}")

    def _update_mode_toggle_availability(self):
        """Update the availability of mode toggle options."""
        if self.nav_sidebar.mode_toggle:
            # Dictionary mode is always available
            self.nav_sidebar.mode_toggle.set_mode_enabled(
                SequenceCardMode.DICTIONARY, True
            )

            # Generation mode availability depends on generate tab
            generation_available = self.generation_manager.is_available()
            self.nav_sidebar.mode_toggle.set_mode_enabled(
                SequenceCardMode.GENERATION, generation_available
            )

    def showEvent(self, event):
        super().showEvent(event)
        if not self.initialized:
            self.initialized = True
            self.setCursor(Qt.CursorShape.WaitCursor)
            QTimer.singleShot(50, self.initializer.initialize_content)
            # Also try to ensure generate tab is available after initialization
            QTimer.singleShot(100, self._ensure_generate_tab_available)
        else:
            # Refresh mode availability when tab becomes visible
            self._update_mode_toggle_availability()
            # Also try to ensure generate tab is available
            self._ensure_generate_tab_available()

    def _ensure_generate_tab_available(self):
        """Ensure the generate tab is available for generation functionality."""
        try:
            if not self.generation_manager.is_available():
                # Try to refresh the generate tab reference
                self.generation_manager._refresh_generate_tab_reference()
                # Update mode toggle availability after attempting to create tab
                self._update_mode_toggle_availability()
        except Exception as e:
            print(f"Error ensuring generate tab availability: {e}")

    def load_sequences(self):
        selected_length = self.nav_sidebar.selected_length
        length_text = f"{selected_length}-step" if selected_length > 0 else "all"
        self.header.description_label.setText(f"Loading {length_text} sequences...")
        QApplication.processEvents()

        if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
            self.printable_displayer.display_sequences(selected_length)
            self._sync_pages_from_displayer()
        else:
            pass

    def regenerate_all_images(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        original_text = self.header.description_label.text()
        self.header.description_label.setText("Regenerating images... Please wait")
        QApplication.processEvents()

        try:
            if hasattr(self.image_exporter, "export_all_images"):
                self.image_exporter.export_all_images()

            selected_length = self.nav_sidebar.selected_length

            if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
                self.printable_displayer.display_sequences(selected_length)
                self._sync_pages_from_displayer()

            self.header.description_label.setText("Images regenerated successfully!")
            QTimer.singleShot(
                3000, lambda: self.header.description_label.setText(original_text)
            )

        except Exception as e:
            self.header.description_label.setText(f"Error regenerating: {str(e)}")
            QTimer.singleShot(
                5000, lambda: self.header.description_label.setText(original_text)
            )
        finally:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _sync_pages_from_displayer(self):
        if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
            if hasattr(self.printable_displayer, "pages"):
                self.pages = self.printable_displayer.pages
            elif hasattr(self.printable_displayer, "manager") and hasattr(
                self.printable_displayer.manager, "pages"
            ):
                self.pages = self.printable_displayer.manager.pages

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.initialized and hasattr(self.nav_sidebar, "selected_length"):
            QTimer.singleShot(300, self.load_sequences)

    def on_scroll_area_resize(self):
        if self.resource_manager.resize_timer.isActive():
            self.resource_manager.resize_timer.stop()
        self.resource_manager.resize_timer.start(250)

    def refresh_layout_after_resize(self):
        if not self.initialized or not hasattr(self.nav_sidebar, "selected_length"):
            return

        if USE_PRINTABLE_LAYOUT and hasattr(self, "printable_displayer"):
            logging.debug("Refreshing layout after resize")
            self.printable_displayer.refresh_layout()
            self._sync_pages_from_displayer()

    def cleanup(self):
        self.resource_manager.cleanup()

        # Cleanup generation components
        if hasattr(self, "generated_sequence_store"):
            self.generated_sequence_store.cleanup()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)
