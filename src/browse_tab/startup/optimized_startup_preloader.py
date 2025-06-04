"""
Optimized Startup Preloader for Browse Tab v2

This module provides ultra-fast startup optimization by eliminating all visible
loading delays after splash screen completion. It focuses on:

1. Silent sequence discovery (no verbose logging)
2. Aggressive thumbnail pre-caching
3. Widget pre-initialization
4. Memory-optimized data structures
5. Instant UI population

Performance Targets:
- Zero visible loading states after splash screen
- <1 second total preloading time
- Browse tab fully interactive immediately
- No cache misses during initial display
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from ..core.interfaces import SequenceModel, BrowseTabConfig
from ..services.sequence_service import SequenceService
from ..services.cache_service import CacheService

logger = logging.getLogger(__name__)

# Global optimization state
_optimization_completed = False
_optimized_data: Dict[str, Any] = {}
_optimization_results: Dict[str, Any] = {}

# Persistent storage for cross-process optimization data
import tempfile
import json
from pathlib import Path

_OPTIMIZATION_CACHE_FILE = (
    Path(tempfile.gettempdir()) / "kinetic_constructor_optimization.json"
)


def _save_optimization_to_disk(optimized_data: Dict[str, Any], results: Dict[str, Any]):
    """Save optimization data to disk for cross-process access."""
    try:
        # Create a serializable version of the data
        disk_data = {
            "optimization_completed": True,
            "optimization_timestamp": optimized_data.get(
                "optimization_timestamp", time.time()
            ),
            "total_sequences": results.get("total_sequences", 0),
            "preloaded_thumbnails": results.get("preloaded_thumbnails", 0),
            "overall_duration_ms": results.get("overall_duration_ms", 0),
            "sequence_ids": [seq.id for seq in optimized_data.get("sequences", [])],
            "critical_thumbnails": optimized_data.get("critical_thumbnails", {}),
            "navigation_data": optimized_data.get("navigation_data", {}),
        }

        with open(_OPTIMIZATION_CACHE_FILE, "w") as f:
            json.dump(disk_data, f)

        logger.debug(f"Optimization data saved to {_OPTIMIZATION_CACHE_FILE}")
    except Exception as e:
        logger.warning(f"Failed to save optimization data to disk: {e}")


def _load_optimization_from_disk() -> Optional[Dict[str, Any]]:
    """Load optimization data from disk."""
    try:
        if not _OPTIMIZATION_CACHE_FILE.exists():
            return None

        with open(_OPTIMIZATION_CACHE_FILE, "r") as f:
            disk_data = json.load(f)

        # Check if data is recent (within last 10 minutes)
        timestamp = disk_data.get("optimization_timestamp", 0)
        if time.time() - timestamp > 600:  # 10 minutes
            logger.debug("Optimization cache expired")
            return None

        logger.debug(f"Loaded optimization data from {_OPTIMIZATION_CACHE_FILE}")
        return disk_data
    except Exception as e:
        logger.debug(f"Failed to load optimization data from disk: {e}")
        return None


class OptimizedStartupPreloader:
    """Ultra-fast startup preloader for instant browse tab display."""

    def __init__(self, silent_mode: bool = True):
        self.silent_mode = silent_mode
        self.config = BrowseTabConfig()

        # Services
        self.sequence_service: Optional[SequenceService] = None
        self.cache_service: Optional[CacheService] = None

        # Optimized data structures
        self.sequences: List[SequenceModel] = []
        self.critical_thumbnails: Dict[str, str] = {}  # sequence_id -> thumbnail_path
        self.navigation_data: Dict[str, Any] = {}

        # Progress tracking
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        self.current_progress = 0
        self.total_steps = 4  # Reduced from 6 for faster startup

        # Enhanced progress tracking for smooth UX
        self.detailed_progress_callback: Optional[Callable[[float, str], None]] = None

        if not self.silent_mode:
            logger.info("OptimizedStartupPreloader initialized")

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """Set progress callback for splash screen updates."""
        self.progress_callback = callback

    def set_detailed_progress_callback(self, callback: Callable[[float, str], None]):
        """Set detailed progress callback for smooth incremental updates."""
        self.detailed_progress_callback = callback

    def _update_progress(self, message: str, step: int):
        """Update progress with minimal overhead."""
        if self.progress_callback:
            progress_percent = int((step / self.total_steps) * 100)
            self.progress_callback(message, progress_percent)
        self.current_progress = step

    def _update_progress_incremental(
        self, message: str, step: int, sub_progress: float
    ):
        """Update progress with sub-step granularity for smooth UX."""
        if self.detailed_progress_callback:
            # Calculate overall progress including sub-step
            overall_progress = (step - 1 + sub_progress) / self.total_steps
            self.detailed_progress_callback(overall_progress, message)

        # Also update legacy callback for compatibility
        if self.progress_callback:
            progress_percent = int(((step - 1 + sub_progress) / self.total_steps) * 100)
            self.progress_callback(message, progress_percent)

    async def preload_for_instant_startup(self) -> Dict[str, Any]:
        """
        Ultra-fast preloading for instant startup experience.

        Returns:
            Dict[str, Any]: Results of optimization including timing and success status
        """
        global _optimization_completed, _optimized_data, _optimization_results

        if _optimization_completed:
            if not self.silent_mode:
                logger.debug("Startup optimization already completed")
            return _optimization_results

        if not self.silent_mode:
            logger.info("🚀 Starting optimized startup preloading...")

        overall_start_time = time.time()

        results = {
            "overall_success": False,
            "overall_duration_ms": 0.0,
            "steps": {},
            "total_sequences": 0,
            "preloaded_thumbnails": 0,
            "failed_steps": [],
            "optimization_level": "instant_startup",
        }

        try:
            # Step 1: Initialize services (silent)
            self._update_progress("Initializing...", 1)
            await self._initialize_services_silent()
            results["steps"]["initialize_services"] = {
                "success": True,
                "duration_ms": 0,
            }

            # Step 2: Fast sequence discovery (no logging)
            self._update_progress("Scanning sequences...", 2)
            step_start = time.time()
            await self._fast_sequence_discovery()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["sequence_discovery"] = {
                "success": True,
                "duration_ms": step_duration,
                "count": len(self.sequences),
            }
            results["total_sequences"] = len(self.sequences)

            # Step 3: Critical thumbnail pre-caching (with granular progress)
            self._update_progress("Caching thumbnails...", 3)
            step_start = time.time()
            await self._preload_critical_thumbnails_aggressive_with_progress()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["thumbnail_caching"] = {
                "success": True,
                "duration_ms": step_duration,
                "cached_count": len(self.critical_thumbnails),
            }
            results["preloaded_thumbnails"] = len(self.critical_thumbnails)

            # Step 4: Prepare instant navigation data
            self._update_progress("Finalizing...", 4)
            step_start = time.time()
            await self._prepare_instant_navigation()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["navigation_prep"] = {
                "success": True,
                "duration_ms": step_duration,
            }

            # Calculate overall results
            overall_duration_ms = (time.time() - overall_start_time) * 1000
            results["overall_duration_ms"] = overall_duration_ms
            results["overall_success"] = True

            # Store results globally for instant access
            _optimized_data = {
                "sequences": self.sequences,
                "critical_thumbnails": self.critical_thumbnails,
                "navigation_data": self.navigation_data,
                "config": self.config,
                "optimization_timestamp": time.time(),
            }
            _optimization_results = results
            _optimization_completed = True

            # Save to persistent storage for cross-process access
            _save_optimization_to_disk(_optimized_data, results)

            # Debug logging to confirm flag is set
            logger.info(
                f"🔍 OPTIMIZATION_COMPLETE: Flag set to {_optimization_completed}"
            )
            logger.info(
                f"🔍 OPTIMIZATION_COMPLETE: Data stored with {len(self.sequences)} sequences"
            )

            if not self.silent_mode:
                logger.info(
                    f"✅ Optimized startup completed in {overall_duration_ms:.1f}ms"
                )
                logger.info(
                    f"   Ready: {results['total_sequences']} sequences, {results['preloaded_thumbnails']} thumbnails"
                )

            return results

        except Exception as e:
            overall_duration_ms = (time.time() - overall_start_time) * 1000
            results["overall_duration_ms"] = overall_duration_ms
            results["overall_success"] = False
            results["failed_steps"].append(("overall", str(e)))

            if not self.silent_mode:
                logger.error(f"❌ Optimized startup failed: {e}")
            return results

    async def _initialize_services_silent(self):
        """Initialize services with minimal logging."""
        try:
            # Initialize sequence service with silent mode
            self.sequence_service = SequenceService(config=self.config)

            # Get or initialize cache service (use global instance for startup optimization)
            from ..services.cache_service import get_global_cache_service

            self.cache_service = get_global_cache_service()
            if self.cache_service is None:
                self.cache_service = CacheService()

        except Exception as e:
            if not self.silent_mode:
                logger.error(f"Failed to initialize services: {e}")
            raise

    async def _fast_sequence_discovery(self):
        """Fast sequence discovery without verbose logging."""
        try:
            if not self.sequence_service:
                raise RuntimeError("Sequence service not initialized")

            # Temporarily suppress sequence service logging
            sequence_logger = logging.getLogger(
                "src.browse_tab_v2.services.sequence_service"
            )
            original_level = sequence_logger.level
            sequence_logger.setLevel(logging.WARNING)

            try:
                # Load sequences with suppressed logging
                self.sequences = await self.sequence_service.get_all_sequences()
            finally:
                # Restore original logging level
                sequence_logger.setLevel(original_level)

            if not self.silent_mode:
                logger.info(f"Discovered {len(self.sequences)} sequences")

        except Exception as e:
            if not self.silent_mode:
                logger.error(f"Failed sequence discovery: {e}")
            self.sequences = []

    async def _preload_critical_thumbnails_aggressive_with_progress(self):
        """Aggressively preload critical thumbnails with granular progress updates."""
        try:
            # Step 3.1: Queue all images for background loading (0-30% of step 3)
            self._update_progress_incremental(
                "Queuing images for background loading...", 3, 0.1
            )

            logger.info(
                f"🚀 STARTUP_LOADING: Queuing ALL {len(self.sequences)} thumbnails for progressive background loading"
            )

            # Get or create image service for background loading
            try:
                from ..services.fast_image_service import get_image_service

                image_service = get_image_service()

                self._update_progress_incremental(
                    "Starting background image loader...", 3, 0.2
                )

                # Queue all images for background loading with priority
                all_thumbnail_paths = []
                total_sequences = len(self.sequences)

                for i, sequence in enumerate(self.sequences):
                    if sequence.thumbnails:
                        thumbnail_path = sequence.thumbnails[0]
                        all_thumbnail_paths.append(thumbnail_path)

                        # Use priority based on position (earlier = higher priority)
                        priority = min(1 + (i // 50), 5)  # Priority 1-5, groups of 50
                        image_service.queue_image_load(
                            thumbnail_path, priority=priority
                        )

                    # Update progress every 50 sequences
                    if i % 50 == 0 and total_sequences > 0:
                        queue_progress = (
                            0.2 + (i / total_sequences) * 0.1
                        )  # 20-30% of step 3
                        self._update_progress_incremental(
                            f"Queuing images... ({i}/{total_sequences})",
                            3,
                            queue_progress,
                        )

                self._update_progress_incremental(
                    "All images queued for background loading", 3, 0.3
                )
                logger.info(
                    f"✅ STARTUP_LOADING: Queued {len(all_thumbnail_paths)} images for progressive background loading"
                )

            except Exception as e:
                logger.warning(f"Failed to queue images for background loading: {e}")

            # Step 3.2: Pre-cache critical thumbnails (30-100% of step 3)
            critical_sequences = self.sequences[:50]  # Increased from 20 to 50

            self._update_progress_incremental(
                f"Pre-loading {len(critical_sequences)} critical thumbnails...", 3, 0.35
            )

            logger.info(
                f"🚀 INSTANT_THUMBNAILS: Pre-loading {len(critical_sequences)} critical thumbnails for instant display"
            )

            for i, sequence in enumerate(critical_sequences):
                if sequence.thumbnails:
                    thumbnail_path = sequence.thumbnails[0]
                    self.critical_thumbnails[sequence.id] = thumbnail_path

                    # Pre-cache the thumbnail in memory instantly with multiple sizes
                    if self.cache_service:
                        try:
                            # Load and cache thumbnail immediately
                            from PyQt6.QtGui import QPixmap
                            from PyQt6.QtCore import Qt

                            pixmap = QPixmap(thumbnail_path)
                            if not pixmap.isNull():
                                # Cache multiple sizes for different display contexts
                                sizes = [
                                    (260, 220),  # Standard thumbnail size
                                    (280, 240),  # Slightly larger for hover effects
                                    (300, 260),  # Large thumbnail size
                                ]

                                for width, height in sizes:
                                    scaled_pixmap = pixmap.scaled(
                                        width,
                                        height,
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation,
                                    )

                                    # Use synchronous cache method for instant availability
                                    if hasattr(self.cache_service, "cache_image_sync"):
                                        self.cache_service.cache_image_sync(
                                            thumbnail_path,
                                            scaled_pixmap,
                                            (width, height),
                                        )
                                    elif hasattr(
                                        self.cache_service, "cache_image_instant"
                                    ):
                                        self.cache_service.cache_image_instant(
                                            thumbnail_path,
                                            scaled_pixmap,
                                            (width, height),
                                        )

                                logger.debug(
                                    f"🚀 INSTANT_THUMBNAILS: Pre-cached {sequence.id} in {len(sizes)} sizes"
                                )
                        except Exception as e:
                            logger.debug(
                                f"Failed to pre-cache thumbnail for {sequence.id}: {e}"
                            )

                # Update progress every 5 thumbnails for smooth UX
                if i % 5 == 0 and len(critical_sequences) > 0:
                    cache_progress = (
                        0.35 + (i / len(critical_sequences)) * 0.65
                    )  # 35-100% of step 3
                    self._update_progress_incremental(
                        f"Caching thumbnails... ({i+1}/{len(critical_sequences)})",
                        3,
                        cache_progress,
                    )

            logger.info(
                f"✅ INSTANT_THUMBNAILS: Pre-loaded {len(self.critical_thumbnails)} thumbnails for instant display"
            )

            if not self.silent_mode:
                logger.debug(
                    f"Pre-cached {len(self.critical_thumbnails)} critical thumbnails"
                )

        except Exception as e:
            if not self.silent_mode:
                logger.error(f"Failed to preload thumbnails: {e}")
            self.critical_thumbnails = {}

    async def _preload_critical_thumbnails_aggressive(self):
        """Legacy method - redirects to enhanced version."""
        await self._preload_critical_thumbnails_aggressive_with_progress()

    async def _prepare_instant_navigation(self):
        """Prepare navigation data for instant display."""
        try:
            # Pre-compute navigation sections for instant access
            alphabetical_sections = {}

            for sequence in self.sequences:
                if sequence.name:
                    first_letter = sequence.name[0].upper()
                    if first_letter not in alphabetical_sections:
                        alphabetical_sections[first_letter] = []
                    alphabetical_sections[first_letter].append(sequence.id)

            self.navigation_data = {
                "alphabetical": alphabetical_sections,
                "total_sequences": len(self.sequences),
                "sections_count": len(alphabetical_sections),
            }

        except Exception as e:
            if not self.silent_mode:
                logger.error(f"Failed to prepare navigation: {e}")
            self.navigation_data = {}


def get_optimized_data() -> Optional[Dict[str, Any]]:
    """
    Get pre-loaded optimized data for instant startup.

    Returns:
        Dict[str, Any]: Pre-loaded data if available, None otherwise
    """
    global _optimized_data, _optimization_completed

    # Check in-memory first
    if _optimization_completed and _optimized_data:
        logger.debug("🔍 GET_OPTIMIZED_DATA: Returning in-memory data")
        return _optimized_data.copy()

    # Check persistent storage
    disk_data = _load_optimization_from_disk()
    if disk_data and disk_data.get("optimization_completed", False):
        logger.debug("🔍 GET_OPTIMIZED_DATA: Found disk data, reconstructing sequences")

        # CRITICAL FIX: Reconstruct sequences from disk data
        sequences = []
        sequence_ids = disk_data.get("sequence_ids", [])

        if sequence_ids:
            logger.debug(
                f"🔍 GET_OPTIMIZED_DATA: Reconstructing {len(sequence_ids)} sequences from disk"
            )

            # Try to reconstruct sequences using sequence service
            try:
                from ..services.sequence_service import SequenceService
                from ..core.interfaces import BrowseTabConfig

                config = BrowseTabConfig()
                sequence_service = SequenceService(config=config)

                # Use synchronous approach to get sequences without async complications
                try:
                    # Try to get cached sequences first
                    if (
                        hasattr(sequence_service, "_sequences_cache")
                        and sequence_service._sequences_cache
                    ):
                        all_sequences = sequence_service._sequences_cache
                        # Filter to only the sequences we have IDs for
                        sequences = [
                            seq for seq in all_sequences if seq.id in sequence_ids
                        ]
                        logger.debug(
                            f"🔍 GET_OPTIMIZED_DATA: Reconstructed {len(sequences)} sequences from cache"
                        )
                    else:
                        # Try to load sequences synchronously using the fallback method
                        logger.debug(
                            "🔍 GET_OPTIMIZED_DATA: No cache, attempting synchronous load"
                        )
                        try:
                            # Use the synchronous loading method from the sequence service
                            from utils.path_helpers import get_data_path
                            import os

                            dictionary_path = get_data_path("dictionary")
                            if os.path.exists(dictionary_path):
                                # Load a subset of sequences for instant display
                                word_dirs = [
                                    d
                                    for d in os.listdir(dictionary_path)
                                    if os.path.isdir(os.path.join(dictionary_path, d))
                                ][
                                    :50
                                ]  # Limit for performance

                                for word_dir in word_dirs:
                                    word_path = os.path.join(dictionary_path, word_dir)
                                    try:
                                        # Use the synchronous method that exists
                                        sequence = sequence_service._create_sequence_from_directory(
                                            word_path
                                        )
                                        if sequence and sequence.id in sequence_ids:
                                            sequences.append(sequence)
                                    except AttributeError as attr_error:
                                        logger.warning(
                                            f"🔍 GET_OPTIMIZED_DATA: Method not found: {attr_error}"
                                        )
                                        # Try alternative approach - create sequence manually
                                        try:
                                            thumbnails = (
                                                sequence_service._find_thumbnails(
                                                    word_path
                                                )
                                            )
                                            if thumbnails:
                                                sequence = sequence_service._create_sequence_model_from_directory_sync(
                                                    word_dir, word_path, thumbnails
                                                )
                                                if (
                                                    sequence
                                                    and sequence.id in sequence_ids
                                                ):
                                                    sequences.append(sequence)
                                        except Exception as fallback_error:
                                            logger.warning(
                                                f"🔍 GET_OPTIMIZED_DATA: Fallback failed: {fallback_error}"
                                            )

                                logger.debug(
                                    f"🔍 GET_OPTIMIZED_DATA: Loaded {len(sequences)} sequences synchronously"
                                )
                            else:
                                logger.warning(
                                    "🔍 GET_OPTIMIZED_DATA: Dictionary path not found"
                                )

                        except Exception as load_error:
                            logger.warning(
                                f"🔍 GET_OPTIMIZED_DATA: Synchronous load failed: {load_error}"
                            )

                except Exception as e:
                    logger.warning(
                        f"🔍 GET_OPTIMIZED_DATA: Failed to reconstruct sequences: {e}"
                    )

            except Exception as e:
                logger.warning(
                    f"🔍 GET_OPTIMIZED_DATA: Failed to initialize sequence service: {e}"
                )

        # Convert disk data back to expected format with reconstructed sequences
        return {
            "sequences": sequences,  # Now properly reconstructed
            "critical_thumbnails": disk_data.get("critical_thumbnails", {}),
            "navigation_data": disk_data.get("navigation_data", {}),
            "optimization_timestamp": disk_data.get("optimization_timestamp", 0),
            "total_sequences": len(sequences),  # Use actual count
            "preloaded_thumbnails": disk_data.get("preloaded_thumbnails", 0),
        }

    logger.debug("🔍 GET_OPTIMIZED_DATA: No data available")
    return None


def is_optimization_completed() -> bool:
    """
    Check if startup optimization has been completed.

    Returns:
        bool: True if optimization is complete
    """
    global _optimization_completed

    # Check in-memory first
    if _optimization_completed:
        logger.debug("🔍 OPTIMIZATION_FLAG_CHECK: In-memory flag is True")
        return True

    # Check persistent storage
    disk_data = _load_optimization_from_disk()
    if disk_data and disk_data.get("optimization_completed", False):
        logger.debug("🔍 OPTIMIZATION_FLAG_CHECK: Found completed optimization on disk")
        return True

    logger.debug("🔍 OPTIMIZATION_FLAG_CHECK: No optimization found")
    return False


def clear_optimization_cache():
    """Clear optimization cache for testing purposes."""
    global _optimization_completed, _optimized_data, _optimization_results
    _optimization_completed = False
    _optimized_data = {}
    _optimization_results = {}

    # Also remove persistent file
    try:
        if _OPTIMIZATION_CACHE_FILE.exists():
            _OPTIMIZATION_CACHE_FILE.unlink()
            logger.debug("Cleared persistent optimization cache")
    except Exception as e:
        logger.debug(f"Failed to clear persistent cache: {e}")
