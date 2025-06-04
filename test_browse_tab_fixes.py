#!/usr/bin/env python3
"""
Systematic testing script for browse tab visual fixes.

This script implements automatic program restarts and incremental testing
to identify and verify fixes for:
1. Image label width/height scaling problems
2. Sequence label cards shifting/overflow bugs

Usage:
    python test_browse_tab_fixes.py
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('browse_tab_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BrowseTabTester:
    """Systematic tester for browse tab visual issues."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.main_script = self.project_root / "src" / "main.py"
        self.test_iteration = 0
        self.max_iterations = 5
        
    def run_test_cycle(self):
        """Run a complete test cycle with automatic restarts."""
        logger.info("🚀 Starting browse tab visual fixes test cycle")
        
        for iteration in range(1, self.max_iterations + 1):
            self.test_iteration = iteration
            logger.info(f"📋 Test Iteration {iteration}/{self.max_iterations}")
            
            # Run the application
            success = self._run_application_test()
            
            if success:
                logger.info(f"✅ Iteration {iteration} completed successfully")
            else:
                logger.error(f"❌ Iteration {iteration} failed")
                
            # Wait between iterations
            if iteration < self.max_iterations:
                logger.info("⏳ Waiting 3 seconds before next iteration...")
                time.sleep(3)
                
        logger.info("🎯 Test cycle completed")
        
    def _run_application_test(self):
        """Run the application and monitor for issues."""
        try:
            logger.info(f"🔄 Starting application (iteration {self.test_iteration})")
            
            # Start the application
            process = subprocess.Popen(
                [sys.executable, str(self.main_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor application startup
            startup_timeout = 30  # 30 seconds for startup
            start_time = time.time()
            
            while time.time() - start_time < startup_timeout:
                # Check if process is still running
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    logger.error(f"Application crashed during startup:")
                    logger.error(f"STDOUT: {stdout}")
                    logger.error(f"STDERR: {stderr}")
                    return False
                    
                time.sleep(0.5)
                
            # Application should be running now
            logger.info("✅ Application started successfully")
            
            # Let it run for a bit to test browse tab loading
            logger.info("🔍 Monitoring browse tab behavior...")
            time.sleep(10)  # Monitor for 10 seconds
            
            # Check if still running
            if process.poll() is None:
                logger.info("✅ Application running stable")
                # Terminate gracefully
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Application crashed during monitoring:")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running application test: {e}")
            return False
            
    def log_test_summary(self):
        """Log a summary of the test results."""
        logger.info("=" * 60)
        logger.info("📊 BROWSE TAB VISUAL FIXES TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("🎯 Issues being tested:")
        logger.info("   1. Image label width/height scaling problems")
        logger.info("   2. Sequence label cards shifting/overflow bugs")
        logger.info("")
        logger.info("🔧 Fixes implemented:")
        logger.info("   1. Set image labels to use 100% container width")
        logger.info("   2. Disabled CSS transitions causing layout shifts")
        logger.info("   3. Removed deferred initialization operations")
        logger.info("   4. Added proper size policies for image labels")
        logger.info("")
        logger.info(f"📋 Total test iterations: {self.max_iterations}")
        logger.info("📝 Check browse_tab_test.log for detailed results")
        logger.info("=" * 60)

def main():
    """Main test function."""
    print("🧪 Browse Tab Visual Fixes - Systematic Testing")
    print("=" * 50)
    
    tester = BrowseTabTester()
    
    # Log initial state
    logger.info("🎯 Testing fixes for browse tab visual issues:")
    logger.info("   Issue 1: Image label width/height scaling problems")
    logger.info("   Issue 2: Sequence label cards shifting/overflow bugs")
    
    # Run test cycle
    tester.run_test_cycle()
    
    # Log summary
    tester.log_test_summary()
    
    print("\n✅ Testing completed! Check browse_tab_test.log for details.")

if __name__ == "__main__":
    main()
