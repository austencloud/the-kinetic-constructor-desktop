"""
Dynamic Section Headers Component

Sticky headers within the thumbnail grid that update based on current filter criteria.
Supports alphabetical, date, length, and difficulty grouping with modern styling.

Features:
- Sticky headers within scroll area
- Auto-update based on FilterService criteria
- Modern glassmorphism styling
- Smooth fade-in animations
- Support for multiple grouping types
"""

import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from ..core.interfaces import BrowseTabConfig
from ..core.state import SequenceModel

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Types of section grouping."""
    ALPHABETICAL = "alphabetical"
    DATE_ADDED = "date_added"
    LENGTH = "length"
    DIFFICULTY = "difficulty"
    AUTHOR = "author"
    TAGS = "tags"


class ModernSectionHeader(QWidget):
    """Modern styled section header with glassmorphism effects."""
    
    def __init__(self, title: str, section_id: str, parent: QWidget = None):
        super().__init__(parent)
        
        self.title = title
        self.section_id = section_id
        self.is_sticky = False
        
        self._setup_ui()
        self._setup_styling()
    
    def _setup_ui(self):
        """Setup header UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(0)
        
        # Header frame
        self.header_frame = QFrame()
        self.header_frame.setObjectName("sectionHeaderFrame")
        frame_layout = QVBoxLayout(self.header_frame)
        frame_layout.setContentsMargins(20, 12, 20, 12)
        frame_layout.setSpacing(0)
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("sectionHeaderTitle")
        font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.title_label)
        
        layout.addWidget(self.header_frame)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(60)
    
    def _setup_styling(self):
        """Apply modern glassmorphic styling."""
        self.setStyleSheet("""
            QFrame#sectionHeaderFrame {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                margin: 5px 0px;
            }
            
            QLabel#sectionHeaderTitle {
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
                border: none;
                font-weight: bold;
            }
            
            ModernSectionHeader[sticky="true"] QFrame#sectionHeaderFrame {
                background: rgba(76, 175, 80, 0.15);
                border: 1px solid rgba(76, 175, 80, 0.3);
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
            }
        """)
    
    def set_sticky(self, sticky: bool):
        """Set sticky state for header."""
        self.is_sticky = sticky
        self.setProperty("sticky", sticky)
        self.style().polish(self)
    
    def update_title(self, new_title: str):
        """Update header title."""
        self.title = new_title
        self.title_label.setText(new_title)


class SectionHeaderManager:
    """Manages section header creation and grouping logic."""
    
    def __init__(self):
        self.current_section_type = SectionType.ALPHABETICAL
        self.grouping_functions = {
            SectionType.ALPHABETICAL: self._group_by_alphabetical,
            SectionType.DATE_ADDED: self._group_by_date,
            SectionType.LENGTH: self._group_by_length,
            SectionType.DIFFICULTY: self._group_by_difficulty,
            SectionType.AUTHOR: self._group_by_author,
            SectionType.TAGS: self._group_by_tags,
        }
    
    def group_sequences(self, sequences: List[SequenceModel], section_type: SectionType) -> Dict[str, List[SequenceModel]]:
        """Group sequences by the specified section type."""
        self.current_section_type = section_type
        
        if section_type in self.grouping_functions:
            return self.grouping_functions[section_type](sequences)
        else:
            # Default to alphabetical
            return self._group_by_alphabetical(sequences)
    
    def _group_by_alphabetical(self, sequences: List[SequenceModel]) -> Dict[str, List[SequenceModel]]:
        """Group sequences alphabetically."""
        groups = {}
        
        for sequence in sequences:
            first_letter = sequence.name[0].upper() if sequence.name else 'Z'
            
            # Create range groups (A-C, D-F, etc.)
            if first_letter <= 'C':
                group_key = "A-C"
            elif first_letter <= 'F':
                group_key = "D-F"
            elif first_letter <= 'I':
                group_key = "G-I"
            elif first_letter <= 'L':
                group_key = "J-L"
            elif first_letter <= 'O':
                group_key = "M-O"
            elif first_letter <= 'R':
                group_key = "P-R"
            elif first_letter <= 'U':
                group_key = "S-U"
            else:
                group_key = "V-Z"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(sequence)
        
        return groups
    
    def _group_by_date(self, sequences: List[SequenceModel]) -> Dict[str, List[SequenceModel]]:
        """Group sequences by date added."""
        groups = {
            "Recent (Last 7 days)": [],
            "This Month": [],
            "Last Month": [],
            "Older": []
        }
        
        # For now, just put all in "Recent" - would need actual date logic
        for sequence in sequences:
            groups["Recent (Last 7 days)"].append(sequence)
        
        return {k: v for k, v in groups.items() if v}  # Remove empty groups
    
    def _group_by_length(self, sequences: List[SequenceModel]) -> Dict[str, List[SequenceModel]]:
        """Group sequences by length."""
        groups = {
            "Short (1-4 beats)": [],
            "Medium (5-8 beats)": [],
            "Long (9+ beats)": []
        }
        
        for sequence in sequences:
            length = getattr(sequence, 'length', 0)
            if length <= 4:
                groups["Short (1-4 beats)"].append(sequence)
            elif length <= 8:
                groups["Medium (5-8 beats)"].append(sequence)
            else:
                groups["Long (9+ beats)"].append(sequence)
        
        return {k: v for k, v in groups.items() if v}  # Remove empty groups
    
    def _group_by_difficulty(self, sequences: List[SequenceModel]) -> Dict[str, List[SequenceModel]]:
        """Group sequences by difficulty."""
        groups = {
            "Beginner (1-2)": [],
            "Intermediate (3-4)": [],
            "Advanced (5+)": []
        }
        
        for sequence in sequences:
            difficulty = getattr(sequence, 'difficulty', 1)
            if difficulty <= 2:
                groups["Beginner (1-2)"].append(sequence)
            elif difficulty <= 4:
                groups["Intermediate (3-4)"].append(sequence)
            else:
                groups["Advanced (5+)"].append(sequence)
        
        return {k: v for k, v in groups.items() if v}  # Remove empty groups
    
    def _group_by_author(self, sequences: List[SequenceModel]) -> Dict[str, List[SequenceModel]]:
        """Group sequences by author."""
        groups = {}
        
        for sequence in sequences:
            author = getattr(sequence, 'author', 'Unknown')
            if author not in groups:
                groups[author] = []
            groups[author].append(sequence)
        
        return groups
    
    def _group_by_tags(self, sequences: List[SequenceModel]) -> Dict[str, List[SequenceModel]]:
        """Group sequences by primary tag."""
        groups = {}
        
        for sequence in sequences:
            tags = getattr(sequence, 'tags', [])
            primary_tag = tags[0] if tags else 'Untagged'
            
            if primary_tag not in groups:
                groups[primary_tag] = []
            groups[primary_tag].append(sequence)
        
        return groups


class DynamicSectionHeaders(QWidget):
    """
    Dynamic section headers that update based on filter criteria.
    
    Features:
    - Auto-grouping based on sort criteria
    - Sticky header behavior
    - Modern glassmorphism styling
    - Smooth animations
    """
    
    # Signals
    section_changed = pyqtSignal(str)  # section_id
    header_clicked = pyqtSignal(str)  # section_id
    
    def __init__(self, config: BrowseTabConfig = None, parent: QWidget = None):
        super().__init__(parent)
        
        self.config = config or BrowseTabConfig()
        
        # State
        self.current_sequences: List[SequenceModel] = []
        self.current_section_type = SectionType.ALPHABETICAL
        self.headers: Dict[str, ModernSectionHeader] = {}
        self.section_groups: Dict[str, List[SequenceModel]] = {}
        
        # Manager
        self.header_manager = SectionHeaderManager()
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        logger.debug("DynamicSectionHeaders initialized")
    
    def update_sequences(self, sequences: List[SequenceModel], section_type: SectionType = None):
        """Update sequences and rebuild headers."""
        self.current_sequences = sequences
        
        if section_type:
            self.current_section_type = section_type
        
        # Group sequences
        self.section_groups = self.header_manager.group_sequences(
            sequences, self.current_section_type
        )
        
        # Rebuild headers
        self._rebuild_headers()
        
        logger.debug(f"Updated headers for {len(sequences)} sequences with {len(self.section_groups)} sections")
    
    def _rebuild_headers(self):
        """Rebuild section headers."""
        # Clear existing headers
        for header in self.headers.values():
            header.deleteLater()
        self.headers.clear()
        
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create new headers
        for section_id, sequences in self.section_groups.items():
            header = ModernSectionHeader(
                f"{section_id} ({len(sequences)} sequences)",
                section_id,
                self
            )
            
            self.headers[section_id] = header
            self.layout.addWidget(header)
            
            # Add fade-in animation
            if self.config.enable_animations:
                self._animate_header_fade_in(header)
    
    def _animate_header_fade_in(self, header: ModernSectionHeader):
        """Animate header fade-in."""
        header.setWindowOpacity(0.0)
        
        fade_animation = QPropertyAnimation(header, b"windowOpacity")
        fade_animation.setDuration(300)
        fade_animation.setStartValue(0.0)
        fade_animation.setEndValue(1.0)
        fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_animation.start()
    
    def get_section_groups(self) -> Dict[str, List[SequenceModel]]:
        """Get current section groups."""
        return self.section_groups.copy()
    
    def get_section_names(self) -> List[str]:
        """Get list of section names."""
        return list(self.section_groups.keys())
    
    def set_section_type(self, section_type: SectionType):
        """Set section grouping type."""
        if section_type != self.current_section_type:
            self.current_section_type = section_type
            self.update_sequences(self.current_sequences, section_type)
