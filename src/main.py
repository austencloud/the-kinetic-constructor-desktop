import sys
import os
import logging


def configure_import_paths():
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
        src_dir = os.path.join(base_dir, "src")
        if os.path.exists(src_dir) and src_dir not in sys.path:
            sys.path.insert(0, src_dir)
    else:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)


def initialize_logging():
    from src.utils.logging_config import configure_logging

    # Configure the logging system with INFO level by default
    configure_logging(logging.INFO)


def initialize_application():
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")
    return app


def initialize_dependency_injection():
    """Initialize the modern dependency injection system.

    This replaces the old AppContext singleton with proper dependency injection.
    """
    try:
        from src.core.dependency_container import configure_dependencies
        from src.core.application_context import create_application_context
        from src.core.migration_adapters import setup_legacy_compatibility
        from src.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Initializing dependency injection container...")

        # Configure the dependency injection container
        container = configure_dependencies()

        # Create application context with the container
        app_context = create_application_context(container)

        # CRITICAL: Set up legacy compatibility IMMEDIATELY after creating app_context
        # This must happen before any services are resolved to avoid circular dependency
        logger.info("Setting up legacy compatibility immediately...")
        setup_legacy_compatibility(app_context)
        logger.info("Legacy compatibility established during initialization")

        logger.info("Dependency injection system initialized successfully")
        return app_context

    except ImportError as e:
        from src.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error initializing dependency injection: {e}")
        raise


def initialize_legacy_appcontext(app_context):
    """Initialize the legacy AppContext singleton with services from dependency injection.

    This bridges the gap between the new DI system and legacy code that still uses AppContext.
    """
    try:
        from src.settings_manager.global_settings.app_context import AppContext
        from src.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Initializing legacy AppContext singleton...")

        # Get services from the new dependency injection system
        settings_manager = app_context.settings_manager
        json_manager = app_context.json_manager

        # Create special placement handler and loader directly
        # (Skip the fancy interface checking since those don't exist yet)
        logger.info("Creating special placement services...")

        try:
            from main_window.main_widget.json_manager.special_placement_saver import (
                SpecialPlacementSaver,
            )

            special_placement_handler = SpecialPlacementSaver()
            logger.info("Created SpecialPlacementSaver successfully")
        except ImportError as e:
            logger.warning(f"Could not import SpecialPlacementSaver: {e}")
            special_placement_handler = None

        try:
            from main_window.main_widget.special_placement_loader import (
                SpecialPlacementLoader,
            )

            special_placement_loader = SpecialPlacementLoader()
            logger.info("Created SpecialPlacementLoader successfully")
        except ImportError as e:
            logger.warning(f"Could not import SpecialPlacementLoader: {e}")
            special_placement_loader = None

        # Initialize the legacy AppContext
        AppContext.init(
            settings_manager=settings_manager,
            json_manager=json_manager,
            special_placement_handler=special_placement_handler,
            special_placement_loader=special_placement_loader,
        )

        logger.info("Legacy AppContext singleton initialized successfully")

    except Exception as e:
        from src.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.error(f"Failed to initialize legacy AppContext: {e}")
        logger.error("This will cause issues with widgets that still use AppContext")
        # Don't raise - let the app continue, some things might still work


def create_main_window(profiler, splash_screen, app_context):
    """Create the main window with dependency injection.

    This function creates the MainWindow using the new dependency injection system.
    """
    try:
        from src.main_window.main_window import MainWindow
        from src.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Creating MainWindow with dependency injection...")

        # Create the main window with dependency injection
        main_window = MainWindow(profiler, splash_screen, app_context)

        logger.info("MainWindow created successfully")
        return main_window

    except ImportError as e:
        from src.utils.logging_config import get_logger

        logger = get_logger(__name__)
        logger.error(f"Error importing in create_main_window: {e}")
        raise


def install_handlers():
    from src.utils.paint_event_supressor import PaintEventSuppressor

    # Only install the paint event suppressor, no more call tracing
    PaintEventSuppressor.install_message_handler()


def main():
    configure_import_paths()

    from PyQt6.QtCore import QTimer
    from src.splash_screen.splash_screen import SplashScreen
    from src.profiler import Profiler
    from src.settings_manager.settings_manager import SettingsManager
    from src.utils.logging_config import get_logger
    from src.utils.startup_silencer import silence_startup_logs

    # Get a logger for the main module
    logger = get_logger(__name__)

    # Log minimal startup information
    logger.info(f"Kinetic Constructor v1.0.0")
    logger.info(f"Python {sys.version.split()[0]}")

    # Use the startup silencer to reduce noise during initialization
    with silence_startup_logs():
        pass

    # Initialize logging without creating log files
    initialize_logging()

    app = initialize_application()

    settings_manager = SettingsManager()

    # Restore original splash screen with performance fixes
    splash_screen = SplashScreen(app, settings_manager)
    app.processEvents()

    # CRITICAL: Pre-initialize Browse Tab v2 performance systems
    # This eliminates first-run penalties: 118ms→17ms widget creation, 473ms→33ms viewer init
    logger.info("Pre-initializing Browse Tab v2 performance systems...")
    try:
        from src.browse_tab_v2.startup.performance_preinitialization import (
            initialize_browse_tab_performance_systems,
        )

        preinitialization_results = initialize_browse_tab_performance_systems()

        if preinitialization_results["overall_success"]:
            logger.info(
                f"✅ Browse Tab v2 pre-initialization successful in "
                f"{preinitialization_results['overall_duration_ms']:.1f}ms"
            )
        else:
            logger.warning(
                f"⚠️ Browse Tab v2 pre-initialization partially failed: "
                f"{preinitialization_results['successful_systems']}/"
                f"{preinitialization_results['total_systems']} systems ready"
            )

    except Exception as e:
        logger.error(f"❌ Browse Tab v2 pre-initialization failed: {e}")
        logger.warning(
            "Application will continue but may experience first-run performance penalties"
        )

    # CRITICAL: Optimized startup preloading for instant browse tab display
    # This eliminates ALL visible loading delays after splash screen completion
    logger.info("Starting optimized startup preloading...")
    splash_screen.updater.update_progress("OptimizedStartup")

    try:
        import asyncio
        from src.browse_tab_v2.startup.optimized_startup_preloader import (
            OptimizedStartupPreloader,
        )

        # Create optimized preloader with silent mode for faster startup
        preloader = OptimizedStartupPreloader(silent_mode=True)

        # Create progress callback for splash screen updates
        def progress_callback(message: str, progress_percent: int):
            splash_screen.updater.update_detailed_progress(
                f"Loading: {message}", progress_percent
            )

        # Set progress callback on preloader
        preloader.set_progress_callback(progress_callback)

        # Run optimized startup preloading
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            data_preloading_results = loop.run_until_complete(
                preloader.preload_for_instant_startup()
            )

            if data_preloading_results["overall_success"]:
                logger.info(
                    f"✅ Optimized startup completed in "
                    f"{data_preloading_results['overall_duration_ms']:.1f}ms"
                )
                logger.info(
                    f"   Ready: {data_preloading_results['total_sequences']} sequences, "
                    f"{data_preloading_results['preloaded_thumbnails']} thumbnails cached"
                )
            else:
                logger.warning(f"⚠️ Optimized startup partially failed")

        finally:
            # Don't close the loop - keep it alive for browse tab async operations
            logger.info("Event loop kept alive for browse tab async operations")

    except Exception as e:
        logger.error(f"❌ Optimized startup preloading failed: {e}")
        logger.warning(
            "Browse tab will load data on first access (slower initial load)"
        )

    profiler = Profiler()
    # Note: JsonManager and other services are now managed by dependency injection

    # Initialize the modern dependency injection system
    # Note: Legacy compatibility is now set up automatically during initialization
    logger.info("Starting dependency injection initialization...")
    app_context = initialize_dependency_injection()
    logger.info("Dependency injection initialization completed")

    # NEW: Initialize the legacy AppContext singleton before creating widgets
    logger.info("Initializing legacy AppContext singleton...")
    initialize_legacy_appcontext(app_context)
    logger.info("Legacy AppContext initialization completed")

    # Now create the main window with dependency injection (without widgets)
    logger.info("Starting MainWindow creation...")
    main_window = create_main_window(profiler, splash_screen, app_context)
    logger.info("MainWindow creation completed")

    # Initialize window resize tracking
    try:
        from src.browse_tab_v2.debug.window_resize_tracker import init_tracking

        init_tracking(main_window)
        logger.info("Window resize tracking initialized")
    except ImportError:
        logger.debug("Window resize tracking not available")

    # Initialize widgets AFTER both dependency injection AND legacy AppContext are set up
    logger.info("Starting widget initialization...")
    main_window.initialize_widgets()
    logger.info("Widget initialization completed")

    try:
        logger.info("Showing main window...")
        main_window.show()
        main_window.raise_()
        logger.info("Main window shown successfully")

        # Close splash screen after main window is shown
        splash_screen.close()

        # Install message handlers (no more tracing)
        install_handlers()

        logger.info("Starting application event loop...")

        # Print resize tracking report before starting event loop
        try:
            from src.browse_tab_v2.debug.window_resize_tracker import print_report

            print_report()
        except ImportError:
            pass

        exit_code = main_window.exec(app)
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Error showing main window: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
