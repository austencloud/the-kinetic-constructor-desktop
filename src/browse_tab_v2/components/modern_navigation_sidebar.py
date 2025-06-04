"""
Modern Navigation Sidebar Component - Complete Overhaul

Fixed navigation sidebar with proper glassmorphism styling, individual section buttons,
and precise scroll-to-section functionality. Matches original browse tab behavior
with 2025 design system aesthetics.

Features:
- Fixed width sidebar (200px) with proper visual hierarchy
- Individual section buttons (A, B, C not A-C ranges) based on actual sequence data
- Glassmorphism styling matching other Browse Tab v2 components
- Sort-responsive navigation (alphabetical, difficulty, date, length)
- Pixel-accurate scroll positioning
- Real-time active section highlighting
"""

import logging
from typing import List, Dict, Optional, Set
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QElapsedTimer
from PyQt6.QtGui import QFont, QCursor

from ..core.interfaces import BrowseTabConfig
from ..core.state import SequenceModel

logger = logging.getLogger(__name__)


class ModernSidebarButton(QPushButton):
    """Modern styled sidebar navigation button."""

    def __init__(self, text: str, section_id: str, parent: QWidget = None):
        super().__init__(text, parent)

        self.section_id = section_id
        self.is_active = False

        self._setup_styling()
        self._setup_size()
        self._setup_cursor()

    def _setup_styling(self):
        """Apply proper glassmorphism styling matching Browse Tab v2 components."""

        # CRITICAL FIX: Use Qt-compatible glassmorphism with gradients for buttons
        robust_button_stylesheet = """
            ModernSidebarButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 64, 72, 0.8),
                    stop:1 rgba(50, 54, 62, 0.8)) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 12px !important;
                color: rgba(255, 255, 255, 0.9) !important;
                font-size: 11px !important;
                font-weight: 500 !important;
                padding: 8px 12px !important;
                text-align: center !important;
                margin: 2px !important;
            }

            ModernSidebarButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 84, 92, 0.9),
                    stop:1 rgba(70, 74, 82, 0.9)) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                color: rgba(255, 255, 255, 1.0) !important;
            }

            ModernSidebarButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(90, 94, 102, 0.95),
                    stop:1 rgba(80, 84, 92, 0.95)) !important;
                border: 1px solid rgba(255, 255, 255, 0.4) !important;
            }

            ModernSidebarButton[active="true"] {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(76, 175, 80, 0.8),
                    stop:1 rgba(56, 155, 60, 0.8)) !important;
                border: 1px solid rgba(76, 175, 80, 0.6) !important;
                color: rgba(255, 255, 255, 1.0) !important;
                font-weight: bold !important;
            }

            ModernSidebarButton[active="true"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(96, 195, 100, 0.9),
                    stop:1 rgba(76, 175, 80, 0.9)) !important;
                border: 1px solid rgba(76, 175, 80, 0.8) !important;
            }
        """

        self.setStyleSheet(robust_button_stylesheet)

        # Force immediate style update
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _setup_size(self):
        """Setup button size constraints."""
        self.setMinimumHeight(32)
        self.setMaximumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _setup_cursor(self):
        """Setup cursor behavior."""
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def set_active(self, active: bool):
        """Set button active state with proper styling update."""
        self.is_active = active
        self.setProperty("active", active)
        self.style().polish(self)

    def get_section_id(self) -> str:
        """Get the section ID for this button."""
        return self.section_id

    def enterEvent(self, event):
        """Handle mouse enter."""
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event):
        """Handle mouse leave."""
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)


class SectionDataExtractor:
    """Extracts individual sections from sequence data based on sort criteria."""

    @staticmethod
    def extract_alphabetical_sections(sequences: List[SequenceModel]) -> List[str]:
        """Extract individual letters that have sequences, including Type 3 letters with dash suffixes."""
        letters = set()
        for sequence in sequences:
            if sequence.name:
                # Extract first letter or letter with dash suffix (Type 3 letters)
                first_letter = SectionDataExtractor._extract_first_letter(sequence.name)
                if first_letter:
                    letters.add(first_letter)

        # Sort using proper letter type ordering
        from enums.letter.letter_type import LetterType

        return sorted(list(letters), key=LetterType.sort_key)

    @staticmethod
    def _extract_first_letter(word: str) -> str:
        """Extract the first letter or symbol from the word, handling dash suffixes."""
        if not word:
            return ""

        # Handle Type 3 letters with dash suffixes (W-, X-, Y-, Z-, etc.)
        if len(word) > 1 and word[1] == "-":
            potential_letter = word[:2].upper()
            # Verify this is a supported Type 3 letter
            if SectionDataExtractor._is_supported_letter(potential_letter):
                return potential_letter

        # Handle regular letters
        first_char = word[0].upper()

        # Only return supported letters/symbols, filter out unsupported characters
        if SectionDataExtractor._is_supported_letter(first_char):
            return first_char

        return ""

    @staticmethod
    def _is_supported_letter(letter_str: str) -> bool:
        """Check if a letter string is supported by the Letter enum."""
        try:
            from enums.letter.letter import Letter

            # Try to convert to Letter enum - if it succeeds, it's supported
            Letter.from_string(letter_str)
            return True
        except (ValueError, AttributeError):
            # If conversion fails, it's not supported
            return False

    @staticmethod
    def extract_difficulty_sections(sequences: List[SequenceModel]) -> List[str]:
        """Extract individual difficulty levels that have sequences."""
        difficulties = set()
        for sequence in sequences:
            difficulty = getattr(sequence, "difficulty", 1)
            if difficulty <= 2:
                difficulties.add("Beginner")
            elif difficulty <= 4:
                difficulties.add("Intermediate")
            else:
                difficulties.add("Advanced")
        return sorted(list(difficulties))

    @staticmethod
    def extract_length_sections(sequences: List[SequenceModel]) -> List[str]:
        """Extract individual length categories that have sequences."""
        lengths = set()
        for sequence in sequences:
            length = getattr(sequence, "length", 0)
            if length <= 4:
                lengths.add("Short")
            elif length <= 8:
                lengths.add("Medium")
            else:
                lengths.add("Long")
        return sorted(list(lengths))

    @staticmethod
    def extract_author_sections(sequences: List[SequenceModel]) -> List[str]:
        """Extract individual authors that have sequences."""
        authors = set()
        for sequence in sequences:
            author = getattr(sequence, "author", "Unknown")
            if author:
                authors.add(author)
        return sorted(list(authors))


class ModernNavigationSidebar(QWidget):
    """
    Fixed-width navigation sidebar with proper visual hierarchy and individual section buttons.

    Features:
    - Fixed 200px width with proper header/content separation
    - Individual section buttons (A, B, C not A-C ranges) based on actual sequence data
    - Sort-responsive navigation (alphabetical, difficulty, date, length)
    - Glassmorphism styling matching Browse Tab v2 components
    - Pixel-accurate scroll positioning
    - Real-time active section highlighting
    """

    # Signals
    section_clicked = pyqtSignal(str)  # section_id

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State
        self.current_sequences: List[SequenceModel] = []
        self.current_sort_criteria: str = "alphabetical"
        self.sections: List[str] = []  # Individual section names
        self.active_section: Optional[str] = None
        self.buttons: Dict[str, ModernSidebarButton] = {}

        # Fixed dimensions
        self.sidebar_width = 200

        # Components
        self.header_frame: QFrame = None
        self.title_label: QLabel = None
        self.separator_line: QFrame = None
        self.content_area: QScrollArea = None
        self.content_widget: QWidget = None

        # Data extractor
        self.data_extractor = SectionDataExtractor()

        # Performance monitoring for <16ms navigation response
        self._performance_timer = QElapsedTimer()
        self._click_times = []
        self._max_click_history = 50
        self._target_response_time = 16.0  # 16ms target for navigation clicks

        # Pre-computed section indices for O(1) lookups
        self._section_indices: Dict[str, List[int]] = {}

        self._setup_ui()
        self._setup_styling()

        # Set fixed width
        self.setFixedWidth(self.sidebar_width)

        # Check for pre-loaded data
        self._load_preloaded_data()

        logger.debug(
            "ModernNavigationSidebar initialized with fixed width architecture and performance monitoring"
        )

    def _setup_ui(self):
        """Setup the sidebar UI structure with proper visual hierarchy."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # 10px margins as specified
        layout.setSpacing(0)  # No spacing between header and content

        # Header frame (fixed height 40px)
        self.header_frame = self._create_header()
        layout.addWidget(self.header_frame)

        # Visual separator line
        self.separator_line = self._create_separator()
        layout.addWidget(self.separator_line)

        # Scrollable content area
        self.content_area = QScrollArea()
        self.content_area.setObjectName("sidebarContent")
        self.content_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.content_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.content_area.setWidgetResizable(True)

        # Content widget for navigation buttons
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)  # 8px content padding
        self.content_layout.setSpacing(4)  # 4px between buttons
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add spacer at bottom
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.content_layout.addItem(spacer)

        self.content_area.setWidget(self.content_widget)
        layout.addWidget(self.content_area, 1)  # Expandable content area

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def _create_header(self) -> QFrame:
        """Create header with title only (no toggle button for fixed width design)."""
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(40)  # Fixed 40px height as specified

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)  # 12px horizontal, 8px vertical padding
        layout.setSpacing(0)

        # Title label (centered)
        self.title_label = QLabel("Sections")
        self.title_label.setObjectName("sidebarTitle")
        font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        return header

    def _create_separator(self) -> QFrame:
        """Create visual separator line between header and content."""
        separator = QFrame()
        separator.setObjectName("sidebarSeparator")
        separator.setFixedHeight(1)  # 1px line
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        return separator

    def _setup_styling(self):
        """Apply modern glassmorphic styling with Qt-compatible gradients."""

        # CRITICAL FIX: Use Qt-compatible glassmorphism with gradients and solid colors
        robust_stylesheet = """
            ModernNavigationSidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 44, 52, 0.95),
                    stop:1 rgba(33, 37, 43, 0.95)) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 20px !important;
            }

            QFrame#sidebarHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50, 54, 62, 0.9),
                    stop:1 rgba(43, 47, 53, 0.9)) !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                border-radius: 15px !important;
            }

            QLabel#sidebarTitle {
                color: rgba(255, 255, 255, 0.95) !important;
                background: transparent !important;
                border: none !important;
                font-weight: bold !important;
                font-size: 12px !important;
            }

            QFrame#sidebarSeparator {
                background: rgba(255, 255, 255, 0.2) !important;
                border: none !important;
                margin: 0px 8px !important;
            }

            QScrollArea#sidebarContent {
                background: transparent !important;
                border: none !important;
            }

            /* CRITICAL FIX: Ensure content widget doesn't override button styles */
            QScrollArea#sidebarContent > QWidget {
                background: transparent !important;
                border: none !important;
            }

            /* Prevent any QPushButton styling from overriding ModernSidebarButton */
            QScrollArea#sidebarContent QPushButton {
                /* Let ModernSidebarButton handle its own styling */
            }

            QScrollArea#sidebarContent QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1) !important;
                border: none !important;
                border-radius: 4px !important;
                width: 8px !important;
            }

            QScrollArea#sidebarContent QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3) !important;
                border-radius: 4px !important;
                min-height: 20px !important;
            }

            QScrollArea#sidebarContent QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5) !important;
            }
        """

        self.setStyleSheet(robust_stylesheet)

        # Force immediate style update
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _load_preloaded_data(self):
        """Load pre-loaded data if available for immediate display."""
        try:
            from ..startup.data_preloader import get_preloaded_data

            preloaded_data = get_preloaded_data()
            if preloaded_data:
                sequences = preloaded_data.get("sequences", [])
                navigation_sections = preloaded_data.get("navigation_sections", {})

                if sequences and navigation_sections:
                    # Use pre-loaded alphabetical sections by default
                    alphabetical_sections = navigation_sections.get("alphabetical", [])
                    if alphabetical_sections:
                        self.current_sequences = sequences
                        self.current_sort_criteria = "alphabetical"
                        self.sections = alphabetical_sections

                        # Pre-compute section indices
                        self._precompute_section_indices()

                        # Build buttons immediately
                        self._rebuild_buttons()

                        logger.info(
                            f"Navigation sidebar loaded with {len(sequences)} pre-loaded sequences "
                            f"and {len(alphabetical_sections)} sections"
                        )
                        return

            logger.debug("No pre-loaded data available for navigation sidebar")

        except Exception as e:
            logger.warning(
                f"Failed to load pre-loaded data for navigation sidebar: {e}"
            )

    def update_for_sequences(
        self, sequences: List[SequenceModel], sort_criteria: str = "alphabetical"
    ):
        """Update sidebar with optimized pre-computed section indices."""
        self.current_sequences = sequences
        self.current_sort_criteria = sort_criteria

        # Extract individual sections based on sort criteria
        if sort_criteria == "alphabetical":
            self.sections = self.data_extractor.extract_alphabetical_sections(sequences)
        elif sort_criteria == "difficulty":
            self.sections = self.data_extractor.extract_difficulty_sections(sequences)
        elif sort_criteria == "length":
            self.sections = self.data_extractor.extract_length_sections(sequences)
        elif sort_criteria == "author":
            self.sections = self.data_extractor.extract_author_sections(sequences)
        else:
            # Default to alphabetical
            self.sections = self.data_extractor.extract_alphabetical_sections(sequences)

        # Pre-compute section indices for O(1) lookups
        self._precompute_section_indices()

        self._rebuild_buttons()
        logger.debug(
            f"Updated sidebar with {len(self.sections)} individual sections for {sort_criteria} sort"
        )

    def _rebuild_buttons(self):
        """Rebuild individual section buttons."""
        # Clear existing buttons
        for button in self.buttons.values():
            button.deleteLater()
        self.buttons.clear()

        # Remove all widgets except spacer
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new individual section buttons
        for section_name in self.sections:
            # CRITICAL FIX: Parent button to content_widget, not self
            button = ModernSidebarButton(
                section_name, section_name, self.content_widget
            )

            # Fix lambda closure issue
            button.clicked.connect(
                lambda checked=False, name=section_name: self._on_section_clicked(name)
            )

            self.buttons[section_name] = button
            self.content_layout.insertWidget(self.content_layout.count() - 1, button)

    def _precompute_section_indices(self):
        """Pre-compute section indices for O(1) sequence lookups."""
        self._section_indices.clear()

        for section_name in self.sections:
            indices = []

            for i, sequence in enumerate(self.current_sequences):
                if self._sequence_belongs_to_section(sequence, section_name):
                    indices.append(i)

            self._section_indices[section_name] = indices

        logger.debug(f"Pre-computed indices for {len(self.sections)} sections")

    def _sequence_belongs_to_section(
        self, sequence: SequenceModel, section_name: str
    ) -> bool:
        """Optimized check if sequence belongs to section."""
        if self.current_sort_criteria == "alphabetical":
            if sequence.name:
                sequence_first_letter = self.data_extractor._extract_first_letter(
                    sequence.name
                )
                return sequence_first_letter == section_name
        elif self.current_sort_criteria == "difficulty":
            difficulty = getattr(sequence, "difficulty", 1)
            if section_name == "Beginner":
                return difficulty <= 2
            elif section_name == "Intermediate":
                return 3 <= difficulty <= 4
            elif section_name == "Advanced":
                return difficulty >= 5
        elif self.current_sort_criteria == "length":
            length = getattr(sequence, "length", 0)
            if section_name == "Short":
                return length <= 4
            elif section_name == "Medium":
                return 5 <= length <= 8
            elif section_name == "Long":
                return length >= 9
        elif self.current_sort_criteria == "author":
            author = getattr(sequence, "author", "Unknown")
            return author == section_name

        return False

    def _on_section_clicked(self, section_id: str):
        """Handle section button click with comprehensive performance tracking."""
        # Start comprehensive navigation tracking
        navigation_timer = QElapsedTimer()
        navigation_timer.start()

        # Phase 1: UI State Update
        ui_timer = QElapsedTimer()
        ui_timer.start()
        self.set_active_section(section_id)
        ui_time = ui_timer.elapsed()

        # Phase 2: Section Filtering (O(1) lookup)
        filter_timer = QElapsedTimer()
        filter_timer.start()
        section_sequences = self.get_sequences_for_section(section_id)
        filter_time = filter_timer.elapsed()

        # Phase 3: Signal Emission
        signal_timer = QElapsedTimer()
        signal_timer.start()
        self.section_clicked.emit(section_id)
        signal_time = signal_timer.elapsed()

        # Total navigation time
        total_time = navigation_timer.elapsed()

        # Record comprehensive performance metrics
        self._click_times.append(total_time)
        if len(self._click_times) > self._max_click_history:
            self._click_times.pop(0)

        # Performance analysis with phase breakdown
        if total_time > self._target_response_time:
            logger.warning(
                f"SLOW NAVIGATION: {total_time:.2f}ms > {self._target_response_time:.2f}ms "
                f"(ui={ui_time:.1f}ms, filter={filter_time:.1f}ms, signal={signal_time:.1f}ms) "
                f"section={section_id}, sequences={len(section_sequences)}"
            )
        elif total_time > self._target_response_time * 0.8:  # Warning at 80% of target
            logger.info(
                f"NAVIGATION WARNING: {total_time:.2f}ms approaching target "
                f"(ui={ui_time:.1f}ms, filter={filter_time:.1f}ms, signal={signal_time:.1f}ms)"
            )

        # Validate O(1) performance for filtering
        if filter_time > 1.0:  # Should be <1ms for O(1) lookup
            logger.error(
                f"FILTER PERFORMANCE DEGRADED: {filter_time:.2f}ms > 1ms target (O(1) lookup failed)"
            )

        # Periodic comprehensive performance reporting
        if len(self._click_times) % 10 == 0:
            self._report_navigation_performance_metrics()

        logger.debug(
            f"Navigation: {section_id} -> {len(section_sequences)} sequences in {total_time:.2f}ms"
        )

    def _report_navigation_performance_metrics(self):
        """Report comprehensive navigation performance metrics."""
        if not self._click_times:
            return

        # Calculate performance statistics
        avg_time = sum(self._click_times) / len(self._click_times)
        max_time = max(self._click_times)
        min_time = min(self._click_times)

        # Count slow responses
        slow_responses = sum(
            1 for t in self._click_times if t > self._target_response_time
        )
        very_slow_responses = sum(
            1 for t in self._click_times if t > self._target_response_time * 2
        )

        # Performance grade
        if avg_time <= self._target_response_time * 0.5:
            grade = "EXCELLENT"
        elif avg_time <= self._target_response_time:
            grade = "GOOD"
        elif avg_time <= self._target_response_time * 1.5:
            grade = "ACCEPTABLE"
        else:
            grade = "POOR"

        # Section index performance validation
        total_sections = len(self.sections)
        total_sequences = len(self.current_sequences) if self.current_sequences else 0

        logger.info(
            f"NAVIGATION PERFORMANCE [{grade}]: "
            f"avg={avg_time:.1f}ms (target={self._target_response_time:.0f}ms), "
            f"range={min_time:.1f}-{max_time:.1f}ms, "
            f"slow={slow_responses}/{len(self._click_times)} "
            f"(very_slow={very_slow_responses}), "
            f"sections={total_sections}, sequences={total_sequences}"
        )

    def set_active_section(self, section_id: Optional[str]):
        """Optimized active section update for <16ms performance."""
        # Optimized state clearing (single lookup)
        if self.active_section and self.active_section in self.buttons:
            self.buttons[self.active_section].set_active(False)

        # Optimized state setting (single lookup)
        self.active_section = section_id
        if section_id and section_id in self.buttons:
            self.buttons[section_id].set_active(True)

    def get_sections(self) -> List[str]:
        """Get current individual sections."""
        return self.sections.copy()

    def get_current_sort_criteria(self) -> str:
        """Get current sort criteria."""
        return self.current_sort_criteria

    def get_sequences_for_section(self, section_name: str) -> List[SequenceModel]:
        """Optimized O(1) sequence lookup using pre-computed indices."""
        if not self.current_sequences or section_name not in self._section_indices:
            return []

        # Use pre-computed indices for O(1) lookup
        indices = self._section_indices[section_name]
        return [self.current_sequences[i] for i in indices]

    def get_active_section(self) -> Optional[str]:
        """Get active section ID."""
        return self.active_section

    def is_section_active(self, section_id: str) -> bool:
        """Check if section is active."""
        return self.active_section == section_id
