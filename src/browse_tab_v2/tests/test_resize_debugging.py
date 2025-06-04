"""
Comprehensive resize event debugging script for BrowseTabV2.

This script runs the application with enhanced logging to identify the exact
source of unwanted thumbnail resize events during scroll operations.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.WARNING,  # Set to WARNING to capture our detailed logs
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'resize_debug_{int(time.time())}.log')
    ]
)

# Set specific loggers to capture detailed events
loggers_to_monitor = [
    'browse_tab_v2.components.modern_thumbnail_card',
    'browse_tab_v2.components.responsive_thumbnail_grid',
    'browse_tab_v2.components.chunked_image_loader',
    'browse_tab_v2.browse_tab_view',
    'browse_tab_v2.browse_tab_adapter'
]

for logger_name in loggers_to_monitor:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)

# Create main logger
logger = logging.getLogger(__name__)


class ResizeEventTracker:
    """Track and analyze resize events across the application."""
    
    def __init__(self):
        self.resize_events = []
        self.scroll_events = []
        self.render_events = []
        self.start_time = time.time()
    
    def log_resize_event(self, component, old_size, new_size, source, timestamp):
        """Log a resize event for analysis."""
        event = {
            'timestamp': timestamp,
            'relative_time': timestamp - self.start_time,
            'component': component,
            'old_size': old_size,
            'new_size': new_size,
            'source': source,
            'size_change': (new_size[0] - old_size[0], new_size[1] - old_size[1])
        }
        self.resize_events.append(event)
        
        logger.warning(
            f"📊 RESIZE TRACKED: {component} "
            f"{old_size[0]}x{old_size[1]} → {new_size[0]}x{new_size[1]} "
            f"({source}) at +{event['relative_time']:.3f}s"
        )
    
    def log_scroll_event(self, position, viewport_range, timestamp):
        """Log a scroll event for analysis."""
        event = {
            'timestamp': timestamp,
            'relative_time': timestamp - self.start_time,
            'position': position,
            'viewport_range': viewport_range
        }
        self.scroll_events.append(event)
        
        logger.warning(
            f"📜 SCROLL TRACKED: pos={position} "
            f"viewport=[{viewport_range[0]}, {viewport_range[1]}] "
            f"at +{event['relative_time']:.3f}s"
        )
    
    def log_render_event(self, item_count, viewport_range, timestamp):
        """Log a render event for analysis."""
        event = {
            'timestamp': timestamp,
            'relative_time': timestamp - self.start_time,
            'item_count': item_count,
            'viewport_range': viewport_range
        }
        self.render_events.append(event)
        
        logger.warning(
            f"🎨 RENDER TRACKED: {item_count} items "
            f"viewport=[{viewport_range[0]}, {viewport_range[1]}] "
            f"at +{event['relative_time']:.3f}s"
        )
    
    def analyze_events(self):
        """Analyze collected events to identify patterns."""
        logger.warning("=" * 80)
        logger.warning("📊 RESIZE EVENT ANALYSIS")
        logger.warning("=" * 80)
        
        # Group resize events by component
        component_resizes = {}
        for event in self.resize_events:
            comp = event['component']
            if comp not in component_resizes:
                component_resizes[comp] = []
            component_resizes[comp].append(event)
        
        for component, events in component_resizes.items():
            logger.warning(f"\n🔍 {component}: {len(events)} resize events")
            for event in events[-5:]:  # Show last 5 events
                logger.warning(
                    f"   {event['old_size']} → {event['new_size']} "
                    f"({event['source']}) at +{event['relative_time']:.3f}s"
                )
        
        # Correlate scroll and resize events
        logger.warning("\n🔗 SCROLL-RESIZE CORRELATION")
        for scroll_event in self.scroll_events[-10:]:  # Last 10 scroll events
            # Find resize events within 100ms of this scroll
            related_resizes = [
                r for r in self.resize_events
                if abs(r['timestamp'] - scroll_event['timestamp']) < 0.1
            ]
            
            if related_resizes:
                logger.warning(
                    f"   Scroll at +{scroll_event['relative_time']:.3f}s "
                    f"→ {len(related_resizes)} resizes within 100ms"
                )
                for resize in related_resizes:
                    logger.warning(
                        f"     {resize['component']}: {resize['old_size']} → {resize['new_size']}"
                    )
        
        logger.warning("=" * 80)


# Global tracker instance
resize_tracker = ResizeEventTracker()


def run_debug_session():
    """Run the application with comprehensive resize debugging."""
    logger.warning("🚀 STARTING RESIZE DEBUG SESSION")
    logger.warning(f"📝 Logging to: resize_debug_{int(resize_tracker.start_time)}.log")
    
    try:
        # Import and run the main application
        from src.main import main
        
        logger.warning("🎯 LAUNCHING APPLICATION WITH RESIZE MONITORING")
        logger.warning("📋 INSTRUCTIONS:")
        logger.warning("   1. Wait for application to fully load")
        logger.warning("   2. Navigate to Browse tab")
        logger.warning("   3. Scroll slowly through the grid")
        logger.warning("   4. Scroll rapidly to trigger multiple events")
        logger.warning("   5. Close application to see analysis")
        
        # Run the application
        main()
        
    except KeyboardInterrupt:
        logger.warning("⏹️ DEBUG SESSION INTERRUPTED BY USER")
    except Exception as e:
        logger.error(f"❌ DEBUG SESSION FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Analyze collected events
        resize_tracker.analyze_events()
        
        logger.warning("🏁 RESIZE DEBUG SESSION COMPLETED")
        logger.warning(f"📊 Total Events Collected:")
        logger.warning(f"   Resize Events: {len(resize_tracker.resize_events)}")
        logger.warning(f"   Scroll Events: {len(resize_tracker.scroll_events)}")
        logger.warning(f"   Render Events: {len(resize_tracker.render_events)}")


if __name__ == "__main__":
    run_debug_session()
