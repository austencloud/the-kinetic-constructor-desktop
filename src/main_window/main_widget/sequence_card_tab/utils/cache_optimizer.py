"""
Cache optimization utilities for the sequence card tab.

This module provides utilities to optimize cache performance by:
1. Migrating from path-based to content-based cache keys
2. Analyzing cache efficiency and redundancy
3. Providing cache cleanup and optimization tools
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from PyQt6.QtCore import QSize


class CacheOptimizer:
    """
    Utility class for optimizing sequence card image caches.
    
    This class helps transition from path-based cache keys to content-based
    cache keys, reducing redundant storage and improving cache hit rates.
    """
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
    def analyze_cache_redundancy(self) -> Dict[str, any]:
        """
        Analyze the current cache for redundant entries.
        
        Returns:
            Dictionary with analysis results including:
            - total_entries: Total number of cache entries
            - redundant_entries: Number of redundant entries found
            - potential_savings_mb: Potential storage savings in MB
            - duplicate_groups: Groups of duplicate images
        """
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            if not metadata_file.exists():
                return {"error": "Cache metadata not found"}
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Group entries by content signature
            content_groups = {}
            total_size = 0
            
            for cache_key, entry in metadata.items():
                source_path = entry.get('source_path', '')
                file_size = entry.get('file_size', 0)
                target_width = entry.get('target_width', 0)
                target_height = entry.get('target_height', 0)
                scale_factor = entry.get('scale_factor', 1.0)
                
                # Create content signature
                content_id = self._create_content_signature(source_path)
                size_key = f"{target_width}x{target_height}_{scale_factor:.4f}"
                signature = f"{content_id}_{size_key}"
                
                if signature not in content_groups:
                    content_groups[signature] = []
                
                content_groups[signature].append({
                    'cache_key': cache_key,
                    'source_path': source_path,
                    'file_size': file_size,
                    'target_size': f"{target_width}x{target_height}",
                    'scale_factor': scale_factor
                })
                
                total_size += file_size
            
            # Find redundant entries
            redundant_entries = 0
            redundant_size = 0
            duplicate_groups = []
            
            for signature, entries in content_groups.items():
                if len(entries) > 1:
                    # Keep the most recently accessed entry, mark others as redundant
                    entries.sort(key=lambda x: metadata.get(x['cache_key'], {}).get('last_access', 0), reverse=True)
                    
                    redundant_in_group = entries[1:]  # All except the most recent
                    redundant_entries += len(redundant_in_group)
                    redundant_size += sum(entry['file_size'] for entry in redundant_in_group)
                    
                    duplicate_groups.append({
                        'signature': signature,
                        'total_entries': len(entries),
                        'redundant_entries': len(redundant_in_group),
                        'entries': entries
                    })
            
            return {
                'total_entries': len(metadata),
                'unique_content_signatures': len(content_groups),
                'redundant_entries': redundant_entries,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'redundant_size_mb': round(redundant_size / (1024 * 1024), 2),
                'potential_savings_percent': round((redundant_size / total_size) * 100, 1) if total_size > 0 else 0,
                'duplicate_groups': duplicate_groups[:10]  # Show first 10 groups
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cache redundancy: {e}")
            return {"error": str(e)}
    
    def optimize_cache(self, dry_run: bool = True) -> Dict[str, any]:
        """
        Optimize the cache by removing redundant entries.
        
        Args:
            dry_run: If True, only analyze what would be removed without actually removing
            
        Returns:
            Dictionary with optimization results
        """
        try:
            analysis = self.analyze_cache_redundancy()
            if "error" in analysis:
                return analysis
            
            if analysis['redundant_entries'] == 0:
                return {
                    'status': 'no_optimization_needed',
                    'message': 'Cache is already optimized - no redundant entries found'
                }
            
            removed_entries = 0
            freed_space_mb = 0
            
            if not dry_run:
                metadata_file = self.cache_dir / "cache_metadata.json"
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Remove redundant cache files and metadata entries
                for group in analysis['duplicate_groups']:
                    entries = group['entries'][1:]  # Skip the most recent entry
                    
                    for entry in entries:
                        cache_key = entry['cache_key']
                        cache_file = self.cache_dir / f"{cache_key}.png"
                        
                        # Remove cache file
                        if cache_file.exists():
                            cache_file.unlink()
                            freed_space_mb += entry['file_size'] / (1024 * 1024)
                            removed_entries += 1
                        
                        # Remove metadata entry
                        if cache_key in metadata:
                            del metadata[cache_key]
                
                # Save updated metadata
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return {
                'status': 'success',
                'dry_run': dry_run,
                'removed_entries': removed_entries if not dry_run else analysis['redundant_entries'],
                'freed_space_mb': round(freed_space_mb if not dry_run else analysis['redundant_size_mb'], 2),
                'remaining_entries': analysis['total_entries'] - (removed_entries if not dry_run else analysis['redundant_entries'])
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing cache: {e}")
            return {"error": str(e)}
    
    def _create_content_signature(self, image_path: str) -> str:
        """
        Create a content-based signature for an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Content signature string
        """
        try:
            if os.path.exists(image_path):
                stat = os.stat(image_path)
                file_size = stat.st_size
                mtime = stat.st_mtime
                filename = os.path.basename(image_path)
                content_data = f"{filename}_{file_size}_{mtime}"
            else:
                # File doesn't exist, use path as fallback
                content_data = image_path
            
            return hashlib.md5(content_data.encode()).hexdigest()[:12]
            
        except OSError:
            # Fallback to path-based hash
            return hashlib.md5(image_path.encode()).hexdigest()[:12]
    
    def get_cache_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            if not metadata_file.exists():
                return {"error": "Cache metadata not found"}
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            total_size = sum(entry.get('file_size', 0) for entry in metadata.values())
            
            # Analyze by image dimensions
            size_distribution = {}
            for entry in metadata.values():
                width = entry.get('target_width', 0)
                height = entry.get('target_height', 0)
                size_key = f"{width}x{height}"
                
                if size_key not in size_distribution:
                    size_distribution[size_key] = {'count': 0, 'total_size': 0}
                
                size_distribution[size_key]['count'] += 1
                size_distribution[size_key]['total_size'] += entry.get('file_size', 0)
            
            return {
                'total_entries': len(metadata),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir),
                'size_distribution': size_distribution,
                'average_file_size_kb': round((total_size / len(metadata)) / 1024, 2) if metadata else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {e}")
            return {"error": str(e)}
