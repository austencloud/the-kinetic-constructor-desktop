"""
Lazy JsonManager implementation to break circular dependencies.

This version defers the creation of dependencies until they are actually needed,
preventing circular dependency issues during initialization.
"""

import logging
from typing import TYPE_CHECKING, Dict, Any, List, Optional

from src.interfaces.json_manager_interface import IJsonManager
from src.main_window.main_widget.json_manager.json_act_saver import JsonActSaver
from src.main_window.main_widget.json_manager.json_sequence_updater.json_sequence_updater import (
    JsonSequenceUpdater,
)
from .json_ori_calculator import JsonOriCalculator
from .json_ori_validation_engine import JsonOriValidationEngine
from .json_start_position_handler import JsonStartPositionHandler

if TYPE_CHECKING:
    from core.application_context import ApplicationContext
    from .sequence_data_loader_saver import SequenceDataLoaderSaver


class LazyJsonManager:  # IJsonManager is a Protocol, no need to inherit
    """
    Lazy JsonManager that defers dependency creation to break circular dependencies.
    
    This implementation creates dependencies only when they are first accessed,
    preventing the circular dependency chain that occurs during initialization.
    """

    def __init__(self, app_context: Optional["ApplicationContext"] = None) -> None:
        """
        Initialize LazyJsonManager with optional dependency injection.

        Args:
            app_context: Application context with dependencies. If None, uses legacy approach.
        """
        self.logger = logging.getLogger(__name__)
        self._app_context = app_context
        
        # Lazy-loaded dependencies
        self._loader_saver: Optional["SequenceDataLoaderSaver"] = None
        self._updater: Optional[JsonSequenceUpdater] = None
        self._start_pos_handler: Optional[JsonStartPositionHandler] = None
        self._ori_validation_engine: Optional[JsonOriValidationEngine] = None
        
        # These don't cause circular dependencies, so create them immediately
        self.ori_calculator = JsonOriCalculator()
        self.act_saver = JsonActSaver()

    @property
    def loader_saver(self) -> "SequenceDataLoaderSaver":
        """Lazy property for SequenceDataLoaderSaver."""
        if self._loader_saver is None:
            from .sequence_data_loader_saver import SequenceDataLoaderSaver
            self.logger.debug("Lazy-loading SequenceDataLoaderSaver")
            self._loader_saver = SequenceDataLoaderSaver(self._app_context)
        return self._loader_saver

    @property
    def updater(self) -> JsonSequenceUpdater:
        """Lazy property for JsonSequenceUpdater."""
        if self._updater is None:
            self.logger.debug("Lazy-loading JsonSequenceUpdater")
            self._updater = JsonSequenceUpdater(self)
        return self._updater

    @property
    def start_pos_handler(self) -> JsonStartPositionHandler:
        """Lazy property for JsonStartPositionHandler."""
        if self._start_pos_handler is None:
            self.logger.debug("Lazy-loading JsonStartPositionHandler")
            self._start_pos_handler = JsonStartPositionHandler(self)
        return self._start_pos_handler

    @property
    def ori_validation_engine(self) -> JsonOriValidationEngine:
        """Lazy property for JsonOriValidationEngine."""
        if self._ori_validation_engine is None:
            self.logger.debug("Lazy-loading JsonOriValidationEngine")
            self._ori_validation_engine = JsonOriValidationEngine(self)
        return self._ori_validation_engine

    def save_act(self, act_data: dict):
        """Save the act using the JsonActSaver."""
        self.act_saver.save_act(act_data)

    # IJsonManager interface implementation
    def save_sequence(self, sequence_data: List[Dict[str, Any]]) -> bool:
        """Save the current sequence to the default location."""
        return self.loader_saver.save_sequence(sequence_data)

    def load_sequence(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load a sequence from the specified file path or the default location."""
        return self.loader_saver.load_sequence(file_path)

    def get_updater(self):
        """Get the JSON sequence updater."""
        return self.updater

    def set_app_context(self, app_context: "ApplicationContext") -> None:
        """
        Set the application context after initialization.
        
        This allows the JsonManager to be created without dependencies
        and have them injected later.
        
        Args:
            app_context: The application context with dependencies
        """
        self._app_context = app_context
        
        # Reset lazy-loaded dependencies so they use the new context
        self._loader_saver = None
        self._updater = None
        self._start_pos_handler = None
        self._ori_validation_engine = None
        
        self.logger.info("Application context injected into LazyJsonManager")
