"""
UI Components for Browse Tab v2 - Clean Architecture Implementation.

This package contains UI component classes that follow the single responsibility principle.
Each component is focused on one specific UI concern and is <200 lines.

Legacy Components (to be refactored):
- BrowseTabView: Original monolithic view (1315 lines - TO BE REPLACED)

Phase 2 Modern UI Components (existing):
- ResponsiveThumbnailGrid, ModernThumbnailCard, SmartFilterPanel, etc.

Phase 3 Clean Architecture Components (✅ COMPLETE):
- FilterPanel: Search and filtering UI (<200 lines) ✅
- GridView: Thumbnail grid display (<200 lines) ✅
- SequenceViewer: Sequence detail display (<200 lines) ✅
- NavigationSidebar: Alphabet navigation (<200 lines) ✅
- ThumbnailCard: Individual thumbnail widget (<200 lines) ✅

All Phase 3 components follow 2025 best practices with single responsibility,
glassmorphism styling, performance optimization, and clean signal/slot architecture.
"""

# Phase 2 components removed during cleanup - no longer needed
# All functionality replaced by Phase 3 clean architecture components

# Phase 3 Clean Architecture Components (✅ COMPLETE)
from .filter_panel import FilterPanel
from .grid_view import GridView
from .sequence_viewer import SequenceViewer
from .navigation_sidebar import NavigationSidebar
from .thumbnail_card import ThumbnailCard

# Phase 3 Coordinator (✅ NEW - Replaces legacy BrowseTabView)
from .coordinator import BrowseTabV2Coordinator

__all__ = [
    # Phase 3 Clean Architecture Components (Post-Cleanup)
    "FilterPanel",
    "GridView",
    "SequenceViewer",
    "NavigationSidebar",
    "ThumbnailCard",
    "BrowseTabV2Coordinator",
    # All Phase 2 and legacy components removed during cleanup
]
