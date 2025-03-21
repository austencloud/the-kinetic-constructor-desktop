import sys
import os

# Constants and paths defined first
def main_without_imports():
    # Import the modules now that paths are configured
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication
    from main_window.main_widget.json_manager.json_manager import JsonManager
    from main_window.main_widget.json_manager.special_placement_saver import SpecialPlacementSaver
    from main_window.main_window import MainWindow
    from utils.path_helpers import get_data_path
    from settings_manager.settings_manager import SettingsManager
    from main_window.main_widget.special_placement_loader import SpecialPlacementLoader
    from splash_screen.splash_screen import SplashScreen
    from profiler import Profiler
    from utils.call_tracer import CallTracer
    from settings_manager.global_settings.app_context import AppContext
    from utils.paint_event_supressor import PaintEventSuppressor
    
    # Debug information
    print("Python version:", sys.version)
    print("Running main.py main_without_imports()")
    print("Current working directory:", os.getcwd())
    
    # Define project directory and log file now that imports are available
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
    LOG_FILE_PATH = get_data_path("trace_log.txt")
    log_file = open(LOG_FILE_PATH, "w")
    
    # Initialize application
    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")
    
    settings_manager = SettingsManager()
    splash_screen = SplashScreen(app, settings_manager)
    app.processEvents()
    
    profiler = Profiler()
    json_manager = JsonManager()
    special_placement_handler = SpecialPlacementSaver()
    special_placement_loader = SpecialPlacementLoader()
    
    AppContext.init(
        settings_manager,
        json_manager,
        special_placement_handler,
        special_placement_loader=special_placement_loader,
    )
    
    # Create and show main window
    main_window = MainWindow(profiler, splash_screen)
    AppContext._main_window = main_window
    
    main_window.show()
    main_window.raise_()
    
    QTimer.singleShot(0, lambda: splash_screen.close())
    
    # Install handlers and tracers
    PaintEventSuppressor.install_message_handler()
    tracer = CallTracer(PROJECT_DIR, log_file)
    sys.settrace(tracer.trace_calls)
    
    # Start the application event loop
    exit_code = main_window.exec(app)
    sys.exit(exit_code)


# This is kept for running directly in development
if __name__ == "__main__":
    # Configure the import paths
    if getattr(sys, 'frozen', False):
        # Running as frozen application
        base_dir = sys._MEIPASS
        src_dir = os.path.join(base_dir, "src")
        if os.path.exists(src_dir) and src_dir not in sys.path:
            sys.path.insert(0, src_dir)
    else:
        # In development, add project root to path
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
    
    # Now call the function with imports
    main_without_imports()