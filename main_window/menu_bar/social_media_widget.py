from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QPushButton
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtCore import Qt, QSize, QUrl

if TYPE_CHECKING:
    from main_window.menu_bar.menu_bar import MenuBarWidget


class SocialMediaWidget(QWidget):
    """Handles all social media link buttons."""

    def __init__(self, menu_bar: "MenuBarWidget"):
        super().__init__(menu_bar)
        self.main_widget = menu_bar.main_widget

        # Core layout
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(10)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create buttons
        self.paypal_button = self._create_icon_button(
            icon_path="images/icons/paypal.png",
            tooltip="Support via PayPal",
            click_handler=self._open_paypal_link,
        )
        self.venmo_button = self._create_icon_button(
            icon_path="images/icons/venmo.png",
            tooltip="Support via Venmo",
            click_handler=self._open_venmo_link,
        )
        self.github_button = self._create_icon_button(
            icon_path="images/icons/github.png",
            tooltip="View project on GitHub",
            click_handler=self._open_github_link,
        )
        self.facebook_button = self._create_icon_button(
            icon_path="images/icons/facebook.png",
            tooltip="Visit on Facebook",
            click_handler=self._open_facebook_link,
        )
        self.instagram_button = self._create_icon_button(
            icon_path="images/icons/instagram.png",
            tooltip="Follow on Instagram",
            click_handler=self._open_instagram_link,
        )
        self.youtube_button = self._create_icon_button(
            icon_path="images/icons/youtube.png",
            tooltip="Follow on YouTube",
            click_handler=self._open_youtube_link,
        )

        # Combine them in a list for easy iteration
        self.social_buttons = [
            self.paypal_button,
            self.venmo_button,
            self.github_button,
            self.facebook_button,
            self.instagram_button,
            self.youtube_button,
        ]

        # Place them in a two-row, three-column layout
        for index, button in enumerate(self.social_buttons):
            row = index // 3  # 0 or 1
            col = index % 3  # 0, 1, or 2
            self._grid_layout.addWidget(button, row, col)

        # Root layout for this widget
        root_layout = QVBoxLayout(self)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addLayout(self._grid_layout)
        self.setLayout(root_layout)

    def _create_icon_button(self, icon_path, tooltip, click_handler):
        """Creates a single icon button."""
        button = QPushButton()
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        icon = QIcon(icon_path)
        button.setIcon(icon)
        icon_size = QSize(
            self.main_widget.height() // 40,
            self.main_widget.height() // 40,
        )
        button.setIconSize(icon_size)
        button.setFixedSize(icon_size.width() + 10, icon_size.height() + 10)
        button.setStyleSheet(
            """
            QPushButton {
                border: none;
                background-color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            """
        )
        button.setToolTip(tooltip)
        button.clicked.connect(click_handler)
        return button

    def resize_social_media_buttons(self):
        """Resizes social media buttons on window resize."""
        icon_size = QSize(
            self.main_widget.height() // 40,
            self.main_widget.height() // 40,
        )
        for button in self.social_buttons:
            button.setIconSize(icon_size)
            button.setFixedSize(icon_size.width() + 10, icon_size.height() + 10)

    # ---- Social link handlers ----
    def _open_paypal_link(self):
        """Opens PayPal support page."""
        QDesktopServices.openUrl(QUrl("https://www.paypal.me/austencloud"))

    def _open_venmo_link(self):
        """Opens Venmo link."""
        QDesktopServices.openUrl(QUrl("https://venmo.com/austencloud"))

    def _open_github_link(self):
        """Opens GitHub repo."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/austencloud/the-kinetic-constructor")
        )

    def _open_facebook_link(self):
        """Opens Facebook page."""
        QDesktopServices.openUrl(QUrl("https://www.facebook.com/thekineticalphabet"))

    def _open_instagram_link(self):
        """Opens Instagram profile."""
        QDesktopServices.openUrl(QUrl("https://www.instagram.com/thekineticalphabet"))

    def _open_youtube_link(self):
        """Opens YouTube channel."""
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/channel/UCbLHNRSASZS_gwkmRATH1-A"))
