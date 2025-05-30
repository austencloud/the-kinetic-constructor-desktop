"""
Layout mode enumeration for MainWidgetCoordinator.
"""

from enum import Enum


class LayoutMode(Enum):
    """
    Enumeration of available layout modes.
    
    STACK: Stack-based layout for construct/generate/learn tabs
    FULL_WIDGET: Full-widget layout for browse/sequence_card tabs
    """
    
    STACK = "stack"
    FULL_WIDGET = "full_widget"
