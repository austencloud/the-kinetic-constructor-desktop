# Code Implementation Guide: Sequence Workbench & Beat Frame Architectural Redesign

**Date:** May 31, 2025  
**Prepared for:** User  
**Prepared by:** Gemini Large Language Model  
**Version:** 1.0  
**Based on:**

- Modern Architecture Design Document (ID: modern_architecture_design_v1)
- Implementation Roadmap (ID: implementation_roadmap_v1)

## 1. Introduction

This document provides practical code examples, best practices, and integration patterns for implementing the modern MVVM with Services architecture for the sequence_workbench and beat_frame components. It serves as a companion to the "Modern Architecture Design Document" and the "Implementation Roadmap."

The examples provided are illustrative and will need to be adapted and expanded based on the specific requirements and complexities of the application.

## 2. Project Structure

A recommended project structure to support the new architecture:

```
your_project_root/
├── main.py
├── app_context.py             # For service locator/DI container
├── core/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   ├── sequence_data_model.py
│   │   ├── beat_data_model.py
│   │   └── settings_model.py
│   └── services/
│       ├── __init__.py
│       ├── base_service.py
│       ├── service_locator.py
│       ├── sequence_management_service.py
│       ├── beat_operations_service.py
│       ├── settings_service.py
│       ├── image_export_service.py
│       ├── layout_calculation_service.py
│       └── undo_redo_service.py
├── modules/
│   └── sequence_workbench/
│       ├── __init__.py
│       ├── views/
│       │   ├── __init__.py
│       │   ├── sequence_beat_frame_view.py
│       │   ├── beat_view.py
│       │   ├── start_position_view.py
│       │   └── selection_overlay_view.py
│       ├── viewmodels/
│       │   ├── __init__.py
│       │   ├── base_viewmodel.py
│       │   ├── sequence_beat_frame_viewmodel.py
│       │   └── beat_viewmodel.py
│       └── components/ # Other related UI components like graph editor, info panel
│           ├── graph_editor_view.py
│           └── graph_editor_viewmodel.py
├── resources/
│   └── styles/
│       └── default_theme.qss
└── utils/
    └── ... # Utility functions
```

## 3. Core Architectural Components: Code Examples

### 3.1. Data Models (Example: BeatDataModel)

Plain Python objects, potentially using dataclasses for simplicity and type hinting.
Should be immutable or have controlled mutability.

```python
# core/models/beat_data_model.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(frozen=True) # Using frozen=True for immutability
class MotionAttributes:
    color: str
    turns: float

@dataclass(frozen=True)
class BeatDataModel:
    id: str # Unique identifier for the beat
    beat_number: int
    letter: Optional[str] = None
    duration: float = 1.0
    blue_motion: Optional[MotionAttributes] = None
    red_motion: Optional[MotionAttributes] = None
    blue_reversal: bool = False
    red_reversal: bool = False

    def update(self, **kwargs) -> 'BeatDataModel':
        """Returns a new instance with updated fields"""
        return dataclass.replace(self, **kwargs)
```

```python
# core/models/sequence_data_model.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .beat_data_model import BeatDataModel

@dataclass(frozen=True)
class SequenceDataModel:
    id: str # Unique sequence identifier
    word: str = ""
    level: int = 1
    beats: List[BeatDataModel] = field(default_factory=list)
    start_position: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs) -> 'SequenceDataModel':
        """Returns a new instance with updated fields"""
        return dataclass.replace(self, **kwargs)
```

### 3.2. Service Locator / Dependency Injection (Simple Example)

```python
# core/services/service_locator.py
class ServiceLocator:
    def __init__(self):
        self._services = {}

    def register_service(self, name: str, service_instance):
        self._services[name] = service_instance

    def get_service(self, name: str):
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
        return self._services[name]
```

```python
# app_context.py (or main application setup)
from core.services.service_locator import ServiceLocator
from core.services.sequence_management_service import SequenceManagementService
from core.services.beat_operations_service import BeatOperationsService
# ... import other services

service_locator = ServiceLocator()

def setup_services():
    sequence_management_service = SequenceManagementService()
    service_locator.register_service("sequence_management", sequence_management_service)

    beat_operations_service = BeatOperationsService(sequence_management_service) # Example of service dependency
    service_locator.register_service("beat_operations", beat_operations_service)
    # Register other services...

# Call setup_services() during application startup
```

### 3.3. Services (Example: BeatOperationsService)

```python
# core/services/beat_operations_service.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.sequence_data_model import SequenceDataModel
    from core.models.beat_data_model import BeatDataModel, MotionAttributes
    from .sequence_management_service import SequenceManagementService

class BeatOperationsService:
    def __init__(self, sequence_management_service: "SequenceManagementService"):
        self.sequence_management_service = sequence_management_service
        # Potentially other services like ReversalDetectionService

    def add_new_beat_to_sequence(self, sequence_model: "SequenceDataModel", new_beat_data: Dict) -> "SequenceDataModel":
        """
        Adds a new beat to the sequence and returns updated SequenceDataModel
        """
        from core.models.beat_data_model import BeatDataModel
        import uuid

        new_beat = BeatDataModel(
            id=str(uuid.uuid4()),
            beat_number=len(sequence_model.beats) + 1,
            letter=new_beat_data.get("letter", "N"),
            duration=new_beat_data.get("duration", 1.0)
        )

        updated_beats = list(sequence_model.beats) + [new_beat]
        # Apply reversal detection logic here
        updated_beats = self._recalculate_reversals(updated_beats)

        return sequence_model.update(beats=updated_beats)

    def remove_beat_from_sequence(self, sequence_model: "SequenceDataModel", beat_id_to_remove: str) -> "SequenceDataModel":
        updated_beats = [beat for beat in sequence_model.beats if beat.id != beat_id_to_remove]
        return sequence_model.update(beats=updated_beats)

    def update_beat_duration(self, sequence_model: "SequenceDataModel", beat_id: str, new_duration: float) -> "SequenceDataModel":
        updated_beats = []
        for beat in sequence_model.beats:
            if beat.id == beat_id:
                updated_beats.append(beat.update(duration=new_duration))
            else:
                updated_beats.append(beat)
        return sequence_model.update(beats=updated_beats)

    # Placeholder for more complex logic
    def _recalculate_reversals(self, beats: List["BeatDataModel"]) -> List["BeatDataModel"]:
        # Implement reversal detection logic here
        return beats
```

### 3.4. Base ViewModel (BaseViewModel)

```python
# modules/sequence_workbench/viewmodels/base_viewmodel.py
from PyQt6.QtCore import QObject, pyqtSignal

class BaseViewModel(QObject):
    # Generic signal that can be emitted when any property the View cares about changes
    # More specific signals per property are often better for granularity
    properties_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.some_service = service_locator.get_service("some_service")

    def _notify_properties_changed(self):
        self.properties_changed.emit()
```

### 3.5. Specific ViewModel (Example: BeatViewModel)

```python
# modules/sequence_workbench/viewmodels/beat_viewmodel.py
from PyQt6.QtCore import pyqtProperty, pyqtSignal, QObject
from typing import Optional, Dict, Any

from .base_viewmodel import BaseViewModel
from core.models.beat_data_model import BeatDataModel # Assuming BeatDataModel is defined

class BeatViewModel(BaseViewModel):
    beat_data_model_changed = pyqtSignal()
    selection_changed = pyqtSignal(bool)

    def __init__(self, beat_data_model: BeatDataModel, parent=None):
        super().__init__(parent)
        self._beat_data_model = beat_data_model
        self._is_selected = False
        # Potentially inject services if this VM needs them directly

    @pyqtProperty(QObject, notify=beat_data_model_changed)
    def model(self) -> BeatDataModel:
        return self._beat_data_model

    def set_model(self, beat_data_model: BeatDataModel):
        if self._beat_data_model != beat_data_model:
            self._beat_data_model = beat_data_model
            self.beat_data_model_changed.emit()
            self._notify_properties_changed()

    @pyqtProperty(str, notify=beat_data_model_changed)
    def beat_id(self) -> str:
        return self._beat_data_model.id

    @pyqtProperty(str, notify=beat_data_model_changed)
    def display_beat_number(self) -> str:
        # Logic to display beat number, possibly with duration
        return str(self._beat_data_model.beat_number)

    @pyqtProperty(str, notify=beat_data_model_changed)
    def letter(self) -> Optional[str]:
        return self._beat_data_model.letter

    @pyqtProperty(bool, notify=selection_changed)
    def is_selected(self) -> bool:
        return self._is_selected

    def set_selected(self, selected: bool):
        if self._is_selected != selected:
            self._is_selected = selected
            self.selection_changed.emit(selected)
            self._notify_properties_changed()

    # Expose other properties needed by the BeatView
    # (e.g., colors, orientations, turn numbers, reversal symbols)
    # These would be derived from self._beat_data_model

    @pyqtProperty(dict, notify=beat_data_model_changed)
    def visual_attributes(self) -> Dict[str, Any]:
        # This method would transform BeatDataModel into a dict suitable for rendering
        attrs = {}
        if self._beat_data_model.blue_motion:
            attrs["blue_prop_color"] = self._beat_data_model.blue_motion.color
        if self._beat_data_model.red_motion:
            attrs["red_prop_color"] = self._beat_data_model.red_motion.color
        # Add more visual attributes based on BeatDataModel
        return attrs

    # Commands could be implemented here if actions are specific to this beat
    # e.g., self.delete_command = DeleteBeatCommand(self, beat_operations_service)
```

### 3.6. View (Example: BeatView)

BeatView would be a QWidget or QGraphicsView.
It takes a BeatViewModel in its constructor or via a setter.
It connects to the ViewModel's signals to update its display.
User interactions (e.g., clicks) on the BeatView would call methods or emit signals that the SequenceBeatFrameViewModel (or a parent controller/VM) handles.

```python
# modules/sequence_workbench/views/beat_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

from ..viewmodels.beat_viewmodel import BeatViewModel

class BeatView(QFrame): # Using QFrame for easy bordering and background
    clicked = pyqtSignal(str) # Emits beat_id when clicked

    def __init__(self, view_model: BeatViewModel, parent=None):
        super().__init__(parent)
        self._view_model = view_model
        self.setFixedSize(120, 120) # Example fixed size
        self.setLineWidth(1)
        self.setFrameStyle(QFrame.Shape.Box)

        self._setup_ui()
        self._connect_view_model()

    def _setup_ui(self):
        # Basic UI: a label for the beat number/letter
        self.layout = QVBoxLayout(self)
        self.beat_label = QLabel()
        self.beat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Area for pictograph rendering
        self.pictograph_area = QFrame()
        self.pictograph_area.setFixedSize(80, 80)
        self.pictograph_area.setStyleSheet("background-color: lightgray;")

        self.layout.addWidget(self.beat_label)
        self.layout.addWidget(self.pictograph_area)

        self._update_display()

    def _connect_view_model(self):
        self._view_model.beat_data_model_changed.connect(self._update_display)
        self._view_model.selection_changed.connect(self._handle_selection_changed)
        # Connect to other specific signals as needed

    @pyqtSlot()
    def _update_display(self):
        # Update UI elements based on view_model properties
        self.beat_label.setText(f"{self._view_model.display_beat_number} ({self._view_model.letter or ''})")

        # Trigger a repaint to update custom drawing
        self.update()

    @pyqtSlot(bool)
    def _handle_selection_changed(self, is_selected: bool):
        if is_selected:
            self.setStyleSheet("background-color: lightblue; border: 2px solid blue;")
        else:
            self.setStyleSheet("background-color: white; border: 1px solid gray;")
        self.update() # For border changes

    def paintEvent(self, event):
        super().paintEvent(event) # Handles QFrame's own painting (border, background)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get visual attributes from ViewModel
        attrs = self._view_model.visual_attributes

        # Example: Draw a simple representation of props based on ViewModel data
        # This is where the complex pictograph drawing logic would go,
        # driven entirely by the ViewModel's `visual_attributes`.
        # For now, just draw placeholder colored circles for props.

        rect_width = self.pictograph_area.width() - 20
        rect_height = self.pictograph_area.height() - 20
        center_x = self.pictograph_area.width() / 2
        center_y = self.pictograph_area.height() / 2

        if "blue_prop_color" in attrs:
            painter.setBrush(QColor(attrs["blue_prop_color"]))
            painter.drawEllipse(int(center_x - rect_width / 4), int(center_y - rect_height / 4), int(rect_width/3), int(rect_height/3))

        if "red_prop_color" in attrs:
            painter.setBrush(QColor(attrs["red_prop_color"]))
            painter.drawEllipse(int(center_x + rect_width / 4 - rect_width/3), int(center_y - rect_height / 4), int(rect_width/3), int(rect_height/3))

        # Draw selection highlight if not handled by stylesheet
        if self._view_model.is_selected:
            pen = QPen(QColor("gold"), 3)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(1,1,-1,-1))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._view_model.beat_id)
        super().mousePressEvent(event)

    def set_view_model(self, view_model: BeatViewModel):
        # Disconnect old view_model if any
        if self._view_model:
            try:
                self._view_model.beat_data_model_changed.disconnect(self._update_display)
                self._view_model.selection_changed.disconnect(self._handle_selection_changed)
            except:
                pass # In case signals weren't connected

        self._view_model = view_model
        self._connect_view_model()
        self._update_display()
```

## 4. Key Implementation Patterns

### 4.1. Data Binding

**ViewModel to View:** Use pyqtProperty with notify signals in ViewModels. Views connect to these signals to update themselves.

**View to ViewModel:** User interactions in the View (e.g., button clicks) should trigger methods (commands) on the ViewModel or emit signals that the ViewModel is connected to.

### 4.2. Command Pattern (for Undo/Redo and Actions)

Define command classes (e.g., AddBeatCommand, ChangeDurationCommand) that encapsulate an action and its inverse.
ViewModels will create and execute these commands via an UndoRedoService.

```python
# core/services/undo_redo_service.py (Conceptual)
class Command:
    def execute(self): raise NotImplementedError
    def undo(self): raise NotImplementedError
    def redo(self): self.execute() # Default redo is to re-execute

class UndoRedoService:
    def __init__(self):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def execute_command(self, command: Command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear() # Clear redo stack on new command

    def undo(self):
        if not self.undo_stack: return
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)

    def redo(self):
        if not self.redo_stack: return
        command = self.redo_stack.pop()
        command.redo() # or command.execute()
        self.undo_stack.append(command)
```

### 4.3. Background Processing (QThread)

For long-running tasks like file I/O or image export.
Create a QObject worker that performs the task and move it to a QThread.
Use signals to communicate results/progress back to the main thread (ViewModel).

```python
# Example for a service method
from PyQt6.QtCore import QThread, QObject, pyqtSignal

class FileLoaderWorker(QObject):
    finished = pyqtSignal(object) # Emits loaded data (e.g., SequenceDataModel)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, sequence_management_service_instance):
        super().__init__()
        self.file_path = file_path
        self.sms = sequence_management_service_instance # Pass instance, not class

    @pyqtSlot()
    def run(self):
        try:
            # This is where the actual loading logic from SequenceManagementService would be called
            # For this example, let's assume sms has a _load_data_from_json method
            data = self.sms._load_data_from_json(self.file_path) # Fictional internal method
            sequence_model = self.sms._parse_json_to_sequence_model(data) # Fictional internal method
            self.finished.emit(sequence_model)
        except Exception as e:
            self.error.emit(str(e))
```

### 4.4. Decoupled Image Export

The ImageExportService will take a SequenceDataModel and export options.
It will contain its own rendering logic (not relying on live BeatView widgets).
This might involve creating lightweight utility functions to draw pictograph elements (props, arrows, grids) directly onto a QImage based on BeatDataModel attributes.

## 5. Styling and Theming

Use external QSS files for styling to keep it separate from Python code.
Define a consistent theme (colors, fonts, spacing).
Leverage QPropertyAnimation for smooth transitions and visual feedback.

```css
/* resources/styles/default_theme.qss */
BeatView {
  background-color: white;
  border: 1px solid #cccccc;
  border-radius: 5px;
}

BeatView[selected="true"] {
  /* Custom property for styling selection */
  border: 2px solid #007bff;
  background-color: #e7f3ff;
}

QPushButton {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
}
QPushButton:hover {
  background-color: #0056b3;
}
QPushButton:pressed {
  background-color: #004085;
}
```

## 6. Testing Strategies

**Unit Tests (pytest):**

- Models: Test data integrity, update methods
- Services: Test business logic with mock dependencies
- ViewModels: Test property changes, command execution, interaction with mock services

**Integration Tests:**
Test the interaction between ViewModel, Service, and Model for key user flows (e.g., adding a beat, loading a sequence).

**UI Tests (pytest-qt - optional, can be complex):**
Simulate user interactions and verify UI state changes. Can be brittle but useful for critical paths.

## 7. Conclusion

This guide provides a starting point for implementing the redesigned architecture. The key is to maintain strict separation of concerns, leverage PyQt6's features effectively (signals/slots, properties), and prioritize clean, testable code. Iterative development and refinement will be crucial throughout the implementation phases.
