"""
Navigation Sidebar Component - Clean Architecture Implementation.

Handles alphabet navigation with single responsibility for section-based navigation.
Provides Type 3 kinetic alphabet support, individual section buttons, and precise positioning.

Features:
- Fixed 200px width sidebar with proper visual hierarchy
- Individual section buttons (A, B, C not A-C ranges) based on actual sequence data
- Type 3 kinetic alphabet support (W-, X-, Y- dash suffixes)
- Sort-responsive navigation (alphabetical, difficulty, date, length)
- Pixel-accurate scroll positioning with <100ms response times
- Glassmorphism styling integration

Performance Targets:
- <16ms navigation response times
- <100ms section button creation
- Pixel-accurate positioning
- Smooth scroll animations
"""

import logging
from typing import List, Dict, Optional, Set
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, QTimer, QElapsedTimer
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from ..core.interfaces import SequenceModel, BrowseTabConfig

logger = logging.getLogger(__name__)


class NavigationSidebar(QWidget):
    """
    Navigation sidebar component for section-based navigation.

    Single Responsibility: Provide section-based navigation with Type 3 alphabet support

    Features:
    - Fixed 200px width with proper visual hierarchy
    - Individual section buttons (A, B, C) based on actual sequence data
    - Type 3 kinetic alphabet support (W-, X-, Y- dash suffixes)
    - Sort-responsive navigation (alphabetical, difficulty, date, length)
    - Pixel-accurate scroll positioning
    - Real-time active section highlighting
    """

    # Signals for component communication
    section_clicked = pyqtSignal(str)  # section_id
    active_section_changed = pyqtSignal(str)  # section_id

    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)

        self.config = config or BrowseTabConfig()

        # State management
        self._current_sequences: List[SequenceModel] = []
        self._current_sort_criteria = "alphabetical"
        self._sections: List[str] = []
        self._section_indices: Dict[str, int] = {}
        self._active_section: Optional[str] = None

        # Performance tracking
        self._performance_timer = QElapsedTimer()
        self._click_timers: Dict[str, Dict] = {}
        self._target_response_time = 16.0  # 16ms target for navigation response

        # UI components
        self.header_label = None
        self.sections_container = None
        self.section_buttons: Dict[str, QPushButton] = {}
        self.scroll_area = None

        self._setup_ui()
        self._setup_styling()

        # Set fixed width for proper layout
        self.setFixedWidth(200)

        logger.debug("NavigationSidebar component initialized")

    def _setup_ui(self):
        """Setup the navigation sidebar UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)

        # Header section
        self._create_header_section(layout)

        # Sections scroll area
        self._create_sections_area(layout)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def _create_header_section(self, layout):
        """Create header section with title."""
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        # Navigation title
        self.header_label = QLabel("Navigation")
        self.header_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.header_label.setStyleSheet("color: white;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.header_label)

        # Sort criteria label
        self.sort_label = QLabel("Alphabetical")
        self.sort_label.setFont(QFont("Segoe UI", 9))
        self.sort_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.sort_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.sort_label)

        layout.addWidget(header_container)

    def _create_sections_area(self, layout):
        """Create scrollable sections area."""
        # Create scroll area for sections
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Sections container
        self.sections_container = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_container)
        self.sections_layout.setContentsMargins(5, 5, 5, 5)
        self.sections_layout.setSpacing(5)

        # Add stretch to push buttons to top
        self.sections_layout.addStretch()

        # Set container to scroll area
        self.scroll_area.setWidget(self.sections_container)
        layout.addWidget(self.scroll_area, 1)

    def _setup_styling(self):
        """Apply glassmorphism styling to the navigation sidebar."""
        try:
            self.setStyleSheet(
                """
                NavigationSidebar {
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                QScrollArea {
                    background: transparent;
                    border: none;
                }
                QScrollBar:vertical {
                    background: rgba(255, 255, 255, 0.1);
                    width: 6px;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 3px;
                    min-height: 15px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(255, 255, 255, 0.5);
                }
            """
            )

            logger.debug("Navigation sidebar styling applied")

        except Exception as e:
            logger.warning(f"Failed to apply navigation sidebar styling: {e}")

    def _extract_sections_from_sequences(
        self, sequences: List[SequenceModel], sort_criteria: str
    ) -> List[str]:
        """Extract sections from sequences based on sort criteria."""
        sections = set()

        if sort_criteria == "alphabetical":
            # Extract individual letters including Type 3 letters with dash suffixes
            for sequence in sequences:
                if sequence.name:
                    first_letter = self._extract_first_letter(sequence.name)
                    if first_letter:
                        sections.add(first_letter)

        elif sort_criteria == "difficulty":
            # Extract difficulty levels
            for sequence in sequences:
                if hasattr(sequence, "difficulty") and sequence.difficulty:
                    sections.add(str(sequence.difficulty))

        elif sort_criteria == "length":
            # Extract length ranges
            for sequence in sequences:
                if hasattr(sequence, "length") and sequence.length:
                    length = int(sequence.length)
                    if length <= 5:
                        sections.add("1-5")
                    elif length <= 10:
                        sections.add("6-10")
                    elif length <= 15:
                        sections.add("11-15")
                    else:
                        sections.add("16+")

        elif sort_criteria == "date_added":
            # Extract date ranges (simplified)
            sections.update(["Recent", "This Week", "This Month", "Older"])

        elif sort_criteria == "author":
            # Extract authors
            for sequence in sequences:
                if hasattr(sequence, "author") and sequence.author:
                    sections.add(sequence.author)

        # Sort sections appropriately
        if sort_criteria == "alphabetical":
            return self._sort_alphabetical_sections(list(sections))
        else:
            return sorted(list(sections))

    def _extract_first_letter(self, sequence_name: str) -> Optional[str]:
        """Extract first letter or letter with dash suffix (Type 3 letters)."""
        if not sequence_name:
            return None

        first_char = sequence_name[0]

        # Handle Greek letters by transliterating to English
        greek_to_english = {
            "Α": "A",
            "Β": "B",
            "Γ": "G",
            "Δ": "D",
            "Ε": "E",
            "Ζ": "Z",
            "Η": "H",
            "Θ": "T",
            "Ι": "I",
            "Κ": "K",
            "Λ": "L",
            "Μ": "M",
            "Ν": "N",
            "Ξ": "X",
            "Ο": "O",
            "Π": "P",
            "Ρ": "R",
            "Σ": "S",
            "Τ": "T",
            "Υ": "Y",
            "Φ": "F",
            "Χ": "C",
            "Ψ": "P",
            "Ω": "W",
        }

        if first_char in greek_to_english:
            first_char = greek_to_english[first_char]

        # Handle Type 3 letters with dash suffixes (W-, X-, Y-)
        if len(sequence_name) >= 2 and sequence_name[1] == "-":
            return first_char + "-"  # Return "W-", "X-", "Y-" etc.
        else:
            return first_char.upper()  # Return first letter

    def _sort_alphabetical_sections(self, sections: List[str]) -> List[str]:
        """Sort alphabetical sections with proper Type 3 letter ordering."""
        try:
            # Try to use LetterType.sort_key if available
            from enums.letter.letter_type import LetterType

            # Filter out sections that can't be processed by LetterType
            valid_sections = []
            for section in sections:
                try:
                    # Test if this section can be processed by LetterType.sort_key
                    LetterType.sort_key(section)
                    valid_sections.append(section)
                except (ValueError, AttributeError) as e:
                    logger.warning(
                        f"Skipping unrecognized letter section: {section} ({e})"
                    )
                    continue

            return sorted(valid_sections, key=LetterType.sort_key)
        except ImportError:
            # Fallback to simple sorting
            # Put dash suffixes after their base letters
            regular_letters = [s for s in sections if len(s) == 1]
            dash_letters = [s for s in sections if len(s) == 2 and s[1] == "-"]

            # Sort each group
            regular_letters.sort()
            dash_letters.sort()

            # Interleave them properly
            result = []
            for letter in regular_letters:
                result.append(letter)
                # Add any dash variants
                for dash_letter in dash_letters:
                    if dash_letter[0] == letter:
                        result.append(dash_letter)

            # Add any remaining dash letters
            for dash_letter in dash_letters:
                if dash_letter not in result:
                    result.append(dash_letter)

            return result

    def _precompute_section_indices(self):
        """Pre-compute section indices for fast navigation."""
        self._section_indices.clear()

        for section in self._sections:
            # Find first sequence that matches this section
            for index, sequence in enumerate(self._current_sequences):
                if self._sequence_matches_section(sequence, section):
                    self._section_indices[section] = index
                    break

    def _sequence_matches_section(self, sequence: SequenceModel, section: str) -> bool:
        """Check if a sequence matches a section."""
        if self._current_sort_criteria == "alphabetical":
            if sequence.name:
                first_letter = self._extract_first_letter(sequence.name)
                return first_letter == section

        elif self._current_sort_criteria == "difficulty":
            if hasattr(sequence, "difficulty") and sequence.difficulty:
                return str(sequence.difficulty) == section

        elif self._current_sort_criteria == "length":
            if hasattr(sequence, "length") and sequence.length:
                length = int(sequence.length)
                if section == "1-5":
                    return length <= 5
                elif section == "6-10":
                    return 6 <= length <= 10
                elif section == "11-15":
                    return 11 <= length <= 15
                elif section == "16+":
                    return length >= 16

        elif self._current_sort_criteria == "author":
            if hasattr(sequence, "author") and sequence.author:
                return sequence.author == section

        return False

    def _create_section_buttons(self):
        """Create section buttons based on current sections."""
        self._performance_timer.start()

        # Clear existing buttons
        self._clear_section_buttons()

        # Create new buttons
        for section in self._sections:
            button = self._create_section_button(section)
            self.section_buttons[section] = button

            # Insert before stretch
            self.sections_layout.insertWidget(self.sections_layout.count() - 1, button)

        elapsed = self._performance_timer.elapsed()
        logger.debug(
            f"Section buttons created in {elapsed}ms for {len(self._sections)} sections"
        )

        # Performance target: <100ms section button creation
        if elapsed > 100:
            logger.warning(
                f"Section button creation exceeded 100ms target: {elapsed}ms"
            )

    def _create_section_button(self, section: str) -> QPushButton:
        """Create a single section button."""
        button = QPushButton(section)
        button.setMinimumHeight(35)
        button.setMaximumHeight(35)

        # Style the button
        button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(100, 150, 255, 0.3);
                border-color: rgba(100, 150, 255, 0.5);
            }
        """
        )

        # Connect click handler with performance tracking
        button.clicked.connect(lambda: self._on_section_clicked(section))

        return button

    def _clear_section_buttons(self):
        """Clear all existing section buttons."""
        for button in self.section_buttons.values():
            button.deleteLater()
        self.section_buttons.clear()

    def _on_section_clicked(self, section: str):
        """Handle section button clicks with performance tracking."""
        click_id = f"{section}_{self._performance_timer.elapsed()}"
        self._performance_timer.start()

        # Update active section
        self._set_active_section(section)

        # Emit signal for external handling
        self.section_clicked.emit(section)

        elapsed = self._performance_timer.elapsed()
        logger.debug(f"Section clicked in {elapsed}ms: {section}")

        # Performance target: <16ms navigation response
        if elapsed > self._target_response_time:
            logger.warning(
                f"Section click exceeded {self._target_response_time}ms target: {elapsed}ms"
            )

    def _set_active_section(self, section: str):
        """Set the active section and update button styling."""
        # Remove active styling from previous section
        if self._active_section and self._active_section in self.section_buttons:
            self._update_button_styling(self._active_section, False)

        # Set new active section
        self._active_section = section

        # Apply active styling to new section
        if section in self.section_buttons:
            self._update_button_styling(section, True)

        self.active_section_changed.emit(section)

    def _update_button_styling(self, section: str, is_active: bool):
        """Update button styling for active/inactive state."""
        if section not in self.section_buttons:
            return

        button = self.section_buttons[section]

        if is_active:
            button.setStyleSheet(
                button.styleSheet()
                + """
                QPushButton {
                    background: rgba(100, 150, 255, 0.4);
                    border-color: rgba(100, 150, 255, 0.6);
                }
            """
            )
        else:
            # Reset to default styling
            button.setStyleSheet(self._create_section_button(section).styleSheet())

    # Public interface methods
    def update_sections(self, sequences: List[SequenceModel], sort_criteria: str):
        """Update sections based on new sequences and sort criteria."""
        self._performance_timer.start()

        self._current_sequences = sequences
        self._current_sort_criteria = sort_criteria

        # Extract sections from sequences
        self._sections = self._extract_sections_from_sequences(sequences, sort_criteria)

        # Pre-compute section indices for fast navigation
        self._precompute_section_indices()

        # Update UI
        self._create_section_buttons()

        # Update sort label
        sort_display_names = {
            "alphabetical": "Alphabetical",
            "difficulty": "Difficulty",
            "length": "Length",
            "date_added": "Date Added",
            "author": "Author",
        }
        self.sort_label.setText(
            sort_display_names.get(sort_criteria, sort_criteria.title())
        )

        elapsed = self._performance_timer.elapsed()
        logger.debug(
            f"Navigation sections updated in {elapsed}ms: {len(self._sections)} sections"
        )

    def get_section_index(self, section: str) -> Optional[int]:
        """Get the starting index for a section."""
        return self._section_indices.get(section)

    def get_active_section(self) -> Optional[str]:
        """Get the currently active section."""
        return self._active_section

    def get_sections(self) -> List[str]:
        """Get all available sections."""
        return self._sections.copy()

    def set_active_section(self, section: str):
        """Set the active section by section name (public interface)."""
        if section in self._sections:
            self._set_active_section(section)
        else:
            logger.warning(
                f"Section '{section}' not found in available sections: {self._sections}"
            )

    def set_active_section_by_index(self, sequence_index: int):
        """Set active section based on sequence index."""
        # Find which section this index belongs to
        for section, start_index in self._section_indices.items():
            # Check if this index is in this section's range
            next_section_index = None
            section_list = list(self._section_indices.keys())
            if section in section_list:
                current_section_idx = section_list.index(section)
                if current_section_idx + 1 < len(section_list):
                    next_section = section_list[current_section_idx + 1]
                    next_section_index = self._section_indices[next_section]

            if sequence_index >= start_index and (
                next_section_index is None or sequence_index < next_section_index
            ):
                self._set_active_section(section)
                break

    def cleanup(self):
        """Cleanup resources."""
        try:
            self._clear_section_buttons()
            logger.debug("NavigationSidebar cleanup completed")
        except Exception as e:
            logger.error(f"NavigationSidebar cleanup failed: {e}")
