import logging
import os
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..image_processor import ImageProcessor


class CacheStatsManager:
    def __init__(self, image_processor: "ImageProcessor"):
        self.image_processor = image_processor
        self.cache_hits = 0
        self.cache_misses = 0
        self.using_cached_content = False
        self.logger = logging.getLogger(__name__)

    def reset_stats(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.using_cached_content = False

    def record_cache_hit(self):
        self.cache_hits += 1

    def record_cache_miss(self):
        self.cache_misses += 1

    def check_cache_availability(self, sequences: List[Dict[str, Any]]) -> float:
        if not sequences:
            return 0.0

        cached_count = 0
        total_count = 0

        sample_size = min(20, len(sequences))
        sample_step = max(1, len(sequences) // sample_size)

        for i in range(0, len(sequences), sample_step):
            if i >= len(sequences):
                break

            sequence_data = sequences[i]
            image_path = sequence_data.get("path", "")

            if image_path and os.path.exists(image_path):
                total_count += 1

                cached_image = (
                    self.image_processor.coordinator.cache_manager.get_raw_image(
                        image_path
                    )
                )
                if cached_image is not None:
                    cached_count += 1

        if total_count == 0:
            return 0.0

        cache_ratio = cached_count / total_count
        self.using_cached_content = cache_ratio > 0.8
        return cache_ratio

    def get_cache_hit_ratio(self) -> float:
        if self.cache_hits + self.cache_misses > 0:
            return self.cache_hits / (self.cache_hits + self.cache_misses)
        return 0.0

    def log_cache_performance(self, cached_count: int):
        if cached_count > 0:
            self.logger.info(f"Instantly displayed {cached_count} cached images")

        if self.cache_hits + self.cache_misses > 0:
            cache_ratio = self.get_cache_hit_ratio()
            self.logger.debug(f"Cache hit ratio: {cache_ratio:.2f}")
