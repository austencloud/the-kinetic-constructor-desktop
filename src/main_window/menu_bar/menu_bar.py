from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtGui import QResizeEvent

from main_window.menu_bar.navigation_widget.menu_bar_nav_widget import MenuBarNavWidget
from main_window.menu_bar.settings_button import SettingsButton
from .social_media_widget import SocialMediaWidget

if TYPE_CHECKING:
    from main_window.main_widget.main_widget import MainWidget


class MenuBarWidget(QWidget):
    def __init__(self, main_widget: "MainWidget") -> None:
        super().__init__(main_widget)
        self.main_widget: "MainWidget" = main_widget
        self.main_widget.splash_screen.updater.update_progress("MenuBarWidget")

        self._setup_layout()
        self._create_widgets()
        self._apply_styles()

    def _setup_layout(self) -> None:
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(15)

    def _create_widgets(self) -> None:
        self.social_media_widget = SocialMediaWidget(self)
        self.navigation_widget = MenuBarNavWidget(self)
        self.settings_button = SettingsButton(self)

        self.layout.addWidget(self.social_media_widget)
        self.layout.addStretch()
        self.layout.addWidget(self.navigation_widget)
        self.layout.addStretch()
        self.layout.addWidget(self.settings_button)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            MenuBarWidget {
                background-color: #2b2b2b;
                border-bottom: 1px solid #404040;
                min-height: 50px;
            }
            
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                min-height: 40px;
                min-width: 80px;
                padding: 8px 16px;
            }
            
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #666666;
            }
            
            QPushButton:pressed {
                background-color: #2a2a2a;
                border-color: #777777;
            }
            
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #888888;
                border-color: #333333;
            }
        """
        )

    def resizeEvent(self, event: Optional[QResizeEvent]) -> None:
        super().resizeEvent(event)
        if hasattr(self, "social_media_widget"):
            self.social_media_widget.resize_social_media_buttons()
