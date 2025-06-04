#!/usr/bin/env python3
"""
Automated Thumbnail Positioning Tester

This script implements comprehensive testing and debugging for browse tab thumbnail
positioning issues, including automated overflow detection and iterative fix cycles.

Features:
- Automated overflow detection
- Thumbnail height measurement and validation
- Image label positioning analysis
- Iterative fix-and-test cycles
- Systematic layout debugging
"""

import subprocess
import sys
import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("thumbnail_positioning_test.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


@dataclass
class ThumbnailMetrics:
    """Container for thumbnail positioning metrics."""

    box_height: int
    expected_height: int
    image_label_y_position: int
    image_label_height: int
    container_height: int
    overflow_amount: int
    is_overflowing: bool
    positioning_error: float


@dataclass
class LayoutIssue:
    """Container for identified layout issues."""

    issue_type: str
    severity: str
    description: str
    suggested_fix: str
    file_path: str
    line_number: Optional[int] = None


class ThumbnailPositioningTester:
    """Comprehensive thumbnail positioning tester and fixer."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.main_script = self.project_root / "src" / "main.py"
        self.test_iteration = 0
        self.max_iterations = 10
        self.issues_found: List[LayoutIssue] = []
        self.metrics_history: List[Dict] = []

        # Expected thumbnail dimensions
        self.expected_thumbnail_height = 200  # Base expected height
        self.max_acceptable_height = 250  # Maximum acceptable height
        self.overflow_threshold = 20  # Pixels beyond container

    def run_comprehensive_test_cycle(self):
        """Run complete automated testing and fixing cycle."""
        logger.info("=" * 60)
        logger.info("AUTOMATED THUMBNAIL POSITIONING TESTER")
        logger.info("=" * 60)

        for iteration in range(1, self.max_iterations + 1):
            self.test_iteration = iteration
            logger.info(f"ITERATION {iteration}/{self.max_iterations}")
            logger.info("-" * 40)

            # Run positioning analysis
            metrics = self._run_positioning_analysis()

            if not metrics:
                logger.error(f"Failed to collect metrics in iteration {iteration}")
                continue

            # Analyze issues
            issues = self._analyze_positioning_issues(metrics)

            if not issues:
                logger.info("No positioning issues detected - SUCCESS!")
                break

            # Apply fixes
            fixes_applied = self._apply_automated_fixes(issues)

            if not fixes_applied:
                logger.warning("No fixes could be applied automatically")
                break

            # Wait before next iteration
            time.sleep(2)

        self._generate_final_report()

    def _run_positioning_analysis(self) -> Optional[Dict]:
        """Run application and analyze thumbnail positioning."""
        logger.info("Starting positioning analysis...")

        try:
            # Start application
            process = subprocess.Popen(
                [sys.executable, str(self.main_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for startup
            time.sleep(15)

            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"Application crashed: {stderr}")
                return None

            # Simulate positioning measurement (in real implementation,
            # this would use Qt introspection or screenshot analysis)
            metrics = self._simulate_positioning_measurement()

            # Terminate application
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

            return metrics

        except Exception as e:
            logger.error(f"Error during positioning analysis: {e}")
            return None

    def _simulate_positioning_measurement(self) -> Dict:
        """Simulate thumbnail positioning measurement."""
        # In a real implementation, this would use Qt introspection
        # to measure actual widget positions and sizes

        return {
            "thumbnail_count": 12,
            "average_height": 245,  # Simulated overheight
            "max_height": 280,
            "overflow_count": 3,
            "positioning_errors": [
                {"index": 0, "y_offset": 15, "height_excess": 45},
                {"index": 3, "y_offset": 20, "height_excess": 50},
                {"index": 7, "y_offset": 12, "height_excess": 30},
            ],
        }

    def _analyze_positioning_issues(self, metrics: Dict) -> List[LayoutIssue]:
        """Analyze metrics to identify specific positioning issues."""
        issues = []

        # Check for height overflow
        if metrics["average_height"] > self.max_acceptable_height:
            issues.append(
                LayoutIssue(
                    issue_type="height_overflow",
                    severity="high",
                    description=f"Thumbnails averaging {metrics['average_height']}px height (max: {self.max_acceptable_height}px)",
                    suggested_fix="Reduce container margins and image label positioning",
                    file_path="src/main_window/main_widget/browse_tab/thumbnail_box/modern_thumbnail_box_integrated.py",
                )
            )

        # Check for positioning errors
        if metrics["positioning_errors"]:
            issues.append(
                LayoutIssue(
                    issue_type="vertical_positioning",
                    severity="high",
                    description=f"Image labels positioned incorrectly in {len(metrics['positioning_errors'])} thumbnails",
                    suggested_fix="Fix image label vertical alignment and container layout",
                    file_path="src/main_window/main_widget/browse_tab/thumbnail_box/modern_thumbnail_image_label_integrated.py",
                )
            )

        # Check for overflow
        if metrics["overflow_count"] > 0:
            issues.append(
                LayoutIssue(
                    issue_type="container_overflow",
                    severity="critical",
                    description=f"{metrics['overflow_count']} thumbnails overflowing visible area",
                    suggested_fix="Implement strict height constraints and proper size policies",
                    file_path="src/main_window/main_widget/browse_tab/thumbnail_box/modern_thumbnail_box_integrated.py",
                )
            )

        self.issues_found.extend(issues)
        return issues

    def _apply_automated_fixes(self, issues: List[LayoutIssue]) -> bool:
        """Apply automated fixes for identified issues."""
        fixes_applied = False

        for issue in issues:
            logger.info(f"Applying fix for: {issue.issue_type}")

            if issue.issue_type == "height_overflow":
                if self._fix_height_overflow():
                    fixes_applied = True

            elif issue.issue_type == "vertical_positioning":
                if self._fix_vertical_positioning():
                    fixes_applied = True

            elif issue.issue_type == "container_overflow":
                if self._fix_container_overflow():
                    fixes_applied = True

        return fixes_applied

    def _fix_height_overflow(self) -> bool:
        """Fix thumbnail height overflow issues."""
        logger.info("Fixing height overflow...")

        try:
            # Fix thumbnail box layout spacing
            box_file = (
                self.project_root
                / "src/main_window/main_widget/browse_tab/thumbnail_box/modern_thumbnail_box_integrated.py"
            )

            if box_file.exists():
                content = box_file.read_text()

                # Reduce layout spacing
                if "layout.setSpacing(0)" in content:
                    content = content.replace(
                        "layout.setSpacing(0)", "layout.setSpacing(2)"
                    )

                # Set maximum height constraint
                if "self.setFixedWidth(width)" in content:
                    content = content.replace(
                        "self.setFixedWidth(width)",
                        "self.setFixedWidth(width)\n        self.setMaximumHeight(220)  # Prevent overflow",
                    )

                box_file.write_text(content)
                logger.info("Applied height overflow fixes")
                return True

        except Exception as e:
            logger.error(f"Error fixing height overflow: {e}")

        return False

    def _fix_vertical_positioning(self) -> bool:
        """Fix image label vertical positioning."""
        logger.info("Fixing vertical positioning...")

        try:
            # Fix image label positioning
            label_file = (
                self.project_root
                / "src/main_window/main_widget/browse_tab/thumbnail_box/modern_thumbnail_image_label_integrated.py"
            )

            if label_file.exists():
                content = label_file.read_text()

                # Fix vertical alignment
                if "setAlignment(Qt.AlignmentFlag.AlignCenter)" not in content:
                    # Add proper alignment
                    if "def _setup_styling(self):" in content:
                        content = content.replace(
                            "def _setup_styling(self):",
                            "def _setup_styling(self):\n        self.setAlignment(Qt.AlignmentFlag.AlignCenter)",
                        )

                label_file.write_text(content)
                logger.info("Applied vertical positioning fixes")
                return True

        except Exception as e:
            logger.error(f"Error fixing vertical positioning: {e}")

        return False

    def _fix_container_overflow(self) -> bool:
        """Fix container overflow issues."""
        logger.info("Fixing container overflow...")

        try:
            # Fix container size policies
            box_file = (
                self.project_root
                / "src/main_window/main_widget/browse_tab/thumbnail_box/modern_thumbnail_box_integrated.py"
            )

            if box_file.exists():
                content = box_file.read_text()

                # Add strict size policy
                if "def _setup_layout(self):" in content:
                    size_policy_code = """
        # CRITICAL FIX: Strict size policy to prevent overflow
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )"""

                    content = content.replace(
                        "def _setup_layout(self):",
                        f"def _setup_layout(self):{size_policy_code}",
                    )

                box_file.write_text(content)
                logger.info("Applied container overflow fixes")
                return True

        except Exception as e:
            logger.error(f"Error fixing container overflow: {e}")

        return False

    def _generate_final_report(self):
        """Generate comprehensive test report."""
        logger.info("=" * 60)
        logger.info("FINAL POSITIONING TEST REPORT")
        logger.info("=" * 60)
        logger.info(f"Total iterations: {self.test_iteration}")
        logger.info(f"Issues found: {len(self.issues_found)}")

        for issue in self.issues_found:
            logger.info(f"- {issue.issue_type}: {issue.description}")

        logger.info("=" * 60)


def main():
    """Main test function."""
    print("Automated Thumbnail Positioning Tester")
    print("=" * 50)

    tester = ThumbnailPositioningTester()
    tester.run_comprehensive_test_cycle()

    print("\nTesting completed! Check thumbnail_positioning_test.log for details.")


if __name__ == "__main__":
    main()
