from typing import Optional, TYPE_CHECKING
from data.constants import DIAMOND, GRID_MODE

if TYPE_CHECKING:
    from core.application_context import ApplicationContext


class DefaultSequenceProvider:
    @staticmethod
    def get_default_sequence(
        app_context: Optional["ApplicationContext"] = None,
    ) -> list[dict]:
        """Return a default sequence with proper metadata."""

        # Get author safely
        author = "Unknown"
        if app_context and app_context.settings_manager:
            try:
                author = app_context.settings_manager.users.get_current_user()
            except:
                pass
        else:
            # Fallback to legacy AppContext if available
            try:
                from src.settings_manager.global_settings.app_context import AppContext

                author = AppContext.settings_manager().users.get_current_user()
            except:
                pass

        # Get prop_type safely
        prop_type = "staff"
        if app_context and app_context.settings_manager:
            try:
                prop_type = (
                    app_context.settings_manager.global_settings.get_prop_type().name.lower()
                )
            except:
                pass
        else:
            # Fallback to legacy AppContext if available
            try:
                from src.settings_manager.global_settings.app_context import AppContext

                prop_type = (
                    AppContext.settings_manager()
                    .global_settings.get_prop_type()
                    .name.lower()
                )
            except:
                pass

        return [
            {
                "word": "",
                "author": author,
                "level": 0,
                "prop_type": prop_type,
                GRID_MODE: DIAMOND,
                "is_circular": False,
                "can_be_CAP": False,
                "is_strict_rotated_CAP": False,
                "is_strict_mirrored_CAP": False,
                "is_strict_swapped_CAP": False,
                "is_mirrored_swapped_CAP": False,
                "is_rotated_swapped_CAP": False,
            }
        ]
