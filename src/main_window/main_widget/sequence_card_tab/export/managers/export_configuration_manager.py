class ExportConfigurationManager:
    def __init__(self):
        self.quality_settings = {
            "png_compression": 1,
            "high_quality": True,
        }
        self.batch_size = 15
        self.memory_check_interval = 5

    def get_default_export_options(self) -> dict:
        return {
            "add_word": True,
            "add_user_info": True,
            "add_difficulty_level": True,
            "add_date": True,
            "add_note": True,
            "add_beat_numbers": True,
            "add_reversal_symbols": True,
            "combined_grids": False,
            "include_start_position": True,
        }

    def get_quality_settings(self) -> dict:
        return self.quality_settings.copy()

    def update_quality_settings(self, **kwargs):
        self.quality_settings.update(kwargs)

    def get_batch_size(self) -> int:
        return self.batch_size

    def set_batch_size(self, size: int):
        self.batch_size = max(1, size)

    def get_memory_check_interval(self) -> int:
        return self.memory_check_interval

    def set_memory_check_interval(self, interval: int):
        self.memory_check_interval = max(1, interval)
