from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from .filter_stack.sequence_picker_filter_stack import SequencePickerFilterStack
from .section_manager import SequencePickerSectionManager
from .sorter import SequencePickerSorter
from .control_panel.sequence_picker_control_panel import SequencePickerControlPanel
from .progress_bar import SequencePickerProgressBar
from .nav_sidebar.sequence_picker_nav_sidebar import SequencePickerNavSidebar
from .scroll_widget import SequencePickerScrollWidget

if TYPE_CHECKING:
    from ..browse_tab import BrowseTab


class SequencePicker(QWidget):
    initialized = False

    def __init__(self, browse_tab: "BrowseTab"):
        super().__init__(browse_tab)
        self.browse_tab = browse_tab
        self.main_widget = browse_tab.main_widget
        self.sections: dict[str, list[tuple[str, list[str]]]] = {}
        self.currently_displayed_sequences = []
        self.selected_sequence_dict = None

        # Set size policy to respect the layout stretch ratios and prevent excessive expansion
        from PyQt6.QtWidgets import QSizePolicy

        size_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,  # Expanding allows growth but respects constraints
        )
        size_policy.setHorizontalStretch(
            2
        )  # This should match the stretch factor in TabManager (2 for left stack in browse tab)
        self.setSizePolicy(size_policy)

        self._setup_components()
        self._setup_layout()

    def _setup_components(self):
        import logging

        logger = logging.getLogger(__name__)
        logger.info("🔧 Setting up SequencePicker components")

        # Widgets
        logger.info("📚 Creating filter stack...")
        self.filter_stack = SequencePickerFilterStack(self)
        logger.info("🎛️ Creating control panel...")
        self.control_panel = SequencePickerControlPanel(self)
        logger.info("📊 Creating progress bar...")
        self.progress_bar = SequencePickerProgressBar(self)
        logger.info("📜 Creating scroll widget...")
        self.scroll_widget = SequencePickerScrollWidget(self)
        logger.info("🧭 Creating nav sidebar...")
        self.nav_sidebar = SequencePickerNavSidebar(self)

        # Managers
        logger.info("🔄 Creating sorter...")
        self.sorter = SequencePickerSorter(self)
        logger.info("📋 Creating section manager...")
        self.section_manager = SequencePickerSectionManager(self)

        logger.info("✅ All SequencePicker components created successfully")

    def _setup_layout(self):
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # RESPONSIVE LAYOUT FIX: Add proper stretch factors
        # Nav sidebar gets minimal space, scroll widget gets the rest
        content_layout.addWidget(self.nav_sidebar, 0)  # Fixed width, no stretch
        content_layout.addWidget(self.scroll_widget, 1)  # Takes remaining space

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addLayout(content_layout)

        self.setLayout(self.main_layout)

    # CRITICAL FIX: Lightweight filter update for non-blocking tab switching
    def update_filters_lightweight(self):
        """Update filters without heavy processing to prevent UI blocking."""
        from PyQt6.QtWidgets import QApplication

        try:
            # Just ensure the UI is responsive
            QApplication.processEvents()

            # Light filter state update without heavy processing
            if hasattr(self, "filter_stack"):
                # Just ensure filter stack is visible and responsive
                self.filter_stack.update()

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Error in lightweight filter update: {e}")
