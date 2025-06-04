# src/main_window/main_widget/sequence_card_tab/export/export_config.py
import logging
from typing import Dict, Any, Tuple, Optional, TYPE_CHECKING
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..tab import SequenceCardTab


class ExportConfig:
    """
    Manages configuration settings for sequence card page exports.

    This class encapsulates:
    1. Print settings (page dimensions, DPI)
    2. Export settings (format, quality, margins)
    3. Grid layout settings (dimensions, spacing)
    4. Default configurations for different paper sizes and sequence lengths
    5. Synchronization with UI components to ensure consistency
    """

    def __init__(self, sequence_card_tab: Optional["SequenceCardTab"] = None):
        self.logger = logging.getLogger(__name__)
        self.sequence_card_tab = sequence_card_tab

        self.print_settings = {
            "page_width_inches": 8.5,
            "page_height_inches": 11.0,
            "dpi": 600,
            "page_width_pixels": int(8.5 * 600),
            "page_height_pixels": int(11.0 * 600),
        }

        self.export_settings = {
            "format": "PNG",
            "quality": 100,
            "dpi": 600,
            "background_color": Qt.GlobalColor.white,
            "compression": 0,  # 0 = no compression for maximum quality
            "page_margin_left": int(0.25 * 600),
            "page_margin_top": int(0.5 * 600),
            "page_margin_right": int(0.25 * 600),
            "page_margin_bottom": int(0.5 * 600),
            "cell_spacing": int(0.125 * 600),
            "cell_padding": int(0.05 * 600),
            "grid_rows": 3,
            "grid_cols": 2,
            "grid_dimensions": {
                4: (2, 2),
                8: (2, 4),
                16: (4, 4),
            },
            # Color management settings
            "color_management": {
                "preserve_color_profile": True,
                "gamma_correction": 1.0,  # 1.0 = no correction, <1.0 = lighter, >1.0 = darker
                # REMOVED: Red enhancement causing gray-to-red color bleeding
                # "enhance_red_channel": 1.15,  # Slight boost to red channel to compensate for printing
                "color_correction": {
                    # Specific color corrections for known colors
                    "#ED1C24": "#FF1C24",  # Brighten the standard red color for better print fidelity
                },
                "use_high_bit_depth": True,  # Use 16-bit color depth when possible
            },
            # Image processing settings
            "image_processing": {
                "scaling_algorithm": Qt.TransformationMode.SmoothTransformation,
                "maintain_larger_dimensions": True,  # Keep images larger during processing
                "upscale_factor": 1.2,  # Upscale images by 20% before final scaling to preserve detail
                "sharpen_after_scaling": True,  # Apply slight sharpening after scaling
                # Two-stage processing for optimal quality vs color vibrancy balance
                "color_processing_size": 1000,  # High resolution for crisp text and quality color processing
                "printer_output_size": 800,  # Balanced size for good sharpness while maintaining printer compatibility
            },
        }

    def get_print_setting(self, key: str, default: Any = None) -> Any:
        return self.print_settings.get(key, default)

    def get_export_setting(self, key: str, default: Any = None) -> Any:
        return self.export_settings.get(key, default)

    def set_print_setting(self, key: str, value: Any) -> None:
        self.print_settings[key] = value
        self.logger.debug(f"Set print setting {key} to {value}")

    def set_export_setting(self, key: str, value: Any) -> None:
        self.export_settings[key] = value
        self.logger.debug(f"Set export setting {key} to {value}")

    def get_grid_dimensions(
        self, sequence_length: Optional[int] = None
    ) -> Tuple[int, int]:
        if sequence_length is None:
            return (
                self.get_export_setting("grid_rows", 3),
                self.get_export_setting("grid_cols", 2),
            )

        grid_dimensions = self.get_export_setting("grid_dimensions", {})

        if sequence_length in grid_dimensions:
            return grid_dimensions[sequence_length]

        if sequence_length <= 4:
            return (2, 2)
        elif sequence_length <= 8:
            return (2, 4)
        else:
            return (4, 4)

    def get_content_area(self) -> Dict[str, int]:
        page_width = self.get_print_setting("page_width_pixels")
        page_height = self.get_print_setting("page_height_pixels")
        margin_left = self.get_export_setting("page_margin_left")
        margin_top = self.get_export_setting("page_margin_top")
        margin_right = self.get_export_setting("page_margin_right")
        margin_bottom = self.get_export_setting("page_margin_bottom")

        content_width = page_width - margin_left - margin_right
        content_height = page_height - margin_top - margin_bottom

        return {
            "x": margin_left,
            "y": margin_top,
            "width": content_width,
            "height": content_height,
        }

    def get_cell_dimensions(self, rows: int, cols: int) -> Dict[str, int]:
        content_area = self.get_content_area()
        cell_spacing = self.get_export_setting("cell_spacing")

        available_width = content_area["width"] - (cols - 1) * cell_spacing
        available_height = content_area["height"] - (rows - 1) * cell_spacing

        cell_width = available_width // cols
        cell_height = available_height // rows

        return {"width": cell_width, "height": cell_height, "spacing": cell_spacing}

    def sync_with_ui_layout(self) -> bool:
        """
        Synchronize grid dimensions with those used in the UI components.

        This method:
        1. Checks if the sequence_card_tab is available
        2. Retrieves grid dimensions from the PrintablePageFactory
        3. Updates the export_settings with the UI grid dimensions

        Returns:
            bool: True if synchronization was successful, False otherwise
        """
        if self.sequence_card_tab is None:
            self.logger.warning("Cannot sync with UI layout: sequence_card_tab is None")
            return False

        try:
            # Try to access the PrintableDisplayer and its manager
            if hasattr(self.sequence_card_tab, "printable_displayer"):
                printable_displayer = self.sequence_card_tab.printable_displayer

                # Check if the PrintableDisplayer has a manager
                if hasattr(printable_displayer, "manager"):
                    # Get the page factory from the manager
                    page_factory = printable_displayer.manager.page_factory

                    # Get the grid dimensions from the page factory
                    rows = page_factory.rows
                    cols = page_factory.columns

                    # Get the sequence length from the manager
                    sequence_length = getattr(
                        self.sequence_card_tab.nav_sidebar, "selected_length", 0
                    )

                    # Update the grid dimensions in the export settings
                    self.set_export_setting("grid_rows", rows)
                    self.set_export_setting("grid_cols", cols)

                    # Update the grid dimensions for this sequence length
                    if sequence_length > 0:
                        grid_dimensions = self.get_export_setting("grid_dimensions", {})
                        grid_dimensions[sequence_length] = (rows, cols)
                        self.set_export_setting("grid_dimensions", grid_dimensions)

                    self.logger.info(
                        f"Synchronized grid dimensions with UI: {rows}x{cols} for sequence length {sequence_length}"
                    )
                    return True

            # If we can't access the manager, try to access the page factory directly
            elif hasattr(self.sequence_card_tab, "page_factory"):
                page_factory = self.sequence_card_tab.page_factory
                rows = page_factory.rows
                cols = page_factory.columns

                # Update the grid dimensions in the export settings
                self.set_export_setting("grid_rows", rows)
                self.set_export_setting("grid_cols", cols)

                self.logger.info(
                    f"Synchronized grid dimensions with UI page_factory: {rows}x{cols}"
                )
                return True

            self.logger.warning(
                "Cannot sync with UI layout: PrintableDisplayer or page_factory not found"
            )
            return False

        except Exception as e:
            self.logger.error(f"Error synchronizing with UI layout: {e}")
            return False
