import os
import time
import json
import shutil
import hashlib
import logging
from typing import Optional, Dict, Any
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget

from ..export_config import ExportConfig


class CacheService:
    def __init__(self, cache_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = cache_dir or self._setup_cache_directory()
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        self._metadata = self._load_metadata()
        self.max_cache_size_mb = 500
        self.max_cache_age_days = 30

        self._cleanup_old_files()

    def _setup_cache_directory(self) -> str:
        try:
            from utils.path_helpers import get_user_editable_resource_path

            cache_base = get_user_editable_resource_path("cache")
        except ImportError:
            cache_base = os.path.join(os.getcwd(), "cache")

        cache_dir = os.path.join(cache_base, "exported_pages")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load cache metadata: {e}")
        return {}

    def _save_metadata(self) -> None:
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache metadata: {e}")

    def generate_cache_key(self, page: QWidget, export_config: ExportConfig) -> str:
        sequence_items = page.property("sequence_items")
        if not sequence_items:
            return f"page_{id(page)}_{int(time.time())}"

        content_data = []
        for item in sequence_items:
            if isinstance(item, dict):
                item_data = {
                    "path": item.get("sequence_data", {}).get("path", ""),
                    "grid_position": item.get("grid_position", {}),
                    "metadata": item.get("sequence_data", {}).get("metadata", {}),
                }
                content_data.append(item_data)

        export_settings = {
            "page_width": export_config.get_print_setting("page_width_pixels", 5100),
            "page_height": export_config.get_print_setting("page_height_pixels", 6600),
            "background_color": str(
                export_config.get_export_setting("background_color", "white")
            ),
            "format": export_config.get_export_setting("format", "PNG"),
            "quality": export_config.get_export_setting("quality", 100),
        }

        combined_data = {"content": content_data, "settings": export_settings}
        data_str = str(sorted(combined_data.items()))
        cache_key = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"page_{cache_key}"

    def get_cached_page_path(self, cache_key: str) -> Optional[str]:
        cache_file_path = os.path.join(self.cache_dir, f"{cache_key}.png")

        if os.path.exists(cache_file_path) and self._validate_cache_file(
            cache_key, cache_file_path
        ):
            self.logger.info(f"Cache HIT for key: {cache_key}")
            return cache_file_path

        self.logger.info(f"Cache MISS for key: {cache_key}")
        return None

    def _validate_cache_file(self, cache_key: str, cache_file_path: str) -> bool:
        try:
            if (
                not os.path.exists(cache_file_path)
                or os.path.getsize(cache_file_path) == 0
            ):
                return False

            if cache_key in self._metadata:
                metadata = self._metadata[cache_key]
                file_mtime = os.path.getmtime(cache_file_path)
                metadata_timestamp = metadata.get("timestamp", 0)
                time_diff = abs(file_mtime - metadata_timestamp)

                if time_diff > 5:
                    return False

            test_pixmap = QPixmap(cache_file_path)
            return not test_pixmap.isNull()

        except Exception as e:
            self.logger.warning(f"Error validating cache file {cache_file_path}: {e}")
            return False

    def cache_page(
        self, cache_key: str, source_file_path: str, metadata: Dict[str, Any] = None
    ) -> bool:
        try:
            if not os.path.exists(source_file_path):
                return False

            cache_file_path = os.path.join(self.cache_dir, f"{cache_key}.png")
            shutil.copy2(source_file_path, cache_file_path)

            cache_metadata = metadata or {}
            cache_metadata.update(
                {
                    "timestamp": time.time(),
                    "source_file": source_file_path,
                    "cache_file": cache_file_path,
                    "file_size": os.path.getsize(cache_file_path),
                }
            )

            self._metadata[cache_key] = cache_metadata
            self._save_metadata()

            self.logger.info(f"Cached page with key: {cache_key}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cache page {cache_key}: {e}")
            return False

    def copy_from_cache(self, cache_key: str, destination_path: str) -> bool:
        cached_path = self.get_cached_page_path(cache_key)
        if not cached_path:
            return False

        try:
            dest_dir = os.path.dirname(destination_path)
            os.makedirs(dest_dir, exist_ok=True)

            shutil.copy2(cached_path, destination_path)
            self.logger.info(f"Copied from cache: {cached_path} -> {destination_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to copy from cache {cache_key}: {e}")
            return False

    def clear_cache(self) -> int:
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith(".png")]
            for filename in cache_files:
                os.remove(os.path.join(self.cache_dir, filename))

            self._metadata.clear()
            self._save_metadata()

            self.logger.info(f"Cache cleared - removed {len(cache_files)} files")
            return len(cache_files)

        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return 0

    def _cleanup_old_files(self) -> None:
        try:
            current_time = time.time()
            max_age_seconds = self.max_cache_age_days * 24 * 3600
            cache_files = []
            total_size = 0

            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".png"):
                    filepath = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        cache_files.append(
                            {
                                "path": filepath,
                                "filename": filename,
                                "size": stat.st_size,
                                "mtime": stat.st_mtime,
                                "age": current_time - stat.st_mtime,
                            }
                        )
                        total_size += stat.st_size

            removed_count = 0

            for file_info in cache_files[:]:
                if file_info["age"] > max_age_seconds:
                    try:
                        os.remove(file_info["path"])
                        cache_key = file_info["filename"][:-4]
                        if cache_key in self._metadata:
                            del self._metadata[cache_key]
                        cache_files.remove(file_info)
                        total_size -= file_info["size"]
                        removed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove old cache file: {e}")

            max_size_bytes = self.max_cache_size_mb * 1024 * 1024
            if total_size > max_size_bytes:
                cache_files.sort(key=lambda x: x["mtime"])

                while total_size > max_size_bytes and cache_files:
                    file_info = cache_files.pop(0)
                    try:
                        os.remove(file_info["path"])
                        cache_key = file_info["filename"][:-4]
                        if cache_key in self._metadata:
                            del self._metadata[cache_key]
                        total_size -= file_info["size"]
                        removed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove cache file: {e}")

            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old cache files")
                self._save_metadata()

        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        try:
            cache_files = []
            total_size = 0

            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".png"):
                    filepath = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(filepath):
                        file_size = os.path.getsize(filepath)
                        cache_files.append(
                            {
                                "filename": filename,
                                "size": file_size,
                                "mtime": os.path.getmtime(filepath),
                            }
                        )
                        total_size += file_size

            return {
                "cached_pages": len(cache_files),
                "total_disk_usage_mb": total_size / (1024 * 1024),
                "cache_directory": self.cache_dir,
                "metadata_entries": len(self._metadata),
                "oldest_cache_age_hours": (
                    (time.time() - min(f["mtime"] for f in cache_files)) / 3600
                    if cache_files
                    else 0
                ),
                "newest_cache_age_hours": (
                    (time.time() - max(f["mtime"] for f in cache_files)) / 3600
                    if cache_files
                    else 0
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {
                "cached_pages": 0,
                "total_disk_usage_mb": 0,
                "cache_directory": self.cache_dir,
                "error": str(e),
            }
