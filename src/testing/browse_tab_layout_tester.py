"""
Automated Browse Tab Layout Testing System

This module provides comprehensive automated testing for the Browse Tab layout
regression issue, monitoring sequence viewer width and simulating user interactions.
"""

from .browse_tab_layout_monitor import BrowseTabLayoutMonitor
from .browse_tab_mock_interactor import BrowseTabMockInteractor
from .browse_tab_automated_tester import (
    BrowseTabAutomatedTester,
    run_automated_browse_tab_test,
)

__all__ = [
    "BrowseTabLayoutMonitor",
    "BrowseTabMockInteractor",
    "BrowseTabAutomatedTester",
    "run_automated_browse_tab_test",
]
