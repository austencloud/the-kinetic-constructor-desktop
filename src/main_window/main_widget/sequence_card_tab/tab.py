# src/main_window/main_widget/sequence_card_tab/tab.py
import logging
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from src.interfaces.settings_manager_interface import ISettingsManager
from src.interfaces.json_manager_interface import IJsonManager
from .content_area import SequenceCardContentArea
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
from .generation.generated_sequence_store import GeneratedSequenceStore

# New imports for refactored classes
from .ui_manager import SequenceCardUIManager
from .controllers.dictionary_mode_controller import SequenceCardDictionaryModeController
from .controllers.generation_mode_controller import SequenceCardGenerationModeController

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class SequenceCardTab(QWidget):
    # Expose USE_PRINTABLE_LAYOUT as a class attribute for controllers
    USE_PRINTABLE_LAYOUT = USE_PRINTABLE_LAYOUT

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

        self.pages: list = []  # Added type hint for pages
        self.initialized: bool = False
        self.currently_displayed_length: int = 16
        self.is_initializing: bool = True
        self.load_start_time: float = 0  # Assuming it's a timestamp

        self.settings_manager_obj = SequenceCardSettingsHandler(settings_manager)
        self.resource_manager = SequenceCardResourceManager(self)
        self.initializer = SequenceCardInitializer(self)

        # Instantiate managers required by controllers before controllers themselves
        self.generation_manager = GenerationManager(self)

        # Create basic components first so we have the image exporter
        self._create_basic_components()

        # Now create the store with the image exporter
        self.generated_sequence_store = GeneratedSequenceStore(
            self, self.image_exporter
        )

        self.ui_manager = SequenceCardUIManager(self)
        self.dictionary_mode_controller = SequenceCardDictionaryModeController(self)
        self.generation_mode_controller = SequenceCardGenerationModeController(self)
        self.ui_manager.init_ui()
        self._create_and_init_components()

    def _create_basic_components(self):
        """Create basic components needed by UI manager."""
        self.nav_sidebar = SequenceCardNavSidebar(self)
        self.content_area = SequenceCardContentArea(self)

        # Create exporters needed by header buttons
        self.image_exporter = SequenceCardImageExporter(self)
        self.page_exporter = SequenceCardPageExporter(self)

    def _create_and_init_components(self):
        # nav_sidebar is already created in _create_basic_components()

        saved_length = self.settings_manager_obj.saved_length
        self.nav_sidebar.selected_length = saved_length
        self.currently_displayed_length = saved_length
        if hasattr(self.nav_sidebar, "scroll_area") and hasattr(
            self.nav_sidebar.scroll_area, "update_selection"
        ):
            self.nav_sidebar.scroll_area.update_selection(saved_length)
        logging.info(f"INITIALIZATION: Set initial length to {saved_length}")

        if (
            hasattr(self.settings_manager_obj, "saved_levels")
            and self.nav_sidebar.level_filter
        ):
            self.nav_sidebar.level_filter.set_selected_levels(
                self.settings_manager_obj.saved_levels
            )
        self.nav_sidebar.level_filter_changed.connect(self._on_level_filter_changed)

        # Connect header mode toggle instead of sidebar
        self.header.mode_change_requested.connect(self._on_mode_change_requested)

        # Mode manager is initialized here as it might depend on sidebar or other UI elements
        self.mode_manager = SequenceCardModeManager(self)

        # GenerationManager and GeneratedSequenceStore are already created in __init__
        # Now, connect signals that require both generation_manager and generation_mode_controller
        self.generation_manager.sequence_generated.connect(
            self.generation_mode_controller.on_sequence_generated
        )
        self.generation_manager.generation_failed.connect(
            self.generation_mode_controller.on_generation_failed
        )
        self.generation_manager.batch_generation_progress.connect(
            self.generation_mode_controller.on_generation_progress
        )

        # Page factory and displayer (conditionally initialized)
        if USE_PRINTABLE_LAYOUT:
            self.page_factory = PrintablePageFactory(self)
            self.printable_displayer = PrintableDisplayer(self)
            self.printable_displayer.set_paper_size(
                PaperSize.A4
            )  # Default, can be configurable
            self.printable_displayer.set_orientation(
                PaperOrientation.PORTRAIT
            )  # Default
            if hasattr(self.settings_manager_obj, "saved_column_count"):
                self.printable_displayer.columns_per_row = (
                    self.settings_manager_obj.saved_column_count
                )
        else:
            self.page_factory = SequenceCardPageFactory(self)
            self.printable_displayer = None  # Ensure it's None if not used

        # Other utilities (image_exporter and page_exporter already created in _create_basic_components)
        self.refresher = SequenceCardRefresher(
            self
        )  # May need review if its responsibilities overlap

        # Connect length selection from sidebar
        if hasattr(self.nav_sidebar, "length_selected"):
            self.nav_sidebar.length_selected.connect(self._on_length_selected)

        # Finalize mode manager and set initial state
        self.mode_manager.complete_initialization()
        self.is_initializing = False
        # Set initial mode (e.g., Dictionary) after all components are ready
        # This will trigger the appropriate controller's activate method.
        QTimer.singleShot(
            0, lambda: self._on_mode_change_requested(self.mode_manager.current_mode)
        )

    # init_ui is now handled by UIManager

    def update_column_count(self, column_count: int):
        self.ui_manager.update_column_count(column_count)

    def _on_length_selected(self, length: int):
        # Delegate to the dictionary mode controller if it's the active mode
        if self.mode_manager.current_mode == SequenceCardMode.DICTIONARY:
            self.dictionary_mode_controller.on_length_selected(length)
        # If generation mode or other modes need to react, add logic here or in their controllers

    def _on_level_filter_changed(self, selected_levels: list):
        # Delegate to the dictionary mode controller
        if self.mode_manager.current_mode == SequenceCardMode.DICTIONARY:
            self.dictionary_mode_controller.on_level_filter_changed(selected_levels)

    def _on_mode_change_requested(self, mode: SequenceCardMode):
        if (
            self.mode_manager.current_mode == mode and not self.is_initializing
        ):  # Avoid redundant switches
            # If the mode is already active, perhaps just refresh its UI or state
            if mode == SequenceCardMode.DICTIONARY:
                self.dictionary_mode_controller.activate()  # Or a refresh method
            elif mode == SequenceCardMode.GENERATION:
                self.generation_mode_controller.activate()  # Or a refresh method
            self._update_mode_toggle_availability()  # Ensure toggle is correct
            return

        if self.mode_manager.switch_mode(mode):
            # Deactivate previous controller (optional, if controllers manage their state)
            # self.dictionary_mode_controller.deactivate()
            # self.generation_mode_controller.deactivate()

            # Activate new controller
            if mode == SequenceCardMode.DICTIONARY:
                if hasattr(self, "generation_mode_controller"):  # Ensure it exists
                    self.generation_mode_controller.deactivate()
                self.dictionary_mode_controller.activate()
            elif mode == SequenceCardMode.GENERATION:
                if hasattr(self, "dictionary_mode_controller"):  # Ensure it exists
                    self.dictionary_mode_controller.deactivate()
                self.generation_mode_controller.activate()

            self._update_ui_for_mode(mode)  # Keep this for now, or move to controllers

            if self.header.mode_toggle:
                self.header.mode_toggle.set_current_mode(mode)
        self._update_mode_toggle_availability()

    def _update_ui_for_mode(self, mode: SequenceCardMode):
        """Update UI elements based on the current mode.
        This method will now primarily delegate to the active mode's controller."""
        if mode == SequenceCardMode.DICTIONARY:
            # UI updates are handled by dictionary_mode_controller.activate()
            pass
        elif mode == SequenceCardMode.GENERATION:
            # UI updates are handled by generation_mode_controller.activate()
            pass
        # Common UI updates or sidebar visibility can remain here or move to UIManager
        self._update_mode_toggle_availability()

    def _update_mode_toggle_availability(self):
        if self.header.mode_toggle:
            self.header.mode_toggle.set_mode_enabled(SequenceCardMode.DICTIONARY, True)
            generation_available = self.generation_manager.is_available()
            self.header.mode_toggle.set_mode_enabled(
                SequenceCardMode.GENERATION, generation_available
            )
            # Ensure the toggle reflects the actual current mode
            self.header.mode_toggle.set_current_mode(self.mode_manager.current_mode)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.initialized:
            self.initialized = True
            self.ui_manager.show_loading_indicator("Initializing tab...")
            # Initializer logic might need adjustment based on new structure
            QTimer.singleShot(50, self.initializer.initialize_content)
            QTimer.singleShot(
                100, self._ensure_generate_tab_available_and_update_toggle
            )
            QTimer.singleShot(
                150, lambda: self.ui_manager.hide_loading_indicator()
            )  # Hide after init
        else:
            self._ensure_generate_tab_available_and_update_toggle()
            # Refresh current mode's view if necessary
            current_mode = self.mode_manager.current_mode
            if current_mode == SequenceCardMode.DICTIONARY:
                self.dictionary_mode_controller.activate()  # Or a lighter refresh method
            elif current_mode == SequenceCardMode.GENERATION:
                self.generation_mode_controller.activate()  # Or a lighter refresh method

    def _ensure_generate_tab_available_and_update_toggle(self):
        """Ensures generate tab is available and updates mode toggle."""
        self._ensure_generate_tab_available()
        self._update_mode_toggle_availability()

    def _ensure_generate_tab_available(self):
        try:
            if not self.generation_manager.is_available():
                self.generation_manager._refresh_generate_tab_reference()
                # No direct UI update here, _update_mode_toggle_availability will handle it
        except Exception as e:
            logging.error(f"Error ensuring generate tab availability: {e}")

    def load_sequences(self):  # This is dictionary specific
        if self.mode_manager.current_mode == SequenceCardMode.DICTIONARY:
            self.dictionary_mode_controller.load_sequences()
        # If called from elsewhere, ensure it's appropriate or delegate.

    def regenerate_all_images(self):
        self.ui_manager.show_loading_indicator("Regenerating images... Please wait")
        QApplication.processEvents()
        original_text = ""  # Store original text if needed, or let UIManager handle it.
        # Consider if header text should be managed by UIManager or controllers.

        try:
            if hasattr(self.image_exporter, "export_all_images"):
                self.image_exporter.export_all_images()

            # Refresh based on current mode
            if self.mode_manager.current_mode == SequenceCardMode.DICTIONARY:
                selected_length = (
                    self.nav_sidebar.selected_length
                )  # Or get from controller
                if USE_PRINTABLE_LAYOUT and self.printable_displayer:
                    self.printable_displayer.display_sequences(selected_length)
                    self._sync_pages_from_displayer()
            elif self.mode_manager.current_mode == SequenceCardMode.GENERATION:
                self.generation_mode_controller._display_generated_sequences()

            self.ui_manager.set_header_description("Images regenerated successfully!")
            QTimer.singleShot(
                3000,
                lambda: self.ui_manager.set_header_description(
                    original_text
                    if original_text
                    else self.mode_manager.current_mode.name.title()
                ),
            )

        except Exception as e:
            logging.error(f"Error regenerating images: {e}")
            self.ui_manager.set_header_description(f"Error regenerating: {str(e)}")
            QTimer.singleShot(
                5000,
                lambda: self.ui_manager.set_header_description(
                    original_text
                    if original_text
                    else self.mode_manager.current_mode.name.title()
                ),
            )
        finally:
            self.ui_manager.hide_loading_indicator()

    def _sync_pages_from_displayer(self):
        if USE_PRINTABLE_LAYOUT and self.printable_displayer:
            if hasattr(self.printable_displayer, "pages"):
                self.pages = self.printable_displayer.pages
            elif hasattr(self.printable_displayer, "manager") and hasattr(
                self.printable_displayer.manager, "pages"
            ):
                self.pages = self.printable_displayer.manager.pages

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Handle responsive sidebar sizing
        if hasattr(self, "ui_manager"):
            self.ui_manager.handle_resize_event()

        # Debounce or delay the sequence loading on resize
        if self.initialized and hasattr(self.nav_sidebar, "selected_length"):
            # Only reload if in dictionary mode and printable layout is active
            if (
                self.mode_manager.current_mode == SequenceCardMode.DICTIONARY
                and USE_PRINTABLE_LAYOUT
            ):
                # Could use a QTimer to delay this call to avoid rapid reloads
                if hasattr(self, "_resize_load_timer"):
                    self._resize_load_timer.stop()
                else:
                    self._resize_load_timer = QTimer(self)
                    self._resize_load_timer.setSingleShot(True)
                    self._resize_load_timer.timeout.connect(
                        self.dictionary_mode_controller.load_sequences
                    )  # Delegate
                self._resize_load_timer.start(300)

    def on_scroll_area_resize(self):  # This seems tied to resource_manager
        if self.resource_manager.resize_timer.isActive():
            self.resource_manager.resize_timer.stop()
        self.resource_manager.resize_timer.start(
            250
        )  # Triggers refresh_layout_after_resize

    def refresh_layout_after_resize(self):  # This is dictionary/printable specific
        if not self.initialized or not hasattr(self.nav_sidebar, "selected_length"):
            return

        if (
            self.mode_manager.current_mode == SequenceCardMode.DICTIONARY
            and USE_PRINTABLE_LAYOUT
            and self.printable_displayer
        ):
            logging.debug("Refreshing layout after resize (delegated)")
            self.printable_displayer.refresh_layout()  # This might be called by dictionary controller too
            self._sync_pages_from_displayer()

    def cleanup(self):
        self.resource_manager.cleanup()
        if hasattr(self, "generated_sequence_store"):  # Check existence before cleanup
            self.generated_sequence_store.cleanup()
        # Add cleanup for controllers if they have resources to release
        # if hasattr(self, 'dictionary_mode_controller') and hasattr(self.dictionary_mode_controller, 'cleanup'):
        # self.dictionary_mode_controller.cleanup()
        # if hasattr(self, 'generation_mode_controller') and hasattr(self.generation_mode_controller, 'cleanup'):
        # self.generation_mode_controller.cleanup()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)
