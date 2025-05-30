import gc
import time
import psutil
from typing import Optional


class MemoryManager:
    def __init__(self, max_memory_mb: int = 2000, check_interval: int = 5):
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval

    def get_memory_usage(self) -> float:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)
        except Exception:
            return 0.0

    def check_and_manage_memory(self, force_cleanup: bool = False) -> float:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            if force_cleanup or memory_mb > self.max_memory_mb:
                gc.collect()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                time.sleep(0.1)

            return memory_mb
        except Exception:
            return 0.0

    def force_memory_cleanup(self):
        gc.collect()
        time.sleep(0.1)
