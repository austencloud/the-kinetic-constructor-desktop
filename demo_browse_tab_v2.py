#!/usr/bin/env python3
"""
Standalone demonstration of Browse Tab v2 Foundation Architecture.

This script creates a complete working demonstration of the new browse tab
architecture, showcasing reactive state management, async operations,
and service coordination with real data.

Usage:
    python demo_browse_tab_v2.py

Features Demonstrated:
- Reactive state management with PyQt signals
- Async sequence loading and filtering
- Multi-layer caching system
- Performance monitoring
- Service coordination
- Modern MVVM architecture
"""

import sys
import asyncio
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockJsonManager:
    """Mock JSON manager that provides sample data for demonstration."""
    
    def __init__(self):
        self.dictionary_path = "mock_dictionary.json"
        self.loader_saver = self
    
    def load_json_file(self, path):
        """Return mock dictionary data."""
        return {
            "sequence_001": {
                "metadata": {
                    "difficulty": 3,
                    "length": 8,
                    "author": "Alice",
                    "tags": ["beginner", "flow"],
                    "is_favorite": False
                },
                "thumbnails": ["thumb_001.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}, {"beat": 4}]
            },
            "advanced_flow": {
                "metadata": {
                    "difficulty": 5,
                    "length": 12,
                    "author": "Bob",
                    "tags": ["advanced", "dynamic"],
                    "is_favorite": True
                },
                "thumbnails": ["thumb_002.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}, {"beat": 4}, {"beat": 5}]
            },
            "static_poses": {
                "metadata": {
                    "difficulty": 2,
                    "length": 6,
                    "author": "Charlie",
                    "tags": ["beginner", "static"],
                    "is_favorite": False
                },
                "thumbnails": ["thumb_003.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}]
            },
            "expert_combo": {
                "metadata": {
                    "difficulty": 5,
                    "length": 16,
                    "author": "Diana",
                    "tags": ["expert", "combo"],
                    "is_favorite": True
                },
                "thumbnails": ["thumb_004.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}, {"beat": 4}, {"beat": 5}, {"beat": 6}]
            },
            "flow_basics": {
                "metadata": {
                    "difficulty": 1,
                    "length": 4,
                    "author": "Eve",
                    "tags": ["beginner", "basics"],
                    "is_favorite": False
                },
                "thumbnails": ["thumb_005.png"],
                "beats": [{"beat": 1}, {"beat": 2}]
            },
            "intermediate_spin": {
                "metadata": {
                    "difficulty": 4,
                    "length": 10,
                    "author": "Frank",
                    "tags": ["intermediate", "spin"],
                    "is_favorite": False
                },
                "thumbnails": ["thumb_006.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}, {"beat": 4}]
            },
            "creative_expression": {
                "metadata": {
                    "difficulty": 3,
                    "length": 14,
                    "author": "Grace",
                    "tags": ["creative", "expression"],
                    "is_favorite": True
                },
                "thumbnails": ["thumb_007.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}, {"beat": 4}, {"beat": 5}]
            },
            "technical_precision": {
                "metadata": {
                    "difficulty": 5,
                    "length": 8,
                    "author": "Henry",
                    "tags": ["technical", "precision"],
                    "is_favorite": False
                },
                "thumbnails": ["thumb_008.png"],
                "beats": [{"beat": 1}, {"beat": 2}, {"beat": 3}, {"beat": 4}]
            }
        }


class MockSettingsManager:
    """Mock settings manager for demonstration."""
    
    def __init__(self):
        self.browse_settings = self
    
    def get_current_section(self):
        return "all"
    
    def get_current_filter(self):
        return ""
    
    def get_selected_sequence(self):
        return {}


class DemoMainWindow(QMainWindow):
    """Main window for the browse tab v2 demonstration."""
    
    def __init__(self):
        super().__init__()
        
        self.browse_tab_v2 = None
        self._setup_window()
        self._create_browse_tab()
        
        # Auto-initialize after a short delay
        QTimer.singleShot(500, self._initialize_browse_tab)
    
    def _setup_window(self):
        """Setup the main window."""
        self.setWindowTitle("Browse Tab v2 - Foundation Architecture Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set window icon if available
        try:
            icon_path = Path(__file__).parent / "assets" / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except:
            pass
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
    
    def _create_browse_tab(self):
        """Create the browse tab v2 instance."""
        try:
            from browse_tab_v2 import BrowseTabV2Factory
            from browse_tab_v2.core.interfaces import BrowseTabConfig
            
            # Create mock dependencies
            mock_json_manager = MockJsonManager()
            mock_settings_manager = MockSettingsManager()
            
            # Create configuration
            config = BrowseTabConfig(
                max_concurrent_image_loads=2,
                image_cache_size=50,
                enable_performance_monitoring=True,
                enable_debug_logging=True,
                default_columns=3
            )
            
            # Create browse tab v2
            self.browse_tab_v2 = BrowseTabV2Factory.create_with_config(
                config=config,
                json_manager=mock_json_manager,
                settings_manager=mock_settings_manager
            )
            
            # Get the view and add to layout
            view = self.browse_tab_v2.get_view()
            self.main_layout.addWidget(view)
            
            logger.info("Browse tab v2 created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create browse tab v2: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message
            from PyQt6.QtWidgets import QLabel
            error_label = QLabel(f"Error creating browse tab v2: {e}")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            self.main_layout.addWidget(error_label)
    
    def _initialize_browse_tab(self):
        """Initialize the browse tab asynchronously."""
        if self.browse_tab_v2:
            asyncio.create_task(self._async_initialize())
    
    async def _async_initialize(self):
        """Async initialization of browse tab."""
        try:
            logger.info("Initializing browse tab v2...")
            await self.browse_tab_v2.initialize()
            logger.info("Browse tab v2 initialized successfully")
            
            # Auto-load sequences for demonstration
            QTimer.singleShot(1000, lambda: asyncio.create_task(self._auto_load_sequences()))
            
        except Exception as e:
            logger.error(f"Failed to initialize browse tab v2: {e}")
            import traceback
            traceback.print_exc()
    
    async def _auto_load_sequences(self):
        """Auto-load sequences for demonstration."""
        try:
            logger.info("Auto-loading sequences for demonstration...")
            await self.browse_tab_v2.load_sequences()
            logger.info("Sequences loaded successfully")
        except Exception as e:
            logger.error(f"Failed to auto-load sequences: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            if self.browse_tab_v2:
                self.browse_tab_v2.cleanup()
            logger.info("Demo application closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        event.accept()


async def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Browse Tab v2 Demo")
    app.setApplicationVersion("2.0.0")
    
    # Apply modern styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
    """)
    
    # Create and show main window
    window = DemoMainWindow()
    window.show()
    
    logger.info("Browse Tab v2 Foundation Architecture Demo started")
    logger.info("=" * 60)
    logger.info("This demonstration showcases:")
    logger.info("✓ Reactive state management with PyQt signals")
    logger.info("✓ Async sequence loading and filtering")
    logger.info("✓ Multi-layer caching system")
    logger.info("✓ Performance monitoring")
    logger.info("✓ Service coordination")
    logger.info("✓ Modern MVVM architecture")
    logger.info("=" * 60)
    
    # Run the application
    try:
        app.exec()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Handle async main function
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed to start demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
