import os
import shutil
import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtGui import QPixmap


class CacheFileManager:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        os.makedirs(cache_dir, exist_ok=True)

    def get_cache_file_path(self, cache_key: str) -> str:
        return os.path.join(self.cache_dir, f"{cache_key}.png")

    def cache_file_exists(self, cache_key: str) -> bool:
        return os.path.exists(self.get_cache_file_path(cache_key))

    def validate_cache_file(
        self, cache_key: str, metadata: Dict[str, Any] = None
    ) -> bool:
        cache_file_path = self.get_cache_file_path(cache_key)

        try:
            if not os.path.exists(cache_file_path):
                return False

            if os.path.getsize(cache_file_path) == 0:
                return False

            if metadata:
                file_mtime = os.path.getmtime(cache_file_path)
                metadata_timestamp = metadata.get("timestamp", 0)
                time_diff = abs(file_mtime - metadata_timestamp)

                if time_diff > 5:  # 5 second tolerance
                    return False

            test_pixmap = QPixmap(cache_file_path)
            return not test_pixmap.isNull()

        except Exception as e:
            self.logger.warning(f"Error validating cache file {cache_file_path}: {e}")
            return False

    def copy_to_cache(self, cache_key: str, source_file_path: str) -> bool:
        try:
            if not os.path.exists(source_file_path):
                return False

            cache_file_path = self.get_cache_file_path(cache_key)
            shutil.copy2(source_file_path, cache_file_path)
            return True

        except Exception as e:
            self.logger.error(f"Failed to copy to cache {cache_key}: {e}")
            return False

    def copy_from_cache(self, cache_key: str, destination_path: str) -> bool:
        try:
            cache_file_path = self.get_cache_file_path(cache_key)
            if not os.path.exists(cache_file_path):
                return False

            dest_dir = os.path.dirname(destination_path)
            os.makedirs(dest_dir, exist_ok=True)

            shutil.copy2(cache_file_path, destination_path)
            return True

        except Exception as e:
            self.logger.error(f"Failed to copy from cache {cache_key}: {e}")
            return False

    def remove_cache_file(self, cache_key: str) -> bool:
        try:
            cache_file_path = self.get_cache_file_path(cache_key)
            if os.path.exists(cache_file_path):
                os.remove(cache_file_path)
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove cache file {cache_key}: {e}")
            return False

    def get_cache_files_info(self) -> List[Dict[str, Any]]:
        try:
            cache_files = []
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".png"):
                    filepath = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        cache_files.append(
                            {
                                "filename": filename,
                                "path": filepath,
                                "size": stat.st_size,
                                "mtime": stat.st_mtime,
                            }
                        )
            return cache_files

        except Exception as e:
            self.logger.error(f"Error getting cache files info: {e}")
            return []

    def clear_all_cache_files(self) -> int:
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith(".png")]
            for filename in cache_files:
                os.remove(os.path.join(self.cache_dir, filename))
            return len(cache_files)

        except Exception as e:
            self.logger.error(f"Error clearing cache files: {e}")
            return 0

    def cleanup_old_files(self, max_age_seconds: float, max_size_bytes: int) -> int:
        try:
            cache_files = self.get_cache_files_info()
            removed_count = 0
            current_time = os.path.getctime(self.cache_dir)

            # Remove old files
            for file_info in cache_files[:]:
                age = current_time - file_info["mtime"]
                if age > max_age_seconds:
                    os.remove(file_info["path"])
                    cache_files.remove(file_info)
                    removed_count += 1

            # Remove large files if over size limit
            total_size = sum(f["size"] for f in cache_files)
            if total_size > max_size_bytes:
                cache_files.sort(key=lambda x: x["mtime"])  # Oldest first

                while total_size > max_size_bytes and cache_files:
                    file_info = cache_files.pop(0)
                    os.remove(file_info["path"])
                    total_size -= file_info["size"]
                    removed_count += 1

            return removed_count

        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
            return 0
