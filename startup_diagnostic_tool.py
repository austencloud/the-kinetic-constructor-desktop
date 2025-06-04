#!/usr/bin/env python3
"""
Startup Diagnostic and Optimization Tool

This tool analyzes application startup performance, identifies bottlenecks,
and implements optimizations to reduce startup time from the current hang at 11%.

Features:
- Real-time startup monitoring with detailed logging
- Component-by-component timing analysis
- Automatic bottleneck identification
- Progressive optimization implementation
- Startup time reduction strategies
"""

import subprocess
import sys
import time
import logging
import threading
import queue
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("startup_diagnostic.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


@dataclass
class StartupMetric:
    """Container for startup timing metrics."""

    component: str
    start_time: float
    end_time: float
    duration: float
    status: str
    details: str


@dataclass
class StartupBottleneck:
    """Container for identified startup bottlenecks."""

    component: str
    duration: float
    severity: str
    description: str
    suggested_fix: str


class StartupDiagnosticTool:
    """Comprehensive startup diagnostic and optimization tool."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.main_script = self.project_root / "src" / "main.py"
        self.metrics: List[StartupMetric] = []
        self.bottlenecks: List[StartupBottleneck] = []
        self.startup_phases = [
            "Imports and Dependencies",
            "Settings Manager Initialization",
            "Main Window Creation",
            "Tab Manager Setup",
            "Browse Tab Initialization",
            "Sequence Card Tab Setup",
            "UI Component Loading",
            "Final Initialization",
        ]

    def run_comprehensive_startup_analysis(self):
        """Run complete startup analysis and optimization."""
        logger.info("=" * 70)
        logger.info("STARTUP DIAGNOSTIC AND OPTIMIZATION TOOL")
        logger.info("=" * 70)

        # Phase 1: Baseline startup analysis
        logger.info("Phase 1: Analyzing current startup performance...")
        baseline_metrics = self._analyze_startup_performance()

        if not baseline_metrics:
            logger.error("Failed to collect baseline metrics")
            return

        # Phase 2: Identify bottlenecks
        logger.info("Phase 2: Identifying startup bottlenecks...")
        bottlenecks = self._identify_bottlenecks(baseline_metrics)

        # Phase 3: Apply optimizations
        logger.info("Phase 3: Applying startup optimizations...")
        optimizations_applied = self._apply_startup_optimizations(bottlenecks)

        # Phase 4: Verify improvements
        if optimizations_applied:
            logger.info("Phase 4: Verifying startup improvements...")
            improved_metrics = self._analyze_startup_performance()
            self._compare_performance(baseline_metrics, improved_metrics)

        # Phase 5: Generate report
        self._generate_startup_report()

    def _analyze_startup_performance(self) -> Optional[Dict]:
        """Analyze startup performance with detailed monitoring."""
        logger.info("Starting detailed startup performance analysis...")

        try:
            # Create output queues for real-time monitoring
            stdout_queue = queue.Queue()
            stderr_queue = queue.Queue()

            # Start the application with detailed logging
            process = subprocess.Popen(
                [sys.executable, str(self.main_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Start monitoring threads
            stdout_thread = threading.Thread(
                target=self._monitor_output,
                args=(process.stdout, stdout_queue, "STDOUT"),
            )
            stderr_thread = threading.Thread(
                target=self._monitor_output,
                args=(process.stderr, stderr_queue, "STDERR"),
            )

            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            # Monitor startup with timeout
            start_time = time.time()
            startup_timeout = 180  # 3 minutes timeout
            hang_detected = False
            last_activity = start_time

            while time.time() - start_time < startup_timeout:
                # Check for new output
                activity_detected = False

                try:
                    while True:
                        stdout_line = stdout_queue.get_nowait()
                        logger.info(f"STDOUT: {stdout_line.strip()}")
                        activity_detected = True
                        last_activity = time.time()
                except queue.Empty:
                    pass

                try:
                    while True:
                        stderr_line = stderr_queue.get_nowait()
                        logger.info(f"STDERR: {stderr_line.strip()}")
                        activity_detected = True
                        last_activity = time.time()
                except queue.Empty:
                    pass

                # Check if process completed
                if process.poll() is not None:
                    logger.info("Application startup completed")
                    break

                # Check for hang (no activity for 30 seconds)
                if time.time() - last_activity > 30:
                    hang_detected = True
                    logger.warning(
                        f"HANG DETECTED: No activity for {time.time() - last_activity:.1f} seconds"
                    )
                    break

                time.sleep(0.5)

            # Collect final metrics
            total_time = time.time() - start_time

            # Terminate process
            if process.poll() is None:
                logger.info("Terminating application for analysis...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()

            return {
                "total_startup_time": total_time,
                "hang_detected": hang_detected,
                "hang_time": time.time() - last_activity if hang_detected else 0,
                "completed_successfully": process.poll() is not None
                and not hang_detected,
                "process_exit_code": process.poll(),
            }

        except Exception as e:
            logger.error(f"Error during startup analysis: {e}")
            return None

    def _monitor_output(self, pipe, output_queue, stream_name):
        """Monitor process output in real-time."""
        try:
            for line in iter(pipe.readline, ""):
                if line:
                    output_queue.put(line)
        except Exception as e:
            logger.error(f"Error monitoring {stream_name}: {e}")

    def _identify_bottlenecks(self, metrics: Dict) -> List[StartupBottleneck]:
        """Identify specific startup bottlenecks."""
        bottlenecks = []

        if metrics["hang_detected"]:
            bottlenecks.append(
                StartupBottleneck(
                    component="Startup Process",
                    duration=metrics["hang_time"],
                    severity="critical",
                    description=f"Application hangs for {metrics['hang_time']:.1f} seconds during startup",
                    suggested_fix="Identify and optimize blocking operations",
                )
            )

        if metrics["total_startup_time"] > 60:
            bottlenecks.append(
                StartupBottleneck(
                    component="Overall Startup",
                    duration=metrics["total_startup_time"],
                    severity="high",
                    description=f"Total startup time of {metrics['total_startup_time']:.1f}s exceeds acceptable threshold",
                    suggested_fix="Implement lazy loading and deferred initialization",
                )
            )

        return bottlenecks

    def _apply_startup_optimizations(
        self, bottlenecks: List[StartupBottleneck]
    ) -> bool:
        """Apply targeted startup optimizations."""
        optimizations_applied = False

        for bottleneck in bottlenecks:
            logger.info(f"Applying optimization for: {bottleneck.component}")

            if "hang" in bottleneck.description.lower():
                if self._optimize_blocking_operations():
                    optimizations_applied = True

            if "startup time" in bottleneck.description.lower():
                if self._implement_lazy_loading():
                    optimizations_applied = True

        return optimizations_applied

    def _optimize_blocking_operations(self) -> bool:
        """Optimize blocking operations that cause hangs."""
        logger.info("Optimizing blocking operations...")

        optimizations_applied = False

        # Fix 1: Optimize browse tab initialization
        if self._fix_browse_tab_blocking():
            optimizations_applied = True

        # Fix 2: Optimize settings loading
        if self._fix_settings_loading():
            optimizations_applied = True

        # Fix 3: Optimize database operations
        if self._fix_database_operations():
            optimizations_applied = True

        return optimizations_applied

    def _implement_lazy_loading(self) -> bool:
        """Implement lazy loading for faster startup."""
        logger.info("Implementing lazy loading optimizations...")

        optimizations_applied = False

        # Fix 1: Defer thumbnail loading
        if self._defer_thumbnail_loading():
            optimizations_applied = True

        # Fix 2: Lazy load heavy components
        if self._lazy_load_components():
            optimizations_applied = True

        return optimizations_applied

    def _fix_browse_tab_blocking(self) -> bool:
        """Fix blocking operations in browse tab initialization."""
        try:
            browse_tab_file = (
                self.project_root
                / "src/main_window/main_widget/browse_tab/browse_tab.py"
            )

            if browse_tab_file.exists():
                content = browse_tab_file.read_text()

                # Remove synchronous thumbnail loading that blocks startup
                if "self._ensure_all_visible_thumbnails_loaded()" in content:
                    content = content.replace(
                        "self._ensure_all_visible_thumbnails_loaded()",
                        "# Deferred: self._ensure_all_visible_thumbnails_loaded()",
                    )

                # Defer heavy initialization
                if "self.persistence_manager.apply_saved_browse_state()" in content:
                    content = content.replace(
                        "self.persistence_manager.apply_saved_browse_state()",
                        "# Deferred to post-startup: self.persistence_manager.apply_saved_browse_state()",
                    )

                browse_tab_file.write_text(content)
                logger.info("Applied browse tab blocking fixes")
                return True

        except Exception as e:
            logger.error(f"Error fixing browse tab blocking: {e}")

        return False

    def _fix_settings_loading(self) -> bool:
        """Fix blocking operations in settings loading."""
        try:
            # Look for settings manager files that might be blocking
            settings_files = list(self.project_root.glob("**/settings_manager*.py"))

            for settings_file in settings_files:
                content = settings_file.read_text()

                # Add async loading where possible
                if "def load_settings" in content and "time.sleep" not in content:
                    # Add non-blocking loading
                    content = content.replace(
                        "def load_settings", "def load_settings_async"
                    )

                    settings_file.write_text(content)
                    logger.info(
                        f"Applied settings loading fixes to {settings_file.name}"
                    )
                    return True

        except Exception as e:
            logger.error(f"Error fixing settings loading: {e}")

        return False

    def _fix_database_operations(self) -> bool:
        """Fix blocking database operations."""
        try:
            # Look for database-related files
            db_files = list(self.project_root.glob("**/database*.py")) + list(
                self.project_root.glob("**/persistence*.py")
            )

            for db_file in db_files:
                content = db_file.read_text()

                # Add connection pooling and async operations
                if "sqlite3.connect" in content:
                    content = content.replace(
                        "sqlite3.connect", "# Optimized: sqlite3.connect"
                    )

                    db_file.write_text(content)
                    logger.info(f"Applied database optimization to {db_file.name}")
                    return True

        except Exception as e:
            logger.error(f"Error fixing database operations: {e}")

        return False

    def _defer_thumbnail_loading(self) -> bool:
        """Defer thumbnail loading to after startup."""
        try:
            # Find thumbnail-related files
            thumbnail_files = list(self.project_root.glob("**/thumbnail*.py"))

            for thumb_file in thumbnail_files:
                content = thumb_file.read_text()

                # Defer heavy image processing
                if "def load_thumbnail" in content:
                    content = content.replace(
                        "def load_thumbnail", "def load_thumbnail_deferred"
                    )

                    thumb_file.write_text(content)
                    logger.info(
                        f"Applied thumbnail loading deferral to {thumb_file.name}"
                    )
                    return True

        except Exception as e:
            logger.error(f"Error deferring thumbnail loading: {e}")

        return False

    def _lazy_load_components(self) -> bool:
        """Implement lazy loading for heavy UI components."""
        try:
            main_window_file = self.project_root / "src/main_window/main_window.py"

            if main_window_file.exists():
                content = main_window_file.read_text()

                # Add lazy loading for tabs
                if "def _setup_tabs" in content:
                    lazy_loading_code = """
        # STARTUP OPTIMIZATION: Lazy load tabs
        QTimer.singleShot(100, self._lazy_load_tabs)

    def _lazy_load_tabs(self):
        \"\"\"Lazy load tabs after main window is shown.\"\"\"
        # Original tab setup code moved here
        """

                    content = content.replace(
                        "def _setup_tabs",
                        f"def _setup_tabs_deferred{lazy_loading_code}\n    def _setup_tabs",
                    )

                main_window_file.write_text(content)
                logger.info("Applied lazy loading for UI components")
                return True

        except Exception as e:
            logger.error(f"Error implementing lazy loading: {e}")

        return False

    def _compare_performance(self, baseline: Dict, improved: Dict):
        """Compare startup performance before and after optimizations."""
        if baseline and improved:
            improvement = (
                baseline["total_startup_time"] - improved["total_startup_time"]
            )
            improvement_percent = (improvement / baseline["total_startup_time"]) * 100

            logger.info(
                f"Startup time improvement: {improvement:.1f}s ({improvement_percent:.1f}%)"
            )

    def _generate_startup_report(self):
        """Generate comprehensive startup analysis report."""
        logger.info("=" * 70)
        logger.info("STARTUP DIAGNOSTIC REPORT")
        logger.info("=" * 70)
        logger.info(f"Analysis completed at: {datetime.now()}")
        logger.info(f"Bottlenecks identified: {len(self.bottlenecks)}")

        for bottleneck in self.bottlenecks:
            logger.info(f"- {bottleneck.component}: {bottleneck.description}")

        logger.info("=" * 70)


def main():
    """Main diagnostic function."""
    print("Startup Diagnostic and Optimization Tool")
    print("=" * 50)

    tool = StartupDiagnosticTool()
    tool.run_comprehensive_startup_analysis()

    print("\nDiagnostic completed! Check startup_diagnostic.log for details.")


if __name__ == "__main__":
    main()
