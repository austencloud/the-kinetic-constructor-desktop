from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget
from .browse_tab_adapter import BrowseTabV2Adapter

if TYPE_CHECKING:
    from main_window.main_widget.core.main_widget_coordinator import (
        MainWidgetCoordinator,
    )


class BrowseTabFactory:
    @staticmethod
    def create(parent: "MainWidgetCoordinator", app_context=None) -> QWidget:
        json_manager = (
            getattr(app_context, "json_manager", None) if app_context else None
        )
        settings_manager = (
            getattr(app_context, "settings_manager", None) if app_context else None
        )

        return BrowseTabV2Adapter(
            parent=parent, json_manager=json_manager, settings_manager=settings_manager
        )
