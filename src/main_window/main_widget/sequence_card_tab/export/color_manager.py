# src/main_window/main_widget/sequence_card_tab/export/color_manager.py
import logging
import sys
from typing import Dict, Any, Optional, Tuple
import re
from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import Qt, QVersionNumber, QSize

from data.constants import HEX_RED, HEX_BLUE, RED, BLUE


class ColorManager:
    """
    Manages color transformations and corrections for exported images.

    This class handles:
    1. Color profile preservation
    2. Gamma correction
    3. Color channel adjustments
    4. Specific color replacements
    5. Color space transformations for print-optimized output
    """

    def __init__(self, config_settings: Dict[str, Any]):
        """
        Initialize the ColorManager with configuration settings.

        Args:
            config_settings: Dictionary containing color management settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Ensure INFO level logging
        self.settings = config_settings

        # Add console handler if not already present
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Extract specific settings with defaults
        self.preserve_color_profile = self.settings.get("preserve_color_profile", True)
        self.gamma_correction = self.settings.get("gamma_correction", 1.0)
        # REMOVED: Red enhancement causing gray-to-red color bleeding
        # self.enhance_red_channel = self.settings.get("enhance_red_channel", 1.15)
        self.color_correction = self.settings.get("color_correction", {})
        self.use_high_bit_depth = self.settings.get("use_high_bit_depth", True)

        # Determine available image formats based on PyQt version
        self._detect_available_formats()

        # Initialize color correction maps
        self._initialize_color_maps()

        # Pre-compute all lookup tables for maximum performance
        self._precompute_all_lookup_tables()

    def _detect_available_formats(self):
        """Detect available QImage formats based on PyQt version."""
        self.logger.debug("Detecting available QImage formats")

        # Default to 8-bit formats which are always available
        self.high_bit_depth_format = QImage.Format.Format_ARGB32_Premultiplied
        self.standard_format = QImage.Format.Format_ARGB32_Premultiplied

        # Check if 16-bit formats are available
        try:
            # Try to access Format_RGBA64_Premultiplied (available in newer PyQt6 versions)
            if hasattr(QImage.Format, "Format_RGBA64_Premultiplied"):
                self.high_bit_depth_format = QImage.Format.Format_RGBA64_Premultiplied
                self.logger.debug(
                    "Using Format_RGBA64_Premultiplied for high bit depth"
                )
            # Try to access Format_ARGB64_Premultiplied (might be available in some versions)
            elif hasattr(QImage.Format, "Format_ARGB64_Premultiplied"):
                self.high_bit_depth_format = QImage.Format.Format_ARGB64_Premultiplied
                self.logger.debug(
                    "Using Format_ARGB64_Premultiplied for high bit depth"
                )
            else:
                # Fallback to 8-bit format if no 16-bit format is available
                self.logger.warning(
                    "No 16-bit image format available, using 8-bit format"
                )
                self.use_high_bit_depth = False
        except Exception as e:
            self.logger.warning(f"Error detecting image formats: {e}")
            self.use_high_bit_depth = False

    def _initialize_color_maps(self) -> None:
        """Initialize color correction maps for efficient processing."""
        # REMOVED: Default red enhancement (was causing gray-to-red color bleeding)
        # if HEX_RED not in self.color_correction:
        #     # Default enhancement for the standard red color
        #     brighter_red = self._brighten_color(HEX_RED, factor=1.15)
        #     self.color_correction[HEX_RED] = brighter_red

        self.logger.debug(f"Initialized color correction map: {self.color_correction}")

    def _precompute_all_lookup_tables(self):
        """Pre-compute all lookup tables for maximum performance."""
        # Gamma correction lookup table
        if self.gamma_correction != 1.0:
            gamma_inv = 1.0 / self.gamma_correction
            self._gamma_lut = [int(255 * pow(i / 255.0, gamma_inv)) for i in range(256)]
        else:
            self._gamma_lut = list(range(256))  # Identity mapping

        # REMOVED: Red channel enhancement lookup table (was causing gray-to-red color bleeding)
        # if self.enhance_red_channel != 1.0:
        #     self._red_enhancement_lut = [
        #         min(255, int(i * self.enhance_red_channel)) for i in range(256)
        #     ]
        # else:
        #     self._red_enhancement_lut = list(range(256))  # Identity mapping

        # Red enhancement disabled - use identity mapping
        self._red_enhancement_lut = list(range(256))  # Identity mapping

        # Color correction lookup table (RGB to RGB mapping)
        self._color_correction_lut = {}
        for hex_color, corrected_hex in self.color_correction.items():
            if hex_color.startswith("#") and corrected_hex.startswith("#"):
                try:
                    original = QColor(hex_color)
                    corrected = QColor(corrected_hex)
                    # Store as RGB integer for fast lookup
                    self._color_correction_lut[original.rgb()] = corrected.rgb()
                except Exception as e:
                    self.logger.warning(
                        f"Invalid color conversion: {hex_color} -> {corrected_hex}: {e}"
                    )

        # Pre-compute tolerance-based color correction map for common colors
        self._tolerance_correction_map = {}
        tolerance = 2  # ULTRA-PRECISE tolerance for exact color matching (was 8, now 2)
        for original_rgb, corrected_rgb in self._color_correction_lut.items():
            original_color = QColor(original_rgb)
            orig_r, orig_g, orig_b = (
                original_color.red(),
                original_color.green(),
                original_color.blue(),
            )

            # Pre-compute corrections for colors within tolerance
            for r_offset in range(-tolerance, tolerance + 1, 5):  # Sample every 5 units
                for g_offset in range(-tolerance, tolerance + 1, 5):
                    for b_offset in range(-tolerance, tolerance + 1, 5):
                        test_r = max(0, min(255, orig_r + r_offset))
                        test_g = max(0, min(255, orig_g + g_offset))
                        test_b = max(0, min(255, orig_b + b_offset))

                        # Check if within tolerance
                        distance_squared = (
                            r_offset * r_offset
                            + g_offset * g_offset
                            + b_offset * b_offset
                        )
                        if distance_squared <= tolerance * tolerance:
                            test_rgb = QColor(test_r, test_g, test_b).rgb()
                            self._tolerance_correction_map[test_rgb] = corrected_rgb

        self.logger.debug(
            f"Pre-computed {len(self._tolerance_correction_map)} tolerance-based color corrections"
        )

    def _brighten_color(self, hex_color: str, factor: float = 1.15) -> str:
        """
        Brighten a hex color by the specified factor.

        Args:
            hex_color: Hex color string (e.g., "#ED1C24")
            factor: Brightness factor (>1.0 = brighter, <1.0 = darker)

        Returns:
            str: Brightened hex color
        """
        if not hex_color.startswith("#") or len(hex_color) != 7:
            return hex_color

        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)

            # Apply brightness factor with limits
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))

            return f"#{r:02X}{g:02X}{b:02X}"
        except ValueError:
            self.logger.warning(f"Invalid hex color: {hex_color}")
            return hex_color

    def correct_svg_colors(self, svg_data: str) -> str:
        """
        Apply color corrections to SVG data.

        Args:
            svg_data: SVG data as string

        Returns:
            str: Corrected SVG data
        """
        if not svg_data:
            return svg_data

        # Replace known colors with corrected versions
        for original_color, corrected_color in self.color_correction.items():
            # Skip if the original color is not in the standard format
            if not original_color.startswith("#"):
                continue

            # Create patterns to match the color in different contexts
            patterns = [
                # CSS fill property
                re.compile(r'(fill=")(' + re.escape(original_color) + r')(")'),
                # CSS style attribute
                re.compile(r"(fill:\s*)(" + re.escape(original_color) + r")(\s*;)"),
                # Class definition
                re.compile(
                    r"(\.(st0|cls-1)\s*\{[^}]*?fill:\s*)("
                    + re.escape(original_color)
                    + r")([^}]*?\})"
                ),
            ]

            # Apply replacements
            for pattern in patterns:
                svg_data = pattern.sub(
                    lambda m: m.group(1) + corrected_color + m.group(len(m.groups())),
                    svg_data,
                )

        return svg_data

    def process_image(self, image: QImage) -> QImage:
        """
        Apply color corrections to a QImage.

        Args:
            image: Source QImage

        Returns:
            QImage: Color-corrected QImage
        """
        if image.isNull():
            self.logger.warning("Cannot process null image")
            return image

        # Convert to a format that supports color manipulation
        try:
            if self.use_high_bit_depth and image.format() != self.high_bit_depth_format:
                # Use 16-bit color depth for better color fidelity if available
                self.logger.debug(f"Converting image to high bit depth format")
                processed_image = image.convertToFormat(self.high_bit_depth_format)
            else:
                # Fallback to 8-bit color depth
                self.logger.debug(f"Converting image to standard format")
                processed_image = image.convertToFormat(self.standard_format)
        except Exception as e:
            # If format conversion fails, use the original image
            self.logger.warning(
                f"Error converting image format: {e}. Using original format."
            )
            processed_image = image.copy()

        # Apply gamma correction if needed
        if self.gamma_correction != 1.0:
            processed_image = self._apply_gamma_correction(
                processed_image, self.gamma_correction
            )

        # REMOVED: Red channel enhancement (was causing gray-to-red color bleeding)
        # if self.enhance_red_channel != 1.0:
        #     processed_image = self._enhance_color_channel(
        #         processed_image, channel=0, factor=self.enhance_red_channel
        #     )

        # Apply specific color corrections
        processed_image = self._apply_specific_color_corrections(processed_image)

        return processed_image

    def process_image_with_target_size(
        self, image: QImage, target_width: int, target_height: int
    ) -> QImage:
        """
        Optimized image processing: scale first, then apply color corrections.

        This method provides significant performance improvements by applying
        color corrections to smaller scaled images instead of full-resolution originals.

        Args:
            image: Source QImage at original resolution
            target_width: Target width for final image
            target_height: Target height for final image

        Returns:
            QImage: Color-corrected image at target dimensions
        """
        from PyQt6.QtCore import QElapsedTimer

        total_timer = QElapsedTimer()
        total_timer.start()

        if image.isNull():
            self.logger.warning("Cannot process null image")
            return image

        # Step 1: Scale the image to target dimensions using high-quality scaling
        scale_timer = QElapsedTimer()
        scale_timer.start()

        self.logger.info(
            f"[SCALE] Starting: {image.width()}x{image.height()} -> {target_width}x{target_height}"
        )

        # Use Qt's SmoothTransformation for high-quality downscaling
        scaled_image = image.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        scale_time = scale_timer.elapsed()
        self.logger.info(
            f"[SCALE] Completed in {scale_time}ms -> {scaled_image.width()}x{scaled_image.height()}"
        )

        # Step 2: Apply color corrections to the smaller scaled image
        color_timer = QElapsedTimer()
        color_timer.start()

        self.logger.info(
            f"[COLOR] Starting corrections on {scaled_image.width()}x{scaled_image.height()} image"
        )

        # Convert to appropriate format for color manipulation
        try:
            if (
                self.use_high_bit_depth
                and scaled_image.format() != self.high_bit_depth_format
            ):
                processed_image = scaled_image.convertToFormat(
                    self.high_bit_depth_format
                )
            else:
                processed_image = scaled_image.convertToFormat(self.standard_format)
        except Exception as e:
            self.logger.warning(
                f"Error converting scaled image format: {e}. Using original format."
            )
            processed_image = scaled_image.copy()

        # Apply gamma correction if needed
        gamma_timer = QElapsedTimer()
        gamma_timer.start()
        if self.gamma_correction != 1.0:
            self.logger.info(
                f"[COLOR] Applying gamma correction ({self.gamma_correction})"
            )
            processed_image = self._apply_gamma_correction(
                processed_image, self.gamma_correction
            )
            gamma_time = gamma_timer.elapsed()
            self.logger.info(f"[COLOR] Gamma correction completed in {gamma_time}ms")
        else:
            self.logger.info(f"[COLOR] Skipping gamma correction (factor = 1.0)")

        # REMOVED: Red channel enhancement (was causing gray-to-red color bleeding)
        # red_timer = QElapsedTimer()
        # red_timer.start()
        # if self.enhance_red_channel != 1.0:
        #     self.logger.info(
        #         f"[COLOR] Applying red enhancement ({self.enhance_red_channel})"
        #     )
        #     processed_image = self._enhance_color_channel(
        #         processed_image, channel=0, factor=self.enhance_red_channel
        #     )
        #     red_time = red_timer.elapsed()
        #     self.logger.info(f"[COLOR] Red enhancement completed in {red_time}ms")
        # else:
        #     self.logger.info(f"[COLOR] Skipping red enhancement (factor = 1.0)")
        self.logger.info(f"[COLOR] Red enhancement disabled to prevent color bleeding")

        # Apply specific color corrections
        specific_timer = QElapsedTimer()
        specific_timer.start()
        self.logger.info(
            f"[COLOR] Applying ULTRA-PRECISE color corrections ({len(self.color_correction)} mappings) with tolerance=2"
        )
        processed_image = self._apply_specific_color_corrections(processed_image)
        specific_time = specific_timer.elapsed()
        self.logger.info(f"[COLOR] Specific corrections completed in {specific_time}ms")

        color_time = color_timer.elapsed()
        total_time = total_timer.elapsed()
        self.logger.info(f"[COLOR] Total color processing: {color_time}ms")
        self.logger.info(
            f"[TOTAL] process_image_with_target_size completed in {total_time}ms"
        )

        return processed_image

    def _apply_gamma_correction(self, image: QImage, gamma: float) -> QImage:
        """
        Apply gamma correction to an image with optimized processing.

        Args:
            image: Source QImage
            gamma: Gamma correction factor

        Returns:
            QImage: Gamma-corrected QImage
        """
        if gamma == 1.0 or image.isNull():
            return image

        # Create a copy of the image to avoid modifying the original
        result = image.copy()

        # Pre-compute gamma lookup table for faster processing
        gamma_inv = 1.0 / gamma
        gamma_lut = [int(255 * pow(i / 255.0, gamma_inv)) for i in range(256)]

        # Optimized pixel processing
        width = image.width()
        height = image.height()

        # Process pixels in chunks for better cache locality
        chunk_size = 64

        for chunk_y in range(0, height, chunk_size):
            chunk_end_y = min(chunk_y + chunk_size, height)

            for chunk_x in range(0, width, chunk_size):
                chunk_end_x = min(chunk_x + chunk_size, width)

                # Process chunk
                for y in range(chunk_y, chunk_end_y):
                    for x in range(chunk_x, chunk_end_x):
                        pixel_rgb = image.pixel(x, y)

                        # Extract RGB components using bit operations
                        r = (pixel_rgb >> 16) & 0xFF
                        g = (pixel_rgb >> 8) & 0xFF
                        b = pixel_rgb & 0xFF
                        a = (pixel_rgb >> 24) & 0xFF

                        # Apply gamma correction using lookup table
                        corrected_r = gamma_lut[r]
                        corrected_g = gamma_lut[g]
                        corrected_b = gamma_lut[b]

                        # Set corrected pixel
                        result.setPixel(
                            x,
                            y,
                            QColor(corrected_r, corrected_g, corrected_b, a).rgba(),
                        )

        return result

    def _enhance_color_channel(
        self, image: QImage, channel: int, factor: float
    ) -> QImage:
        """
        Enhance a specific color channel with optimized processing.

        Args:
            image: Source QImage
            channel: Color channel index (0=R, 1=G, 2=B)
            factor: Enhancement factor

        Returns:
            QImage: Channel-enhanced QImage
        """
        if factor == 1.0 or image.isNull():
            return image

        # Create a copy of the image to avoid modifying the original
        result = image.copy()

        # Pre-compute enhancement lookup table for the target channel
        enhancement_lut = [min(255, int(i * factor)) for i in range(256)]

        # Optimized pixel processing
        width = image.width()
        height = image.height()

        # Process pixels in chunks for better cache locality
        chunk_size = 64

        for chunk_y in range(0, height, chunk_size):
            chunk_end_y = min(chunk_y + chunk_size, height)

            for chunk_x in range(0, width, chunk_size):
                chunk_end_x = min(chunk_x + chunk_size, width)

                # Process chunk
                for y in range(chunk_y, chunk_end_y):
                    for x in range(chunk_x, chunk_end_x):
                        pixel_rgb = image.pixel(x, y)

                        # Extract RGB components using bit operations
                        r = (pixel_rgb >> 16) & 0xFF
                        g = (pixel_rgb >> 8) & 0xFF
                        b = pixel_rgb & 0xFF
                        a = (pixel_rgb >> 24) & 0xFF

                        # Apply enhancement to the specified channel
                        if channel == 0:  # Red
                            r = enhancement_lut[r]
                        elif channel == 1:  # Green
                            g = enhancement_lut[g]
                        elif channel == 2:  # Blue
                            b = enhancement_lut[b]

                        # Set enhanced pixel
                        result.setPixel(x, y, QColor(r, g, b, a).rgba())

        return result

    def _apply_specific_color_corrections(self, image: QImage) -> QImage:
        """
        Apply specific color corrections to an image with optimized pixel processing.

        Args:
            image: Source QImage

        Returns:
            QImage: Color-corrected QImage
        """
        if not self.color_correction or image.isNull():
            return image

        # Create a copy of the image to avoid modifying the original
        result = image.copy()

        # Pre-compute color map with RGB values for faster lookup
        color_map = {}
        tolerance_squared = (
            2 * 2
        )  # ULTRA-PRECISE tolerance for exact color matching (was 8, now 2)

        for hex_color, corrected_hex in self.color_correction.items():
            if hex_color.startswith("#") and corrected_hex.startswith("#"):
                try:
                    original = QColor(hex_color)
                    corrected = QColor(corrected_hex)
                    # Store as tuple for faster access
                    color_map[original.rgb()] = (
                        corrected.red(),
                        corrected.green(),
                        corrected.blue(),
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Invalid color conversion: {hex_color} -> {corrected_hex}: {e}"
                    )

        if not color_map:
            return result

        # Optimized pixel processing using direct pixel access
        width = image.width()
        height = image.height()

        # Process pixels in chunks for better cache locality
        chunk_size = 64  # Process 64x64 pixel chunks

        for chunk_y in range(0, height, chunk_size):
            chunk_end_y = min(chunk_y + chunk_size, height)

            for chunk_x in range(0, width, chunk_size):
                chunk_end_x = min(chunk_x + chunk_size, width)

                # Process chunk
                for y in range(chunk_y, chunk_end_y):
                    for x in range(chunk_x, chunk_end_x):
                        pixel_rgb = image.pixel(x, y)

                        # PRIORITY 1: Fast exact match first (most common case - ZERO tolerance)
                        if pixel_rgb in color_map:
                            corrected_rgb = color_map[pixel_rgb]
                            # EXACT MATCH: Apply correction immediately (no additional validation needed)
                            result.setPixel(
                                x,
                                y,
                                QColor(
                                    corrected_rgb[0],
                                    corrected_rgb[1],
                                    corrected_rgb[2],
                                    (pixel_rgb >> 24) & 0xFF,
                                ).rgba(),
                            )
                            continue

                        # Tolerance-based matching only if exact match fails
                        pixel_color = QColor(pixel_rgb)
                        pixel_r, pixel_g, pixel_b = (
                            pixel_color.red(),
                            pixel_color.green(),
                            pixel_color.blue(),
                        )

                        for original_rgb, corrected_rgb in color_map.items():
                            original_color = QColor(original_rgb)
                            orig_r, orig_g, orig_b = (
                                original_color.red(),
                                original_color.green(),
                                original_color.blue(),
                            )

                            # Fast squared distance calculation
                            distance_squared = (
                                (pixel_r - orig_r) ** 2
                                + (pixel_g - orig_g) ** 2
                                + (pixel_b - orig_b) ** 2
                            )

                            if distance_squared < tolerance_squared:
                                # SAFETY CHECK: Only apply red corrections to pixels that are actually red-ish
                                # Prevent gray/neutral colors from being affected
                                if self._is_red_correction(
                                    original_rgb
                                ) and self._is_reddish_pixel(pixel_r, pixel_g, pixel_b):
                                    result.setPixel(
                                        x,
                                        y,
                                        QColor(
                                            corrected_rgb[0],
                                            corrected_rgb[1],
                                            corrected_rgb[2],
                                            pixel_color.alpha(),
                                        ).rgba(),
                                    )
                                elif not self._is_red_correction(original_rgb):
                                    # Non-red corrections can be applied normally
                                    result.setPixel(
                                        x,
                                        y,
                                        QColor(
                                            corrected_rgb[0],
                                            corrected_rgb[1],
                                            corrected_rgb[2],
                                            pixel_color.alpha(),
                                        ).rgba(),
                                    )
                                break

        return result

    def _is_red_correction(self, original_rgb: int) -> bool:
        """Check if this is a red color correction (to prevent affecting grays)."""
        original_color = QColor(original_rgb)
        r, g, b = original_color.red(), original_color.green(), original_color.blue()

        # STRICT: Check if the original color is predominantly red (stricter thresholds)
        return r > 220 and r > g + 80 and r > b + 80

    def _is_reddish_pixel(self, r: int, g: int, b: int) -> bool:
        """Check if a pixel is actually reddish (to prevent gray pixels from being affected)."""
        # ULTRA-STRICT: Pixel must be predominantly red and definitely not gray/neutral
        is_red_dominant = (
            r > g + 50 and r > b + 50
        )  # Red is MUCH higher than green/blue (was +20, now +50)
        is_not_gray = (
            abs(r - g) > 30 or abs(r - b) > 30 or abs(g - b) > 30
        )  # Definitely not neutral gray (was >15, now >30)
        has_sufficient_red = r > 180  # Has high red component (was >100, now >180)
        is_definitely_red = r > 200 and g < 100 and b < 100  # Additional red check

        return (
            is_red_dominant and is_not_gray and has_sufficient_red and is_definitely_red
        )

    def _color_distance(self, color1: QColor, color2: QColor) -> float:
        """
        Calculate the Euclidean distance between two colors in RGB space.

        Args:
            color1: First color
            color2: Second color

        Returns:
            float: Color distance
        """
        return (
            (color1.red() - color2.red()) ** 2
            + (color1.green() - color2.green()) ** 2
            + (color1.blue() - color2.blue()) ** 2
        ) ** 0.5
