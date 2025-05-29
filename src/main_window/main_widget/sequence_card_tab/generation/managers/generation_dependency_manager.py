import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main_window.main_widget.generate_tab.generate_tab import GenerateTab
    from main_window.main_widget.main_widget import MainWidget


class GenerationDependencyManager:
    def __init__(self, main_widget: "MainWidget"):
        self.main_widget = main_widget
        self.generate_tab: Optional["GenerateTab"] = None
        self.logger = logging.getLogger(__name__)

    def initialize_generate_tab(self) -> bool:
        try:
            return self._refresh_generate_tab_reference()
        except Exception as e:
            self.logger.error(f"Error initializing generate tab reference: {e}")
            return False

    def _refresh_generate_tab_reference(self) -> bool:
        try:
            if (
                hasattr(self.main_widget, "generate_tab")
                and self.main_widget.generate_tab is not None
            ):
                self.generate_tab = self.main_widget.generate_tab
                return self._ensure_all_dependencies()

            if hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager
                if hasattr(tab_manager, "tabs") and "generate" in tab_manager.tabs:
                    self.generate_tab = tab_manager.tabs["generate"]
                    return self._ensure_all_dependencies()

                if hasattr(tab_manager, "_create_tab"):
                    self.logger.info("Attempting to create generate tab...")
                    generate_tab = tab_manager._create_tab("generate")
                    if generate_tab:
                        self.generate_tab = generate_tab
                        self.logger.info("Generate tab created successfully!")

                        if not self._ensure_construct_tab_available():
                            self.logger.warning(
                                "Could not ensure construct tab availability"
                            )

                        return self._ensure_all_dependencies()

            if self.generate_tab is None:
                self.logger.warning(
                    "Generate tab not available for sequence generation"
                )
            return False
        except Exception as e:
            self.logger.error(f"Error refreshing generate tab reference: {e}")
            return False

    def _ensure_construct_tab_available(self) -> bool:
        try:
            if hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager

                if hasattr(tab_manager, "tabs") and "construct" in tab_manager.tabs:
                    self.logger.info("Construct tab already available")
                    return True

                if hasattr(tab_manager, "_create_tab"):
                    self.logger.info(
                        "Attempting to create construct tab for generation dependencies..."
                    )
                    construct_tab = tab_manager._create_tab("construct")
                    if construct_tab:
                        self.logger.info("Construct tab created successfully!")
                        return True
                    else:
                        self.logger.error("Failed to create construct tab")
                        return False

            return False
        except Exception as e:
            self.logger.error(f"Error ensuring construct tab availability: {e}")
            return False

    def _ensure_all_dependencies(self) -> bool:
        try:
            if not self.generate_tab:
                return False

            if not hasattr(self.generate_tab, "freeform_builder") or not hasattr(
                self.generate_tab, "circular_builder"
            ):
                self.logger.warning("Generate tab missing sequence builders")
                return False

            construct_tab_available = False

            if hasattr(self.main_widget, "tab_manager"):
                tab_manager = self.main_widget.tab_manager
                self.logger.info(f"Tab manager found: {tab_manager}")
                self.logger.info(
                    f"Available tabs: {list(tab_manager._tabs.keys()) if hasattr(tab_manager, '_tabs') else 'No _tabs attribute'}"
                )

                if hasattr(tab_manager, "_tabs") and "construct" in tab_manager._tabs:
                    construct_tab = tab_manager._tabs["construct"]
                    self.logger.info(
                        f"Found construct tab: {type(construct_tab).__name__}"
                    )

                    if hasattr(construct_tab, "option_picker"):
                        option_picker = construct_tab.option_picker
                        self.logger.info(
                            f"Found option_picker: {type(option_picker).__name__}"
                        )

                        if hasattr(option_picker, "option_getter"):
                            option_getter = option_picker.option_getter
                            self.logger.info(
                                f"Found option_getter: {type(option_getter).__name__}"
                            )

                            if hasattr(option_getter, "_load_all_next_option_dicts"):
                                self.logger.info(
                                    "✅ All construct tab dependencies verified - option generation available"
                                )
                                construct_tab_available = True
                            else:
                                self.logger.error(
                                    "option_getter missing _load_all_next_option_dicts method"
                                )
                        else:
                            self.logger.error(
                                "option_picker missing option_getter attribute"
                            )
                    else:
                        self.logger.error(
                            "construct_tab missing option_picker attribute"
                        )
                else:
                    self.logger.error("construct tab not found in tab_manager._tabs")
            else:
                self.logger.error("main_widget missing tab_manager")

            if not construct_tab_available:
                self.logger.error(
                    "CRITICAL: Construct tab dependencies not available - sequence generation will produce identical sequences"
                )
                self.logger.error(
                    "The freeform builder requires construct_tab.option_picker.option_getter._load_all_next_option_dicts() to access sequence options"
                )
                self.logger.error(
                    "Without this, random.choice(option_dicts) will always choose from the same limited set"
                )
                return False

            self.logger.info("All generation dependencies verified successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying generation dependencies: {e}")
            return False

    def is_available(self) -> bool:
        if self.generate_tab is None:
            self._refresh_generate_tab_reference()
        return self.generate_tab is not None

    def get_generate_tab(self) -> Optional["GenerateTab"]:
        return self.generate_tab
