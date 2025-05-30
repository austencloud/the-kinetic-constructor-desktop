#!/usr/bin/env python3
"""
Cache Management CLI for Sequence Card Tab

This utility provides command-line tools for managing and optimizing
the sequence card image cache system.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from .cache_optimizer import CacheOptimizer


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def find_cache_directory() -> Path:
    """Find the sequence card cache directory."""
    # Try common cache locations
    possible_paths = [
        Path.home() / "AppData" / "Local" / "sequence_card_cache",
        Path.home() / ".cache" / "sequence_card_cache",
        Path.cwd() / "cache" / "sequence_card_cache",
        Path("/tmp") / "sequence_card_cache",
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "cache_metadata.json").exists():
            return path
    
    # If not found, ask user to specify
    print("Cache directory not found automatically.")
    print("Please specify the cache directory path using --cache-dir option.")
    sys.exit(1)


def analyze_cache(cache_dir: Path, verbose: bool = False) -> Dict[str, Any]:
    """Analyze cache for redundancy and statistics."""
    print(f"🔍 Analyzing cache directory: {cache_dir}")
    
    optimizer = CacheOptimizer(cache_dir)
    
    # Get basic statistics
    stats = optimizer.get_cache_statistics()
    if "error" in stats:
        print(f"❌ Error getting cache statistics: {stats['error']}")
        return stats
    
    print(f"📊 Cache Statistics:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total size: {stats['total_size_mb']} MB")
    print(f"   Average file size: {stats['average_file_size_kb']} KB")
    
    if verbose and 'size_distribution' in stats:
        print(f"\n📏 Size Distribution:")
        for size, info in stats['size_distribution'].items():
            size_mb = info['total_size'] / (1024 * 1024)
            print(f"   {size}: {info['count']} files ({size_mb:.1f} MB)")
    
    # Analyze redundancy
    analysis = optimizer.analyze_cache_redundancy()
    if "error" in analysis:
        print(f"❌ Error analyzing redundancy: {analysis['error']}")
        return analysis
    
    print(f"\n🔍 Redundancy Analysis:")
    print(f"   Unique content signatures: {analysis['unique_content_signatures']}")
    print(f"   Redundant entries: {analysis['redundant_entries']}")
    print(f"   Potential savings: {analysis['redundant_size_mb']} MB ({analysis['potential_savings_percent']}%)")
    
    if verbose and analysis['duplicate_groups']:
        print(f"\n📋 Sample Duplicate Groups:")
        for i, group in enumerate(analysis['duplicate_groups'][:5]):
            print(f"   Group {i+1}: {group['total_entries']} entries, {group['redundant_entries']} redundant")
    
    return analysis


def optimize_cache(cache_dir: Path, dry_run: bool = True, verbose: bool = False) -> bool:
    """Optimize cache by removing redundant entries."""
    action = "Analyzing" if dry_run else "Optimizing"
    print(f"🛠️  {action} cache directory: {cache_dir}")
    
    optimizer = CacheOptimizer(cache_dir)
    result = optimizer.optimize_cache(dry_run=dry_run)
    
    if "error" in result:
        print(f"❌ Error during optimization: {result['error']}")
        return False
    
    if result['status'] == 'no_optimization_needed':
        print(f"✅ {result['message']}")
        return True
    
    if result['status'] == 'success':
        if dry_run:
            print(f"📊 Optimization Preview:")
            print(f"   Would remove: {result['removed_entries']} entries")
            print(f"   Would free: {result['freed_space_mb']} MB")
            print(f"   Would keep: {result['remaining_entries']} entries")
            print(f"\n💡 Run with --apply to actually perform the optimization")
        else:
            print(f"✅ Optimization completed successfully!")
            print(f"   Removed: {result['removed_entries']} entries")
            print(f"   Freed: {result['freed_space_mb']} MB")
            print(f"   Remaining: {result['remaining_entries']} entries")
        return True
    
    print(f"❌ Unexpected optimization result: {result}")
    return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage and optimize sequence card image cache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze                    # Analyze cache in default location
  %(prog)s analyze --verbose          # Detailed analysis with size distribution
  %(prog)s optimize                   # Preview optimization (dry run)
  %(prog)s optimize --apply           # Actually perform optimization
  %(prog)s --cache-dir /path/to/cache analyze  # Analyze specific cache directory
        """
    )
    
    parser.add_argument(
        'action',
        choices=['analyze', 'optimize'],
        help='Action to perform on the cache'
    )
    
    parser.add_argument(
        '--cache-dir',
        type=Path,
        help='Path to cache directory (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually perform optimization (default is dry run)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Find cache directory
    if args.cache_dir:
        cache_dir = args.cache_dir
        if not cache_dir.exists():
            print(f"❌ Cache directory does not exist: {cache_dir}")
            sys.exit(1)
    else:
        cache_dir = find_cache_directory()
    
    # Perform requested action
    if args.action == 'analyze':
        result = analyze_cache(cache_dir, args.verbose)
        success = "error" not in result
    elif args.action == 'optimize':
        success = optimize_cache(cache_dir, dry_run=not args.apply, verbose=args.verbose)
    else:
        print(f"❌ Unknown action: {args.action}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
