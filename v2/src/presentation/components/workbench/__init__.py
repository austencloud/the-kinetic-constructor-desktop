"""
Sequence Workbench Components

V2 sequence workbench with modern architecture.
"""

from src.presentation.components.workbench.beat_frame import (
    ModernBeatFrame,
    ModernBeatView,
    StartPositionView,
    BeatSelectionManager,
)

from .workbench import (
    ModernSequenceWorkbench,
)

from .indicator_section import WorkbenchIndicatorSection
from .beat_frame_section import WorkbenchBeatFrameSection
from .graph_section import WorkbenchGraphSection
from .event_controller import WorkbenchEventController
from .button_interface import (
    WorkbenchButtonInterfaceAdapter,
    IWorkbenchButtonInterface,
    WorkbenchButtonSignals,
    ButtonOperationResult,
)

# Legacy compatibility
from .button_interface import (
    WorkbenchButtonInterfaceAdapter as ButtonInterface,
)

__all__ = [
    "ModernSequenceWorkbench",
    "ModernBeatFrame",
    "ModernBeatView",
    "StartPositionView",
    "BeatSelectionManager",
    # Core components
    "WorkbenchIndicatorSection",
    "WorkbenchBeatFrameSection",
    "WorkbenchGraphSection",
    "WorkbenchEventController",
    # Interface adapters
    "WorkbenchButtonInterfaceAdapter",
    "IWorkbenchButtonInterface",
    "WorkbenchButtonSignals",
    "ButtonOperationResult",
    "ButtonInterface",  # Legacy alias
]
