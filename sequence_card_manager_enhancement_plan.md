# Enhanced Sequence Card Manager Implementation Plan

## Executive Summary

This document outlines the comprehensive implementation plan for enhancing the sequence card manager system with two distinct modes: **Dictionary Mode** (existing sequences) and **Generation Mode** (on-demand sequence creation). The enhancement includes level-based sorting, filtering capabilities, and a clear separation between dictionary-stored and generated sequences.

## Current State Analysis

### Existing Architecture

- **Main Component**: `SequenceCardTab` in `src/main_window/main_widget/sequence_card_tab/`
- **Navigation**: `SequenceCardNavSidebar` with length-based filtering (2, 3, 4, 5, 6, 8, 10, 12, 16 steps)
- **Display**: `PrintableDisplayer` with page-based layout using `SequenceDisplayManager`
- **Data Source**: Dictionary-based sequences from `data/dictionary/` with metadata extraction
- **Image Pipeline**: `SequenceCardImageExporter` with batch processing and caching
- **Settings**: `SequenceCardTabSettings` with column count and length preferences

### Current Data Flow

1. **Sequence Loading**: `SequenceLoader.get_all_sequences()` scans dictionary images
2. **Metadata Extraction**: `MetaDataExtractor` retrieves sequence length and level data
3. **Filtering**: Length-based filtering via sidebar selection
4. **Display**: `SequenceDisplayManager` creates pages with image labels
5. **Caching**: LRU cache for image data and page-level composite caching

### Existing Level Support

- **Level Evaluation**: `SequenceLevelEvaluator` calculates difficulty (1-3)
  - Level 1: No turns, radial orientations only
  - Level 2: Contains turns
  - Level 3: Contains non-radial orientations
- **Metadata Storage**: Level stored in sequence metadata and image PNG metadata
- **Dictionary Integration**: `DictionaryDataManager.get_records_by_level()` available

## Phase 1: Enhanced Dictionary Mode with Level-Based Sorting

### 1.1 Level Filter Component

**Location**: `src/main_window/main_widget/sequence_card_tab/components/navigation/level_filter.py`

```python
class LevelFilterWidget(QWidget):
    level_filter_changed = pyqtSignal(list)  # List of selected levels

    def __init__(self):
        # Multi-select level filter (All, Level 1, Level 2, Level 3)
        # Checkbox-based interface for intuitive selection
        # Compact design to fit in sidebar
```

### 1.2 Enhanced Sidebar Integration

**Modification**: `src/main_window/main_widget/sequence_card_tab/components/navigation/sidebar.py`

- Add level filter widget below length selection
- Maintain existing length filtering functionality
- Combine length + level filters for precise sequence selection
- Update UI layout to accommodate new filter without crowding

### 1.3 Enhanced Sequence Loader

**Modification**: `src/main_window/main_widget/sequence_card_tab/components/display/sequence_loader.py`

```python
def get_filtered_sequences(self, images_path: str, length_filter: int = None,
                          level_filters: list = None) -> List[Dict[str, Any]]:
    # Enhanced filtering logic combining length and level criteria
    # Efficient metadata extraction and caching
    # Maintain backward compatibility with existing length-only filtering
```

### 1.4 Settings Enhancement

**Modification**: `src/settings_manager/sequence_card_tab_settings.py`

```python
# Add level filter persistence
"selected_levels": [1, 2, 3],  # Default: all levels
"filter_mode": "dictionary",   # Track current mode
```

## Phase 2: Generation Mode Implementation

### 2.1 Mode Management System

**Location**: `src/main_window/main_widget/sequence_card_tab/core/mode_manager.py`

```python
class SequenceCardMode(Enum):
    DICTIONARY = "dictionary"
    GENERATION = "generation"

class SequenceCardModeManager:
    mode_changed = pyqtSignal(SequenceCardMode)

    def __init__(self, sequence_card_tab):
        self.current_mode = SequenceCardMode.DICTIONARY
        self.sequence_card_tab = sequence_card_tab

    def switch_mode(self, new_mode: SequenceCardMode):
        # Clear current display
        # Update UI elements
        # Emit mode change signal
        # Persist mode preference
```

### 2.2 Generation Integration Component

**Location**: `src/main_window/main_widget/sequence_card_tab/generation/generation_manager.py`

```python
class GenerationManager:
    def __init__(self, sequence_card_tab):
        self.generate_tab = sequence_card_tab.main_widget.generate_tab
        self.approval_queue = []
        self.generated_sequences = []

    def generate_sequence_batch(self, count: int, length: int, level: int):
        # Interface with generate tab's sequence builders
        # Create batch of sequences using existing generation logic
        # Return list of generated sequence data

    def create_approval_workflow(self, sequence_data):
        # Generate image representation
        # Display for user approval
        # Handle approve/reject decisions
```

### 2.3 Approval Workflow UI

**Location**: `src/main_window/main_widget/sequence_card_tab/generation/approval_dialog.py`

```python
class SequenceApprovalDialog(QDialog):
    sequence_approved = pyqtSignal(dict)
    sequence_rejected = pyqtSignal(dict)

    def __init__(self, sequence_data, sequence_image):
        # Display sequence image prominently
        # Show sequence metadata (length, level, properties)
        # Approve/Reject buttons
        # Option to generate another sequence
        # Batch approval for multiple sequences
```

### 2.4 Generated Sequence Storage

**Location**: `src/main_window/main_widget/sequence_card_tab/generation/generated_sequence_store.py`

```python
class GeneratedSequenceStore:
    def __init__(self):
        self.sequences = []  # In-memory storage
        self.temp_images = {}  # Temporary image cache

    def add_approved_sequence(self, sequence_data, image_data):
        # Store without polluting main dictionary
        # Assign temporary IDs
        # Create temporary image files if needed

    def clear_generated_sequences(self):
        # Clean up temporary data
        # Clear memory and temp files
```

## Phase 3: UI/UX Integration

### 3.1 Mode Toggle Component

**Location**: `src/main_window/main_widget/sequence_card_tab/components/navigation/mode_toggle.py`

```python
class ModeToggleWidget(QWidget):
    mode_changed = pyqtSignal(str)

    def __init__(self):
        # Clean toggle switch design
        # Clear visual indication of current mode
        # Dictionary Mode | Generation Mode
        # Prominent but not overwhelming
```

### 3.2 Header Enhancement

**Modification**: `src/main_window/main_widget/sequence_card_tab/header.py`

- Add mode indicator in header
- Update description text based on current mode
- Add generation-specific controls when in Generation Mode
- Maintain existing export/refresh functionality

### 3.3 Generation Controls Panel

**Location**: `src/main_window/main_widget/sequence_card_tab/generation/generation_controls.py`

```python
class GenerationControlsPanel(QWidget):
    def __init__(self):
        # Sequence length selector (reuse existing logic)
        # Level selector (1, 2, 3)
        # Batch size selector (1, 5, 10, 20)
        # Generate button
        # Clear generated sequences button
```

## Technical Architecture

### 3.4 Data Flow - Dictionary Mode

```
User Selection (Length + Level) → SequenceLoader.get_filtered_sequences() →
SequenceDisplayManager → Page Creation → Image Display
```

### 3.5 Data Flow - Generation Mode

```
User Parameters → GenerationManager.generate_sequence_batch() →
Generate Tab Integration → SequenceApprovalDialog →
GeneratedSequenceStore → SequenceDisplayManager → Page Creation
```

### 3.6 Integration Points

- **Generate Tab**: Reuse existing `FreeFormSequenceBuilder` and `CircularSequenceBuilder`
- **Image Creation**: Leverage `ImageCreator.create_sequence_image()`
- **Settings**: Extend existing settings system for mode persistence
- **Caching**: Separate cache namespaces for dictionary vs generated sequences

## Implementation Phases

### Phase 1: Dictionary Mode Enhancement (Week 1-2)

1. Create level filter component
2. Enhance sequence loader with level filtering
3. Update sidebar layout and integration
4. Add settings persistence
5. Test level-based filtering functionality

### Phase 2: Generation Mode Foundation (Week 3-4)

1. Implement mode management system
2. Create generation manager and integration
3. Build approval workflow UI
4. Implement generated sequence storage
5. Test basic generation workflow

### Phase 3: UI/UX Polish (Week 5)

1. Create mode toggle component
2. Enhance header with mode indicators
3. Build generation controls panel
4. Integrate all components
5. Comprehensive testing and refinement

## Risk Assessment & Mitigation

### High Risk

- **Generate Tab Integration**: Complex existing generation logic
  - _Mitigation_: Thorough analysis of existing builders, incremental integration
- **Memory Management**: Generated sequences could consume significant memory
  - _Mitigation_: Implement cleanup mechanisms, limit batch sizes

### Medium Risk

- **UI Complexity**: Adding features without cluttering interface
  - _Mitigation_: Progressive disclosure, user testing, clean design patterns
- **Settings Migration**: Existing user preferences
  - _Mitigation_: Backward compatibility, graceful defaults

### Low Risk

- **Performance**: Additional filtering operations
  - _Mitigation_: Efficient algorithms, caching strategies

## Success Criteria

1. **Functional**: Both modes work independently without interference
2. **Performance**: No degradation in existing dictionary mode performance
3. **Usability**: Intuitive mode switching and clear visual feedback
4. **Reliability**: Generated sequences don't pollute main dictionary
5. **Maintainability**: Clean separation of concerns, well-documented code

## Next Steps

1. **Approval**: Review and approve this implementation plan
2. **Environment Setup**: Ensure development environment is ready
3. **Phase 1 Implementation**: Begin with dictionary mode enhancements
4. **Iterative Development**: Regular testing and feedback cycles
5. **Documentation**: Maintain comprehensive documentation throughout

This plan provides a solid foundation for implementing the enhanced sequence card manager while maintaining the existing functionality and ensuring a smooth user experience.

## Detailed Technical Specifications

### Component Dependencies

```
SequenceCardTab
├── ModeManager (new)
├── SequenceCardNavSidebar (enhanced)
│   ├── LevelFilterWidget (new)
│   └── ModeToggleWidget (new)
├── GenerationManager (new)
│   ├── GenerationControlsPanel (new)
│   ├── SequenceApprovalDialog (new)
│   └── GeneratedSequenceStore (new)
└── SequenceDisplayManager (enhanced)
```

### Database Schema Changes

No database changes required - all data stored in:

- **Dictionary Mode**: Existing PNG metadata in `data/dictionary/`
- **Generation Mode**: In-memory storage with optional temp files
- **Settings**: QSettings INI format extensions

### API Interfaces

#### Mode Manager Interface

```python
class ISequenceCardModeManager(Protocol):
    def get_current_mode(self) -> SequenceCardMode
    def switch_mode(self, mode: SequenceCardMode) -> bool
    def is_mode_available(self, mode: SequenceCardMode) -> bool
```

#### Generation Manager Interface

```python
class IGenerationManager(Protocol):
    def generate_sequences(self, params: GenerationParams) -> List[SequenceData]
    def get_approval_queue(self) -> List[SequenceData]
    def approve_sequence(self, sequence_id: str) -> bool
    def reject_sequence(self, sequence_id: str) -> bool
```

### Performance Considerations

- **Level Filtering**: O(n) scan with metadata caching
- **Generation**: Async generation to prevent UI blocking
- **Memory Usage**: Limit generated sequences to 50 per session
- **Image Caching**: Separate LRU caches for each mode

### Error Handling Strategy

- **Generation Failures**: Graceful fallback, user notification
- **Mode Switch Failures**: Revert to previous mode, log error
- **Memory Exhaustion**: Auto-cleanup of oldest generated sequences
- **Settings Corruption**: Reset to defaults with user confirmation

### Testing Strategy

- **Unit Tests**: Each new component with mock dependencies
- **Integration Tests**: Mode switching, generation workflow
- **Performance Tests**: Large sequence sets, memory usage
- **User Acceptance Tests**: UI/UX validation with real users

### Backward Compatibility

- **Settings**: Graceful migration of existing preferences
- **API**: Existing sequence card functionality unchanged
- **Data**: No modification of existing dictionary structure
- **UI**: Existing workflows remain functional
