"""
Instant Browse Tab Manager

This module provides instant browse tab initialization using pre-loaded data
from the optimized startup preloader. It eliminates all visible loading delays
by using cached data and pre-initialized components.

Key Features:
1. Instant widget population from cached data
2. Pre-loaded thumbnail display
3. Zero cache misses for initial view
4. Immediate navigation responsiveness
5. Background completion of remaining data
"""

import logging
import time
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QWidget

from .optimized_startup_preloader import get_optimized_data, is_optimization_completed
from ..core.interfaces import SequenceModel
from ..components.modern_thumbnail_card import ModernThumbnailCard

logger = logging.getLogger(__name__)


class InstantBrowseTabManager(QObject):
    """
    Manages instant browse tab initialization using pre-loaded data.
    """

    # Signals for instant updates
    instant_data_ready = pyqtSignal()
    background_loading_complete = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Pre-loaded data
        self.optimized_data: Optional[Dict[str, Any]] = None
        self.sequences: List[SequenceModel] = []
        self.critical_thumbnails: Dict[str, str] = {}
        self.navigation_data: Dict[str, Any] = {}

        # Widget references
        self.thumbnail_cards: List[ModernThumbnailCard] = []
        self.navigation_sidebar: Optional[QWidget] = None
        self.sequence_viewer: Optional[QWidget] = None

        # State tracking
        self.instant_initialization_complete = False
        self.background_loading_complete_flag = False

        # Background loading timer
        self.background_timer = QTimer()
        self.background_timer.setSingleShot(True)
        self.background_timer.timeout.connect(self._complete_background_loading)

        logger.debug("InstantBrowseTabManager initialized")

    def initialize_instantly(self) -> bool:
        """
        Initialize browse tab instantly using pre-loaded data.

        Returns:
            bool: True if instant initialization was successful
        """
        start_time = time.time()

        try:
            # Check if optimization data is available
            if not is_optimization_completed():
                logger.warning(
                    "Optimization not completed, falling back to normal loading"
                )
                return False

            # Get pre-loaded data
            self.optimized_data = get_optimized_data()
            if not self.optimized_data:
                logger.warning("No optimized data available")
                return False

            # Extract pre-loaded components
            self.sequences = self.optimized_data.get("sequences", [])
            self.critical_thumbnails = self.optimized_data.get(
                "critical_thumbnails", {}
            )
            self.navigation_data = self.optimized_data.get("navigation_data", {})

            # Validate data
            if not self.sequences:
                logger.warning("No sequences in optimized data")
                return False

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Instant browse tab initialization completed in {duration_ms:.1f}ms"
            )
            logger.info(
                f"   Available: {len(self.sequences)} sequences, {len(self.critical_thumbnails)} cached thumbnails"
            )

            self.instant_initialization_complete = True
            self.instant_data_ready.emit()

            # Schedule background completion
            self.background_timer.start(100)  # Complete remaining loading after 100ms

            return True

        except Exception as e:
            logger.error(f"Failed instant initialization: {e}")
            return False

    def populate_thumbnail_grid_instantly(
        self, grid_widget: QWidget, max_cards: int = 20
    ) -> int:
        """
        Populate thumbnail grid instantly with pre-loaded data.

        Args:
            grid_widget: The grid widget to populate
            max_cards: Maximum number of cards to create instantly

        Returns:
            int: Number of cards created
        """
        if not self.instant_initialization_complete:
            logger.warning("Instant initialization not complete")
            return 0

        start_time = time.time()
        cards_created = 0

        try:
            # Create cards for critical sequences only (first 20)
            critical_sequences = self.sequences[:max_cards]

            for sequence in critical_sequences:
                try:
                    # Create card with pre-loaded thumbnail
                    card = ModernThumbnailCard(sequence, parent=grid_widget)

                    # Set pre-loaded thumbnail if available
                    if sequence.id in self.critical_thumbnails:
                        thumbnail_path = self.critical_thumbnails[sequence.id]
                        card.set_preloaded_thumbnail(thumbnail_path)

                    self.thumbnail_cards.append(card)
                    cards_created += 1

                except Exception as e:
                    logger.debug(f"Failed to create card for {sequence.id}: {e}")
                    continue

            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Instant grid population: {cards_created} cards in {duration_ms:.1f}ms"
            )

            return cards_created

        except Exception as e:
            logger.error(f"Failed instant grid population: {e}")
            return 0

    def setup_instant_navigation(self, navigation_widget: QWidget) -> bool:
        """
        Setup navigation instantly with pre-computed data.

        Args:
            navigation_widget: The navigation sidebar widget

        Returns:
            bool: True if setup was successful
        """
        if not self.instant_initialization_complete:
            return False

        try:
            self.navigation_sidebar = navigation_widget

            # Use pre-computed navigation data
            if self.navigation_data:
                alphabetical_sections = self.navigation_data.get("alphabetical", {})

                # Setup navigation sections instantly
                for section_letter, sequence_ids in alphabetical_sections.items():
                    navigation_widget.add_section_instantly(
                        section_letter, len(sequence_ids)
                    )

            logger.debug(
                f"Instant navigation setup: {len(self.navigation_data.get('alphabetical', {}))} sections"
            )
            return True

        except Exception as e:
            logger.error(f"Failed instant navigation setup: {e}")
            return False

    def setup_instant_sequence_viewer(self, viewer_widget: QWidget) -> bool:
        """
        Setup sequence viewer instantly.

        Args:
            viewer_widget: The sequence viewer widget

        Returns:
            bool: True if setup was successful
        """
        if not self.instant_initialization_complete:
            return False

        try:
            self.sequence_viewer = viewer_widget

            # Pre-configure viewer for instant display
            viewer_widget.prepare_for_instant_display()

            logger.debug("Instant sequence viewer setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed instant sequence viewer setup: {e}")
            return False

    def get_instant_sequence_count(self) -> int:
        """Get the number of instantly available sequences."""
        return len(self.sequences) if self.instant_initialization_complete else 0

    def get_instant_thumbnail_count(self) -> int:
        """Get the number of instantly available thumbnails."""
        return (
            len(self.critical_thumbnails) if self.instant_initialization_complete else 0
        )

    def is_instant_ready(self) -> bool:
        """Check if instant data is ready for use."""
        return self.instant_initialization_complete

    def _complete_background_loading(self):
        """Complete any remaining background loading tasks."""
        try:
            logger.debug("Starting background loading completion...")

            # Load remaining sequences that weren't in critical set
            remaining_sequences = self.sequences[20:]  # Skip first 20 already loaded

            # Background thumbnail loading for remaining sequences
            for sequence in remaining_sequences:
                if sequence.thumbnails and sequence.id not in self.critical_thumbnails:
                    self.critical_thumbnails[sequence.id] = sequence.thumbnails[0]

            self.background_loading_complete_flag = True
            self.background_loading_complete.emit()

            logger.info(
                f"✅ Background loading completed: {len(self.sequences)} total sequences ready"
            )

        except Exception as e:
            logger.error(f"Background loading completion failed: {e}")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get optimization statistics for debugging.

        Returns:
            Dict[str, Any]: Statistics about optimization performance
        """
        if not self.optimized_data:
            return {"status": "not_optimized"}

        return {
            "status": "optimized",
            "instant_ready": self.instant_initialization_complete,
            "background_complete": self.background_loading_complete_flag,
            "total_sequences": len(self.sequences),
            "cached_thumbnails": len(self.critical_thumbnails),
            "navigation_sections": len(self.navigation_data.get("alphabetical", {})),
            "optimization_timestamp": self.optimized_data.get(
                "optimization_timestamp", 0
            ),
        }


# Global instance for singleton access
_instant_manager: Optional[InstantBrowseTabManager] = None


def get_instant_manager() -> InstantBrowseTabManager:
    """
    Get the global instant browse tab manager instance.

    Returns:
        InstantBrowseTabManager: The global manager instance
    """
    global _instant_manager

    if _instant_manager is None:
        _instant_manager = InstantBrowseTabManager()

    return _instant_manager


def initialize_instant_browse_tab() -> bool:
    """
    Initialize instant browse tab using pre-loaded data.

    Returns:
        bool: True if initialization was successful
    """
    manager = get_instant_manager()
    return manager.initialize_instantly()
