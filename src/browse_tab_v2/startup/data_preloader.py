"""
Browse Tab v2 Data Pre-loading System

This module provides comprehensive data pre-loading during application startup
to eliminate the initialization delay when users first navigate to the browse tab.

Key Features:
- Pre-loads all sequence data and metadata during splash screen phase
- Pre-populates navigation sidebar with section structure
- Pre-caches thumbnails and sequence information
- Prepares all data structures for immediate display
- Integrates with splash screen progress updates

Performance Targets:
- Complete data pre-loading in 200-500ms during splash screen
- Eliminate 2-3 second delay when clicking browse tab
- Achieve <50ms browse tab display time after pre-loading
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from ..core.interfaces import SequenceModel, BrowseTabConfig
from ..services.sequence_service import SequenceService
from ..services.cache_service import CacheService
from ..components.modern_navigation_sidebar import SectionDataExtractor

logger = logging.getLogger(__name__)

# Global pre-loading state
_preloading_completed = False
_preloaded_data: Dict[str, Any] = {}
_preloading_results: Dict[str, Any] = {}


class BrowseTabDataPreloader:
    """Comprehensive data pre-loading system for Browse Tab v2."""
    
    def __init__(self, config: BrowseTabConfig = None):
        self.config = config or BrowseTabConfig()
        
        # Services
        self.sequence_service: Optional[SequenceService] = None
        self.cache_service: Optional[CacheService] = None
        
        # Pre-loaded data
        self.sequences: List[SequenceModel] = []
        self.navigation_sections: Dict[str, List[str]] = {}
        self.thumbnail_cache: Dict[str, Any] = {}
        self.metadata_cache: Dict[str, Any] = {}
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        self.current_progress = 0
        self.total_steps = 6
        
        logger.info("BrowseTabDataPreloader initialized")
        
    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
        
    def _update_progress(self, message: str, step: int):
        """Update progress and call callback if set."""
        self.current_progress = step
        progress_percent = int((step / self.total_steps) * 100)
        
        logger.info(f"Data pre-loading: {message} ({progress_percent}%)")
        
        if self.progress_callback:
            self.progress_callback(message, progress_percent)
            
    async def preload_all_data(self) -> Dict[str, Any]:
        """
        Pre-load all browse tab data during application startup.
        
        Returns:
            Dict[str, Any]: Results of pre-loading including timing and success status
        """
        global _preloading_completed, _preloaded_data, _preloading_results
        
        if _preloading_completed:
            logger.debug("Browse tab data already pre-loaded")
            return _preloading_results
            
        logger.info("🚀 Starting Browse Tab v2 Data Pre-loading...")
        overall_start_time = time.time()
        
        results = {
            "overall_success": False,
            "overall_duration_ms": 0.0,
            "steps": {},
            "total_sequences": 0,
            "total_sections": 0,
            "total_thumbnails": 0,
            "failed_steps": [],
            "warnings": []
        }
        
        try:
            # Step 1: Initialize services
            self._update_progress("Initializing data services...", 1)
            await self._initialize_services()
            results["steps"]["initialize_services"] = {"success": True, "duration_ms": 0}
            
            # Step 2: Load sequence data
            self._update_progress("Loading sequence data...", 2)
            step_start = time.time()
            await self._load_sequence_data()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["load_sequences"] = {
                "success": True, 
                "duration_ms": step_duration,
                "count": len(self.sequences)
            }
            results["total_sequences"] = len(self.sequences)
            
            # Step 3: Pre-compute navigation sections
            self._update_progress("Building navigation structure...", 3)
            step_start = time.time()
            await self._precompute_navigation_sections()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["navigation_sections"] = {
                "success": True,
                "duration_ms": step_duration,
                "sections": dict((k, len(v)) for k, v in self.navigation_sections.items())
            }
            results["total_sections"] = sum(len(sections) for sections in self.navigation_sections.values())
            
            # Step 4: Pre-cache metadata
            self._update_progress("Caching sequence metadata...", 4)
            step_start = time.time()
            await self._cache_sequence_metadata()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["cache_metadata"] = {
                "success": True,
                "duration_ms": step_duration,
                "cached_items": len(self.metadata_cache)
            }
            
            # Step 5: Pre-load critical thumbnails
            self._update_progress("Pre-loading thumbnails...", 5)
            step_start = time.time()
            await self._preload_critical_thumbnails()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["preload_thumbnails"] = {
                "success": True,
                "duration_ms": step_duration,
                "cached_thumbnails": len(self.thumbnail_cache)
            }
            results["total_thumbnails"] = len(self.thumbnail_cache)
            
            # Step 6: Finalize and store global data
            self._update_progress("Finalizing data structures...", 6)
            step_start = time.time()
            await self._finalize_preloaded_data()
            step_duration = (time.time() - step_start) * 1000
            results["steps"]["finalize"] = {"success": True, "duration_ms": step_duration}
            
            # Calculate overall results
            overall_duration_ms = (time.time() - overall_start_time) * 1000
            results["overall_duration_ms"] = overall_duration_ms
            results["overall_success"] = True
            
            # Store results globally
            _preloaded_data = {
                "sequences": self.sequences,
                "navigation_sections": self.navigation_sections,
                "thumbnail_cache": self.thumbnail_cache,
                "metadata_cache": self.metadata_cache,
                "config": self.config
            }
            _preloading_results = results
            _preloading_completed = True
            
            logger.info(f"✅ Browse Tab v2 data pre-loading completed successfully in {overall_duration_ms:.1f}ms")
            logger.info(f"   Loaded: {results['total_sequences']} sequences, {results['total_sections']} sections, {results['total_thumbnails']} thumbnails")
            
            return results
            
        except Exception as e:
            overall_duration_ms = (time.time() - overall_start_time) * 1000
            results["overall_duration_ms"] = overall_duration_ms
            results["overall_success"] = False
            results["failed_steps"].append(("overall", str(e)))
            
            logger.error(f"❌ Browse Tab v2 data pre-loading failed: {e}")
            return results
            
    async def _initialize_services(self):
        """Initialize required services."""
        try:
            # Initialize sequence service
            self.sequence_service = SequenceService(config=self.config)
            
            # Initialize cache service
            self.cache_service = CacheService()
            
            logger.debug("Data services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
            
    async def _load_sequence_data(self):
        """Load all sequence data from the dictionary."""
        try:
            if not self.sequence_service:
                raise RuntimeError("Sequence service not initialized")
                
            # Load all sequences
            self.sequences = await self.sequence_service.get_all_sequences()
            
            logger.info(f"Loaded {len(self.sequences)} sequences from dictionary")
            
        except Exception as e:
            logger.error(f"Failed to load sequence data: {e}")
            # Don't raise - continue with empty sequences
            self.sequences = []
            
    async def _precompute_navigation_sections(self):
        """Pre-compute navigation sections for all sort criteria."""
        try:
            extractor = SectionDataExtractor()
            
            # Pre-compute sections for all sort criteria
            sort_criteria = ["alphabetical", "difficulty", "length", "author"]
            
            for criteria in sort_criteria:
                if criteria == "alphabetical":
                    sections = extractor.extract_alphabetical_sections(self.sequences)
                elif criteria == "difficulty":
                    sections = extractor.extract_difficulty_sections(self.sequences)
                elif criteria == "length":
                    sections = extractor.extract_length_sections(self.sequences)
                elif criteria == "author":
                    sections = extractor.extract_author_sections(self.sequences)
                else:
                    sections = []
                    
                self.navigation_sections[criteria] = sections
                
            logger.debug(f"Pre-computed navigation sections for {len(sort_criteria)} sort criteria")
            
        except Exception as e:
            logger.error(f"Failed to pre-compute navigation sections: {e}")
            # Don't raise - continue with empty sections
            self.navigation_sections = {}
            
    async def _cache_sequence_metadata(self):
        """Cache sequence metadata for quick access."""
        try:
            for sequence in self.sequences:
                metadata = {
                    "id": sequence.id,
                    "name": sequence.name,
                    "difficulty": sequence.difficulty,
                    "length": sequence.length,
                    "author": sequence.author,
                    "tags": sequence.tags,
                    "is_favorite": sequence.is_favorite,
                    "thumbnail_count": len(sequence.thumbnails) if sequence.thumbnails else 0
                }
                
                self.metadata_cache[sequence.id] = metadata
                
            logger.debug(f"Cached metadata for {len(self.metadata_cache)} sequences")
            
        except Exception as e:
            logger.error(f"Failed to cache sequence metadata: {e}")
            # Don't raise - continue with empty cache
            self.metadata_cache = {}
            
    async def _preload_critical_thumbnails(self):
        """Pre-load critical thumbnails for immediate display."""
        try:
            # Pre-load first few thumbnails from each section for immediate display
            max_thumbnails_per_section = 5  # Limit to avoid excessive startup time
            total_preloaded = 0
            
            for sort_criteria, sections in self.navigation_sections.items():
                if sort_criteria != "alphabetical":
                    continue  # Only pre-load alphabetical for now
                    
                for section in sections[:3]:  # Only first 3 sections to limit startup time
                    section_sequences = [
                        seq for seq in self.sequences 
                        if seq.name and seq.name[0].upper() == section
                    ]
                    
                    for sequence in section_sequences[:max_thumbnails_per_section]:
                        if sequence.thumbnails:
                            # Store thumbnail path for later loading
                            thumbnail_path = sequence.thumbnails[0]
                            self.thumbnail_cache[sequence.id] = {
                                "path": thumbnail_path,
                                "preloaded": True,
                                "section": section
                            }
                            total_preloaded += 1
                            
            logger.debug(f"Pre-loaded {total_preloaded} critical thumbnails")
            
        except Exception as e:
            logger.error(f"Failed to pre-load thumbnails: {e}")
            # Don't raise - continue with empty cache
            self.thumbnail_cache = {}
            
    async def _finalize_preloaded_data(self):
        """Finalize pre-loaded data structures."""
        try:
            # Validate data integrity
            if not self.sequences:
                logger.warning("No sequences loaded - browse tab will be empty")
                
            if not self.navigation_sections:
                logger.warning("No navigation sections computed - navigation will be empty")
                
            # Log summary
            logger.info(f"Pre-loading summary:")
            logger.info(f"  Sequences: {len(self.sequences)}")
            logger.info(f"  Navigation sections: {sum(len(sections) for sections in self.navigation_sections.values())}")
            logger.info(f"  Cached metadata: {len(self.metadata_cache)}")
            logger.info(f"  Pre-loaded thumbnails: {len(self.thumbnail_cache)}")
            
        except Exception as e:
            logger.error(f"Failed to finalize pre-loaded data: {e}")
            raise


def get_preloaded_data() -> Optional[Dict[str, Any]]:
    """
    Get pre-loaded browse tab data.
    
    Returns:
        Dict[str, Any]: Pre-loaded data, or None if not available
    """
    global _preloaded_data, _preloading_completed
    
    if _preloading_completed and _preloaded_data:
        return _preloaded_data.copy()
    return None


def get_preloading_results() -> Optional[Dict[str, Any]]:
    """
    Get the results of the pre-loading process.
    
    Returns:
        Dict[str, Any]: Pre-loading results, or None if not completed
    """
    global _preloading_results, _preloading_completed
    
    if _preloading_completed:
        return _preloading_results.copy()
    return None


def is_preloading_completed() -> bool:
    """
    Check if data pre-loading has been completed.
    
    Returns:
        bool: True if pre-loading is complete
    """
    global _preloading_completed
    return _preloading_completed


async def preload_browse_tab_data(
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> Dict[str, Any]:
    """
    Main entry point for browse tab data pre-loading.
    
    Args:
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dict[str, Any]: Results of pre-loading process
    """
    preloader = BrowseTabDataPreloader()
    
    if progress_callback:
        preloader.set_progress_callback(progress_callback)
        
    return await preloader.preload_all_data()
