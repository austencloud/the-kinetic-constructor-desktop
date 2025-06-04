from typing import TYPE_CHECKING


from main_window.main_widget.codex.codex import Codex
from main_window.main_widget.fade_manager.fade_manager import FadeManager
from main_window.main_widget.pictograph_collector import PictographCollector

# SettingsDialog import moved to conditional import in _create_components
from core.migration_adapters import AppContextAdapter
from .construct_tab.construct_tab_factory import ConstructTabFactory
from .generate_tab.generate_tab_factory import GenerateTabFactory
from .learn_tab.learn_tab_factory import LearnTabFactory
from browse_tab.integration.browse_tab_factory import BrowseTabFactory
from .main_background_widget.main_background_widget_factory import (
    MainBackgroundWidgetFactory,
)
from .font_color_updater.font_color_updater import FontColorUpdater
from .sequence_card_tab.utils.tab_factory import SequenceCardTabFactory
from ..menu_bar.menu_bar import MenuBarWidget
from .sequence_workbench.sequence_workbench import SequenceWorkbench
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)

if TYPE_CHECKING:
    from .main_widget import MainWidget


class MainWidgetUI:
    def __init__(self, main_widget: "MainWidget"):
        self.mw = main_widget
        self.splash_screen = main_widget.splash_screen
        self._create_components()
        self._populate_stacks()
        self._initialize_layout()
        # Defer the final step until the widget has actually been laid out/shown:

    def _create_components(self):
        mw = self.mw
        print("[DEBUG] _create_components called - creating settings dialog...")

        # Get app_context for dependency injection
        app_context = getattr(mw, "app_context", None)
        mw.fade_manager = FadeManager(mw, app_context)

        mw.sequence_workbench = SequenceWorkbench(mw)

        # Use the modern settings dialog with dependency injection
        try:
            from .settings_dialog.settings_dialog_factory import SettingsDialogFactory
            from .settings_dialog.tabs.settings_tab_manager import (
                SettingsTabImportError,
            )

            if app_context:
                mw.settings_dialog = SettingsDialogFactory.create(mw, app_context)
                print(
                    "[SUCCESS] Using modern settings dialog with dependency injection!"
                )
            else:
                # Fallback to direct creation for backward compatibility
                from .settings_dialog.modern_settings_dialog import ModernSettingsDialog

                mw.settings_dialog = ModernSettingsDialog(mw)
                print("[SUCCESS] Using modern settings dialog (legacy mode)!")

        except SettingsTabImportError as e:
            # Critical error - settings tabs are missing or broken
            error_msg = f"CRITICAL ERROR: Settings dialog cannot be initialized due to missing or broken tab implementations.\n\nError: {e}\n\nThe application cannot start properly without functional settings tabs."
            print(f"[CRITICAL ERROR] {error_msg}")

            # Show error dialog to user and exit
            from PyQt6.QtWidgets import QMessageBox, QApplication

            app = QApplication.instance()
            if app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Critical Application Error")
                msg_box.setText("Settings Dialog Initialization Failed")
                msg_box.setDetailedText(error_msg)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()

            # Exit the application - we cannot continue without functional settings
            import sys

            sys.exit(1)

        except Exception as e:
            # Unexpected error - still critical but different handling
            error_msg = f"UNEXPECTED ERROR: Failed to create settings dialog due to an unexpected error.\n\nError: {e}\n\nThis may indicate a code issue that needs to be fixed."
            print(f"[UNEXPECTED ERROR] {error_msg}")

            # Show error dialog to user and exit
            from PyQt6.QtWidgets import QMessageBox, QApplication

            app = QApplication.instance()
            if app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Unexpected Application Error")
                msg_box.setText("Settings Dialog Creation Failed")
                msg_box.setDetailedText(error_msg)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()

            # Exit the application - we cannot continue without settings
            import sys

            sys.exit(1)

        mw.left_stack = QStackedWidget()
        mw.right_stack = QStackedWidget()
        # set size policy to fixed

        mw.font_color_updater = FontColorUpdater(mw)
        mw.pictograph_collector = PictographCollector(mw)

        mw.menu_bar = MenuBarWidget(mw)
        mw.codex = Codex(mw)

        # Use legacy compatibility during transition
        # This will be replaced when MainWidget is fully migrated to MainWidgetCoordinator

        # Get dependencies from legacy adapter during transition period
        settings_manager = AppContextAdapter.settings_manager()
        json_manager = AppContextAdapter.json_manager()

        # Create a temporary app context for the transition period
        from core.application_context import ApplicationContext
        from core.dependency_container import get_container

        # Get the global container that was set up in main.py
        container = get_container()
        temp_app_context = ApplicationContext(container)

        # Use factories with the new dependency injection pattern
        # The factories will handle the transition gracefully
        try:
            mw.construct_tab = ConstructTabFactory.create(mw, temp_app_context)
        except TypeError:
            # Fallback to old pattern if factory hasn't been updated yet
            from .construct_tab.construct_tab import ConstructTab

            mw.construct_tab = ConstructTab(
                beat_frame=mw.sequence_workbench.beat_frame,
                pictograph_dataset={},
                size_provider=lambda: mw.size(),
                fade_to_stack_index=lambda index: mw.fade_manager.stack_fader.fade_stack(
                    mw.right_stack, index
                ),
                fade_manager=mw.fade_manager,
                settings_manager=settings_manager,
                json_manager=json_manager,
            )

        try:
            mw.generate_tab = GenerateTabFactory.create(mw, temp_app_context)
        except TypeError:
            from .generate_tab.generate_tab import GenerateTab

            mw.generate_tab = GenerateTab(mw, settings_manager, json_manager)

        # Create Browse Tab using the new factory system
        mw.browse_tab = BrowseTabFactory.create(mw, temp_app_context)

        try:
            mw.learn_tab = LearnTabFactory.create(mw, temp_app_context)
        except TypeError:
            from .learn_tab.learn_tab import LearnTab

            mw.learn_tab = LearnTab(mw, settings_manager, json_manager)

        try:
            mw.sequence_card_tab = SequenceCardTabFactory.create(mw, temp_app_context)
        except TypeError:
            from .sequence_card_tab.tab import SequenceCardTab

            mw.sequence_card_tab = SequenceCardTab(mw, settings_manager, json_manager)
        # mw.write_tab = WriteTab(mw)

        mw.background_widget = MainBackgroundWidgetFactory.create(
            main_widget=mw, settings_manager=settings_manager
        )
        mw.background_widget.lower()
        mw.state_handler.load_state(mw.sequence_workbench.beat_frame)
        self.splash_screen.updater.update_progress("Finalizing")
        mw.font_color_updater.update_main_widget_font_colors(
            settings_manager.get_global_settings().get_background_type()
        )

    def _populate_stacks(self):
        mw = self.mw

        mw.left_stack.addWidget(mw.sequence_workbench)  # 0
        mw.left_stack.addWidget(mw.codex)  # 1
        # ARCHITECTURAL FIX: Remove filter_stack from main widget - it should live inside browse_tab
        # mw.left_stack.addWidget(mw.browse_tab.sequence_picker.filter_stack)  # 2 - REMOVED
        mw.left_stack.addWidget(mw.browse_tab)  # 2 - Add entire browse_tab instead

        mw.right_stack.addWidget(mw.construct_tab.start_pos_picker)  # 0
        mw.right_stack.addWidget(mw.construct_tab.advanced_start_pos_picker)  # 1
        mw.right_stack.addWidget(mw.construct_tab.option_picker)  # 2
        mw.right_stack.addWidget(mw.generate_tab)  # 3
        mw.right_stack.addWidget(mw.learn_tab)  # 4
        mw.right_stack.addWidget(mw.browse_tab.sequence_viewer)  # 5
        mw.right_stack.addWidget(mw.sequence_card_tab)  # 6

    def _initialize_layout(self):
        mw = self.mw

        mw.main_layout = QVBoxLayout(mw)
        mw.main_layout.setContentsMargins(0, 0, 0, 0)
        mw.main_layout.setSpacing(0)
        mw.setLayout(mw.main_layout)

        top_layout = QHBoxLayout()
        top_layout.addWidget(mw.menu_bar.social_media_widget, 1)
        top_layout.addWidget(mw.menu_bar.navigation_widget, 16)
        top_layout.addWidget(mw.menu_bar.settings_button, 1)

        content_layout = QHBoxLayout()
        content_layout.addWidget(mw.left_stack, 2)  # 2/3 width for left stack
        content_layout.addWidget(mw.right_stack, 1)  # 1/3 width for right stack

        # Store reference to content layout for dynamic ratio changes
        mw.content_layout = content_layout

        mw.main_layout.addLayout(top_layout)
        mw.main_layout.addLayout(content_layout)
