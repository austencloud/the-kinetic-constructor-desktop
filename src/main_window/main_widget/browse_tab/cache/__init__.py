"""
Browse Tab Cache Module

Provides efficient image caching for the browse tab to eliminate
redundant loading and improve performance.
"""

from .browse_image_cache import BrowseImageCache, get_browse_cache, clear_browse_cache

__all__ = ["BrowseImageCache", "get_browse_cache", "clear_browse_cache"]
