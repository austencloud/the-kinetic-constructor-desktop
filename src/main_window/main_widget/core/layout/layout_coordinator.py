"""
Layout Coordinator - Manages different layout modes and transitions.

This coordinator extracts layout management logic from MainWidgetCoordinator
following the Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget

from .layout_mode import LayoutMode

if TYPE_CHECKING:
    from ..tab_manager import TabManager
    from ..main_widget_coordinator import MainWidgetCoordinator


class LayoutCoordinator:
    """
    Manages different layout modes and transitions.

    Responsibilities:
    - Switch between stack and full-widget layouts
    - Manage layout stretch factors
    - Handle layout mode state
    - Coordinate with TabManager for layout changes
    """

    def __init__(self, coordinator: "MainWidgetCoordinator", tab_manager: "TabManager"):
        self.coordinator = coordinator
        self.tab_manager = tab_manager
        self.logger = logging.getLogger(__name__)

        # Track current layout mode
        self._current_layout_mode = LayoutMode.STACK

        self.logger.info("LayoutCoordinator initialized")

    def switch_to_stack_layout(
        self, left_stretch: int = 1, right_stretch: int = 1
    ) -> None:
        """
        Switch to stack-based layout mode for construct/generate/learn tabs.

        Args:
            left_stretch: Stretch factor for left stack
            right_stretch: Stretch factor for right stack
        """
        self.logger.debug(
            f"Switching to stack layout with stretch {left_stretch}:{right_stretch}"
        )

        if self._current_layout_mode != LayoutMode.STACK:
            self.coordinator.main_content_stack.setCurrentIndex(
                0
            )  # Show stack container
            self._current_layout_mode = LayoutMode.STACK

        # Apply stretch factors to the content layout
        self.coordinator.content_layout.setStretch(0, left_stretch)
        self.coordinator.content_layout.setStretch(1, right_stretch)

        # Clear any fixed width constraints
        self.coordinator.left_stack.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
        self.coordinator.left_stack.setMinimumWidth(0)
        self.coordinator.right_stack.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
        self.coordinator.right_stack.setMinimumWidth(0)

        self.logger.debug("Stack layout activated")

    def switch_to_full_widget_layout(self, tab_widget: QWidget) -> None:
        """
        Switch to full-widget layout mode for browse/sequence_card tabs.

        Args:
            tab_widget: The tab widget that should take full control of the layout
        """
        self.logger.debug(
            f"Switching to full widget layout for {tab_widget.__class__.__name__}"
        )

        # Check if this tab widget is already in the main content stack
        tab_index = -1
        for i in range(
            1, self.coordinator.main_content_stack.count()
        ):  # Skip index 0 (stack container)
            if self.coordinator.main_content_stack.widget(i) is tab_widget:
                tab_index = i
                break

        # If not found, add it to the stack with proper size hint management
        if tab_index == -1:
            # RESPONSIVE FIX: Prevent size propagation through proper size hint management
            from PyQt6.QtWidgets import QSizePolicy
            from PyQt6.QtCore import QSize

            # Ensure the tab widget has proper size policies for responsive behavior
            if hasattr(tab_widget, "setSizePolicy"):
                # Set responsive size policy that prevents unwanted expansion
                tab_widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
                    QSizePolicy.Policy.Preferred,  # Prefer natural height, don't force expansion
                )

            # Override sizeHint temporarily during addition to prevent layout recalculation
            original_sizeHint = None
            if hasattr(tab_widget, "sizeHint"):
                original_sizeHint = tab_widget.sizeHint

                # Provide a stable size hint that matches current main window content area
                def stable_sizeHint():
                    # Calculate proportional size based on main window dimensions
                    main_window = self.coordinator.parent()
                    while main_window and not hasattr(main_window, "geometry_manager"):
                        main_window = main_window.parent()

                    if main_window:
                        window_size = main_window.size()
                        # Account for menu bar (approximately 52px) and margins
                        content_height = window_size.height() - 52
                        return QSize(window_size.width(), content_height)
                    else:
                        # Fallback to reasonable default
                        return QSize(2304, 1200)

                tab_widget.sizeHint = stable_sizeHint

            # Add widget to stack
            tab_index = self.coordinator.main_content_stack.addWidget(tab_widget)
            self.logger.debug(
                f"Added tab widget to stack at index {tab_index} with responsive sizing"
            )

            # Restore original sizeHint if it was overridden
            if original_sizeHint:
                tab_widget.sizeHint = original_sizeHint

        # Switch to the tab widget
        self.coordinator.main_content_stack.setCurrentIndex(tab_index)
        self._current_layout_mode = LayoutMode.FULL_WIDGET

        self.logger.debug("Full widget layout activated")

    def get_current_layout_mode(self) -> LayoutMode:
        """Get the current layout mode."""
        return self._current_layout_mode

    def setup_initial_layout(self) -> None:
        """Set up the initial layout structure."""
        self.logger.debug("Setting up initial layout structure")

        # Create horizontal layout for main content (stack-based tabs)
        from PyQt6.QtWidgets import QHBoxLayout, QStackedWidget

        self.coordinator.content_layout = QHBoxLayout()
        self.coordinator.content_layout.setContentsMargins(0, 0, 0, 0)
        self.coordinator.content_layout.setSpacing(0)

        # Add stacked widgets for left and right panels
        self.coordinator.left_stack = QStackedWidget()
        self.coordinator.right_stack = QStackedWidget()

        # Add widgets with initial equal stretch ratio
        self.coordinator.content_layout.addWidget(
            self.coordinator.left_stack, 1
        )  # Left stack
        self.coordinator.content_layout.addWidget(
            self.coordinator.right_stack, 1
        )  # Right stack

        # Create a stacked widget to hold different layout modes with responsive sizing
        self.coordinator.main_content_stack = QStackedWidget()

        # RESPONSIVE FIX: Apply proper size policies for responsive behavior
        from PyQt6.QtWidgets import QWidget, QSizePolicy

        # Set responsive size policy that allows expansion but prevents unwanted size propagation
        self.coordinator.main_content_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Allow horizontal expansion
            QSizePolicy.Policy.Preferred,  # Prefer natural height, don't force expansion
        )

        self.coordinator.stack_container = QWidget()
        self.coordinator.stack_container.setLayout(self.coordinator.content_layout)

        # Add the stack container as the first widget (index 0)
        self.coordinator.main_content_stack.addWidget(self.coordinator.stack_container)

        # Note: Full-widget tabs will be added to main_content_stack at indices 1+
        # Menu bar will be added to the layout after widgets are initialized
        self.coordinator.main_layout.addWidget(self.coordinator.main_content_stack)

        self.logger.debug("Initial layout structure created")

    def update_layout_for_tab(self, tab_name: str) -> None:
        """
        Update layout based on the active tab.

        Args:
            tab_name: Name of the active tab
        """
        self.logger.debug(f"Updating layout for tab: {tab_name}")

        # Get tab widget from tab manager
        tab_widget = self.tab_manager.get_tab_widget(tab_name)
        if not tab_widget:
            self.logger.warning(f"Tab widget not found for {tab_name}")
            return

        # Determine layout mode based on tab type
        full_widget_tabs = ["browse", "sequence_card"]

        if tab_name in full_widget_tabs:
            self.switch_to_full_widget_layout(tab_widget)
        else:
            # Default to stack layout for construct/generate/learn tabs
            self.switch_to_stack_layout()

        self.logger.debug(f"Layout updated for tab {tab_name}")

    def get_layout_info(self) -> dict:
        """
        Get current layout information for debugging.

        Returns:
            Dictionary with layout state information
        """
        return {
            "current_mode": self._current_layout_mode.value,
            "stack_index": self.coordinator.main_content_stack.currentIndex(),
            "stack_count": self.coordinator.main_content_stack.count(),
            "left_stretch": self.coordinator.content_layout.stretch(0),
            "right_stretch": self.coordinator.content_layout.stretch(1),
        }
