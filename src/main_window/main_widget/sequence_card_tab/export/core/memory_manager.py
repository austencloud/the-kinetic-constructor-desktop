"""
Memory Manager - Handles memory monitoring and cleanup operations.

This component extracts memory management logic from the main exporter
following the Single Responsibility Principle.
"""

import logging
import gc
import time
import psutil
from typing import Optional


class MemoryManager:
    """
    Handles memory monitoring and cleanup operations.
    
    Responsibilities:
    - Monitor current memory usage
    - Perform garbage collection when needed
    - Track memory usage patterns
    - Provide memory optimization strategies
    - Handle out-of-memory situations
    """
    
    def __init__(self, max_memory_mb: int = 2000, check_interval: int = 5):
        self.logger = logging.getLogger(__name__)
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        
        # Memory tracking
        self.stats = {
            "peak_memory_mb": 0.0,
            "cleanup_count": 0,
            "forced_cleanup_count": 0,
            "memory_warnings": 0,
            "last_cleanup_time": None,
            "monitoring_enabled": False
        }
        
        # Process reference
        self._process = None
        
        self.logger.info(f"MemoryManager initialized with {max_memory_mb}MB limit")
    
    def initialize_monitoring(self) -> bool:
        """Initialize memory monitoring."""
        try:
            self._process = psutil.Process()
            self.stats["monitoring_enabled"] = True
            self.logger.info("Memory monitoring initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize memory monitoring: {e}")
            return False
    
    def get_current_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Current memory usage in MB, or 0.0 if monitoring unavailable
        """
        if not self._process:
            return 0.0
        
        try:
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Update peak memory
            if memory_mb > self.stats["peak_memory_mb"]:
                self.stats["peak_memory_mb"] = memory_mb
            
            return memory_mb
        except Exception as e:
            self.logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
    
    def check_and_cleanup_if_needed(self, force_cleanup: bool = False) -> float:
        """
        Check memory usage and perform cleanup if necessary.
        
        Args:
            force_cleanup: Force cleanup regardless of memory usage
            
        Returns:
            Current memory usage after cleanup
        """
        current_memory = self.get_current_usage()
        
        # Check if cleanup is needed
        needs_cleanup = (
            force_cleanup or 
            current_memory > self.max_memory_mb or
            self._should_perform_preventive_cleanup()
        )
        
        if needs_cleanup:
            self._perform_cleanup(forced=force_cleanup)
            current_memory = self.get_current_usage()
            
            # Log memory warning if still high
            if current_memory > self.max_memory_mb:
                self.stats["memory_warnings"] += 1
                self.logger.warning(
                    f"Memory usage still high after cleanup: {current_memory:.1f}MB"
                )
        
        return current_memory
    
    def force_cleanup(self) -> float:
        """Force immediate memory cleanup."""
        return self.check_and_cleanup_if_needed(force_cleanup=True)
    
    def _should_perform_preventive_cleanup(self) -> bool:
        """Determine if preventive cleanup should be performed."""
        current_memory = self.get_current_usage()
        
        # Perform preventive cleanup at 80% of limit
        preventive_threshold = self.max_memory_mb * 0.8
        
        return current_memory > preventive_threshold
    
    def _perform_cleanup(self, forced: bool = False) -> None:
        """Perform memory cleanup operations."""
        self.logger.debug(f"Performing memory cleanup (forced: {forced})")
        
        # Record cleanup
        if forced:
            self.stats["forced_cleanup_count"] += 1
        else:
            self.stats["cleanup_count"] += 1
        
        self.stats["last_cleanup_time"] = time.time()
        
        # Perform garbage collection
        collected = gc.collect()
        
        # Add small delay to allow system to stabilize
        time.sleep(0.1)
        
        self.logger.debug(f"Garbage collection freed {collected} objects")
    
    def get_memory_info(self) -> dict:
        """
        Get detailed memory information.
        
        Returns:
            Dictionary with memory details
        """
        if not self._process:
            return {"error": "Memory monitoring not initialized"}
        
        try:
            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()
            
            return {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "percent": memory_percent,
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
                "total_mb": psutil.virtual_memory().total / (1024 * 1024)
            }
        except Exception as e:
            return {"error": f"Failed to get memory info: {e}"}
    
    def estimate_memory_for_image(self, width: int, height: int, channels: int = 4) -> float:
        """
        Estimate memory usage for an image.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            channels: Number of channels (default: 4 for RGBA)
            
        Returns:
            Estimated memory usage in MB
        """
        bytes_per_pixel = channels
        total_bytes = width * height * bytes_per_pixel
        memory_mb = total_bytes / (1024 * 1024)
        
        # Add overhead factor (typically 2-3x for processing)
        overhead_factor = 2.5
        estimated_mb = memory_mb * overhead_factor
        
        return estimated_mb
    
    def can_process_image(self, width: int, height: int, channels: int = 4) -> bool:
        """
        Check if an image can be processed without exceeding memory limits.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            channels: Number of channels
            
        Returns:
            True if image can be processed safely
        """
        current_memory = self.get_current_usage()
        estimated_memory = self.estimate_memory_for_image(width, height, channels)
        total_estimated = current_memory + estimated_memory
        
        # Use 90% of limit as safety margin
        safe_limit = self.max_memory_mb * 0.9
        
        can_process = total_estimated <= safe_limit
        
        if not can_process:
            self.logger.warning(
                f"Image too large for safe processing: "
                f"current={current_memory:.1f}MB, "
                f"estimated={estimated_memory:.1f}MB, "
                f"total={total_estimated:.1f}MB, "
                f"limit={safe_limit:.1f}MB"
            )
        
        return can_process
    
    def get_recommended_max_dimension(self, current_memory: Optional[float] = None) -> int:
        """
        Get recommended maximum image dimension based on available memory.
        
        Args:
            current_memory: Current memory usage (will be measured if None)
            
        Returns:
            Recommended maximum dimension in pixels
        """
        if current_memory is None:
            current_memory = self.get_current_usage()
        
        # Calculate available memory
        available_memory = max(0, self.max_memory_mb * 0.8 - current_memory)
        
        # Estimate maximum pixels (assuming RGBA and 2.5x overhead)
        bytes_per_pixel = 4 * 2.5
        max_pixels = (available_memory * 1024 * 1024) / bytes_per_pixel
        
        # Calculate square dimension
        max_dimension = int(max_pixels ** 0.5)
        
        # Apply reasonable bounds
        max_dimension = max(500, min(max_dimension, 4000))
        
        return max_dimension
    
    def final_cleanup(self) -> None:
        """Perform final cleanup operations."""
        self.logger.info("Performing final memory cleanup")
        self._perform_cleanup(forced=True)
        
        # Additional cleanup for final state
        gc.collect()
        gc.collect()  # Run twice for better cleanup
        
        final_memory = self.get_current_usage()
        self.logger.info(f"Final memory usage: {final_memory:.1f}MB")
    
    def get_stats(self) -> dict:
        """Get memory management statistics."""
        current_memory = self.get_current_usage()
        
        return {
            **self.stats,
            "current_memory_mb": current_memory,
            "memory_limit_mb": self.max_memory_mb,
            "memory_utilization_percent": (current_memory / self.max_memory_mb) * 100,
            "total_cleanup_count": self.stats["cleanup_count"] + self.stats["forced_cleanup_count"]
        }
