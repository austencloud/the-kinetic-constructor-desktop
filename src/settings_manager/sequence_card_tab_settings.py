from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from settings_manager.settings_manager import SettingsManager


class SequenceCardTabSettings:
    """Settings for the Sequence Card Tab."""

    DEFAULT_SETTINGS = {
        "column_count": 3,  # Default to 3 columns
        "last_length": 16,  # Default to 16 beats
        "selected_levels": [1, 2, 3],  # Default to all levels
        "auto_cache": True,  # Automatically cache sequence card pages
        "cache_max_size_mb": 500,  # Maximum cache size in MB
        "cache_max_age_days": 30,  # Maximum cache age in days
    }

    def __init__(self, settings_manager: "SettingsManager") -> None:
        self.settings_manager = settings_manager
        self.settings = settings_manager.settings

    def get_column_count(self) -> int:
        """Get the number of columns to display in the sequence card tab."""
        return int(
            self.settings.value(
                "sequence_card_tab/column_count", self.DEFAULT_SETTINGS["column_count"]
            )
        )

    def set_column_count(self, count: int) -> None:
        """Set the number of columns to display in the sequence card tab."""
        if count < 2:
            count = 2  # Minimum 2 columns
        elif count > 4:
            count = 4  # Maximum 4 columns

        self.settings.setValue("sequence_card_tab/column_count", count)

    def get_last_length(self) -> int:
        """Get the last selected sequence length."""
        return int(
            self.settings.value(
                "sequence_card_tab/last_length", self.DEFAULT_SETTINGS["last_length"]
            )
        )

    def set_last_length(self, length: int) -> None:
        """Set the last selected sequence length."""
        self.settings.setValue("sequence_card_tab/last_length", length)

    def get_selected_levels(self) -> list:
        """Get the selected difficulty levels."""
        # QSettings stores lists as strings, so we need to handle conversion
        saved_levels = self.settings.value(
            "sequence_card_tab/selected_levels",
            self.DEFAULT_SETTINGS["selected_levels"],
        )

        # Handle different possible formats
        if isinstance(saved_levels, list):
            # Already a list, validate and return
            return [
                lvl for lvl in saved_levels if isinstance(lvl, int) and 1 <= lvl <= 3
            ]
        elif isinstance(saved_levels, str):
            # Try to parse as comma-separated string
            try:
                levels = [int(x.strip()) for x in saved_levels.split(",") if x.strip()]
                return [lvl for lvl in levels if 1 <= lvl <= 3]
            except (ValueError, AttributeError):
                return self.DEFAULT_SETTINGS["selected_levels"]
        else:
            # Fallback to default
            return self.DEFAULT_SETTINGS["selected_levels"]

    def set_selected_levels(self, levels: list) -> None:
        """Set the selected difficulty levels."""
        # Validate input
        valid_levels = [lvl for lvl in levels if isinstance(lvl, int) and 1 <= lvl <= 3]
        if not valid_levels:
            valid_levels = self.DEFAULT_SETTINGS["selected_levels"]

        # Store as comma-separated string for better QSettings compatibility
        levels_str = ",".join(map(str, sorted(valid_levels)))
        self.settings.setValue("sequence_card_tab/selected_levels", levels_str)

    def get_auto_cache(self) -> bool:
        """Get whether to automatically cache sequence card pages."""
        return bool(
            self.settings.value(
                "sequence_card_tab/auto_cache", self.DEFAULT_SETTINGS["auto_cache"]
            )
        )

    def set_auto_cache(self, auto_cache: bool) -> None:
        """Set whether to automatically cache sequence card pages."""
        self.settings.setValue("sequence_card_tab/auto_cache", auto_cache)

    def get_cache_max_size_mb(self) -> int:
        """Get the maximum size of the sequence card page cache in MB."""
        return int(
            self.settings.value(
                "sequence_card_tab/cache_max_size_mb",
                self.DEFAULT_SETTINGS["cache_max_size_mb"],
            )
        )

    def set_cache_max_size_mb(self, size_mb: int) -> None:
        """Set the maximum size of the sequence card page cache in MB."""
        self.settings.setValue("sequence_card_tab/cache_max_size_mb", size_mb)

    def get_cache_max_age_days(self) -> int:
        """Get the maximum age of cached sequence card pages in days."""
        return int(
            self.settings.value(
                "sequence_card_tab/cache_max_age_days",
                self.DEFAULT_SETTINGS["cache_max_age_days"],
            )
        )

    def set_cache_max_age_days(self, days: int) -> None:
        """Set the maximum age of cached sequence card pages in days."""
        self.settings.setValue("sequence_card_tab/cache_max_age_days", days)
