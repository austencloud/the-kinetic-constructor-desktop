from typing import TYPE_CHECKING, List, Dict, Tuple, Optional, Any
from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap
import logging


from .placeholder_widget import SequenceCardPlaceholder

if TYPE_CHECKING:
    from main_window.main_widget.sequence_card_tab.tab import SequenceCardTab


class ProgressiveLayoutManager(QObject):
    """
    Manages placeholder-based progressive loading for sequence generation.

    This manager:
    1. Pre-calculates the required number of pages based on batch size
    2. Creates pages with placeholder widgets in correct positions
    3. Replaces placeholders with actual sequence cards as they complete
    4. Maintains the existing page layout structure to avoid duplication bugs
    """

    # Signals
    layout_initialized = pyqtSignal(int)  # Emits number of pages created
    placeholder_replaced = pyqtSignal(
        str, object
    )  # Emits placeholder_id and sequence_data
    all_placeholders_replaced = pyqtSignal()

    def __init__(self, sequence_card_tab: "SequenceCardTab"):
        super().__init__()
        self.sequence_card_tab = sequence_card_tab
        self.logger = logging.getLogger(__name__)

        # Track placeholders and their positions
        self.placeholders: Dict[str, SequenceCardPlaceholder] = {}
        self.placeholder_positions: Dict[str, Tuple[int, int, int]] = (
            {}
        )  # placeholder_id -> (page_idx, row, col)
        self.pages: List[QWidget] = []
        self.sequences_per_page = 0
        self.total_expected_sequences = 0
        self.completed_sequences = 0

        # Track which placeholders have been replaced
        self.replaced_placeholders: set = set()

    def calculate_layout_requirements(self, batch_size: int) -> Tuple[int, int]:
        """
        Calculate how many pages and sequences per page are needed.

        Args:
            batch_size: Number of sequences to generate

        Returns:
            Tuple[int, int]: (number_of_pages, sequences_per_page)
        """
        try:
            # Get grid dimensions from page factory
            page_factory = self.sequence_card_tab.page_factory
            rows = page_factory.rows
            cols = page_factory.columns
            sequences_per_page = rows * cols

            # Calculate number of pages needed
            number_of_pages = (
                batch_size + sequences_per_page - 1
            ) // sequences_per_page

            self.logger.info(
                f"Layout calculation: {batch_size} sequences, "
                f"{rows}x{cols} grid ({sequences_per_page} per page), "
                f"{number_of_pages} pages needed"
            )

            return number_of_pages, sequences_per_page

        except Exception as e:
            self.logger.error(f"Error calculating layout requirements: {e}")
            # Fallback to safe defaults
            return 1, 6

    def initialize_progressive_layout(self, batch_size: int) -> bool:
        """
        Initialize the progressive layout with placeholders.

        Args:
            batch_size: Number of sequences that will be generated

        Returns:
            bool: True if initialization successful
        """
        try:
            self.total_expected_sequences = batch_size
            self.completed_sequences = 0
            self.replaced_placeholders.clear()

            # Calculate layout requirements
            num_pages, sequences_per_page = self.calculate_layout_requirements(
                batch_size
            )
            self.sequences_per_page = sequences_per_page

            # Clear existing state
            self._cleanup_existing_layout()

            # Create pages with placeholders
            self._create_pages_with_placeholders(num_pages, batch_size)

            # Display the pages using the existing display system
            self._display_placeholder_pages()

            self.layout_initialized.emit(num_pages)
            self.logger.info(
                f"Progressive layout initialized: {num_pages} pages, {batch_size} placeholders"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error initializing progressive layout: {e}")
            return False

    def _cleanup_existing_layout(self):
        """Clean up any existing placeholders and pages."""
        # Clean up existing placeholders
        for placeholder in self.placeholders.values():
            placeholder.cleanup()

        self.placeholders.clear()
        self.placeholder_positions.clear()
        self.pages.clear()

    def _create_pages_with_placeholders(self, num_pages: int, total_sequences: int):
        """Create the required pages with placeholder widgets."""
        page_factory = self.sequence_card_tab.page_factory

        for page_idx in range(num_pages):
            # Create a new page using the existing page factory
            page = page_factory.create_page()
            self.pages.append(page)

            # Get the grid layout from the page
            grid_layout = page.layout()
            if not isinstance(grid_layout, QGridLayout):
                self.logger.error(f"Page {page_idx} does not have a QGridLayout")
                continue

            # Calculate how many sequences go on this page
            start_sequence = page_idx * self.sequences_per_page
            end_sequence = min(
                start_sequence + self.sequences_per_page, total_sequences
            )
            sequences_on_this_page = end_sequence - start_sequence

            # Get grid positions for this page
            grid_positions = page_factory.get_grid_positions()

            # Add placeholders to the grid
            for i in range(sequences_on_this_page):
                if i >= len(grid_positions):
                    break

                row, col = grid_positions[i]
                placeholder_id = f"page_{page_idx}_pos_{i}"

                # Create placeholder widget with correct dimensions
                placeholder = SequenceCardPlaceholder(placeholder_id)
                placeholder.replace_requested.connect(
                    self._on_placeholder_replace_requested
                )

                # Set placeholder size to match the printable system's cell size
                cell_size = page_factory.get_cell_size()
                placeholder.setFixedSize(cell_size)

                # Add to grid layout
                grid_layout.addWidget(
                    placeholder, row, col, Qt.AlignmentFlag.AlignCenter
                )

                # Track the placeholder
                self.placeholders[placeholder_id] = placeholder
                self.placeholder_positions[placeholder_id] = (page_idx, row, col)

                self.logger.debug(
                    f"Created placeholder {placeholder_id} at page {page_idx}, position ({row}, {col})"
                )

    def _display_placeholder_pages(self):
        """Display the pages with placeholders using the existing display system."""
        try:
            # Clear the content area
            self.sequence_card_tab.ui_manager.clear_content_area()

            # Add pages to the scroll layout
            for page in self.pages:
                self.sequence_card_tab.content_area.scroll_layout.addWidget(page)

            self.logger.debug(f"Displayed {len(self.pages)} placeholder pages")

        except Exception as e:
            self.logger.error(f"Error displaying placeholder pages: {e}")

    def replace_placeholder_with_sequence(self, sequence_data: Any) -> bool:
        """
        Replace the next available placeholder with a sequence card.

        Args:
            sequence_data: The generated sequence data

        Returns:
            bool: True if replacement successful
        """
        try:
            # Find the next placeholder to replace (in order)
            placeholder_id = self._get_next_placeholder_id()
            if not placeholder_id:
                self.logger.warning("No available placeholder to replace")
                return False

            placeholder = self.placeholders.get(placeholder_id)
            if not placeholder:
                self.logger.error(f"Placeholder {placeholder_id} not found")
                return False

            # Get position information
            page_idx, row, col = self.placeholder_positions[placeholder_id]
            page = self.pages[page_idx]
            grid_layout = page.layout()

            # Create the actual sequence image label (compatible with printable system)
            sequence_image_label = self._create_sequence_image_label(sequence_data)

            # Replace the placeholder with the sequence image label
            grid_layout.removeWidget(placeholder)
            placeholder.cleanup()
            placeholder.deleteLater()

            grid_layout.addWidget(
                sequence_image_label, row, col, Qt.AlignmentFlag.AlignCenter
            )

            # Update tracking
            self.replaced_placeholders.add(placeholder_id)
            self.completed_sequences += 1

            self.placeholder_replaced.emit(placeholder_id, sequence_data)
            self.logger.debug(
                f"Replaced placeholder {placeholder_id} with sequence {getattr(sequence_data, 'id', 'unknown')}"
            )

            # Check if all placeholders have been replaced
            if self.completed_sequences >= self.total_expected_sequences:
                self.all_placeholders_replaced.emit()
                self.logger.info(
                    "All placeholders have been replaced with sequence cards"
                )

            return True

        except Exception as e:
            self.logger.error(f"Error replacing placeholder with sequence: {e}")
            return False

    def _get_next_placeholder_id(self) -> Optional[str]:
        """Get the ID of the next placeholder to replace (in order)."""
        for page_idx in range(len(self.pages)):
            for i in range(self.sequences_per_page):
                placeholder_id = f"page_{page_idx}_pos_{i}"
                if (
                    placeholder_id in self.placeholders
                    and placeholder_id not in self.replaced_placeholders
                ):
                    return placeholder_id
        return None

    def _create_sequence_image_label(self, sequence_data: Any) -> QWidget:
        """
        Create a simple image label widget compatible with the printable system.
        This creates the exact same type of widget as the existing printable displayer.
        """
        try:
            # Generate the sequence image using the existing image generation pipeline
            pixmap = self._generate_sequence_image(sequence_data)

            if not pixmap or pixmap.isNull():
                # Create error placeholder if image generation fails
                return self._create_error_label()

            # Create simple image label directly (compatible with printable system)
            image_label = self._create_simple_image_label(pixmap, sequence_data)

            return image_label

        except Exception as e:
            self.logger.error(f"Error creating sequence image label: {e}")
            return self._create_error_label()

    def _generate_sequence_image(self, sequence_data: Any) -> QPixmap:
        """Generate page-optimized sequence image for fast progressive loading."""
        try:
            # Get target cell size for page-optimized generation
            cell_size = self.sequence_card_tab.page_factory.get_cell_size()

            # Generate lightweight, page-optimized image directly at target size
            pixmap = self._generate_page_optimized_image(sequence_data, cell_size)

            if pixmap and not pixmap.isNull():
                return pixmap
            else:
                # Fallback to error placeholder
                self.logger.warning(
                    f"Failed to generate page-optimized image for {getattr(sequence_data, 'id', 'unknown')}"
                )
                return self._create_error_pixmap(cell_size)

        except Exception as e:
            self.logger.error(f"Error generating sequence image: {e}")
            # Return error placeholder with correct size
            cell_size = self.sequence_card_tab.page_factory.get_cell_size()
            return self._create_error_pixmap(cell_size)

    def _generate_page_optimized_image(
        self, sequence_data: Any, target_size: QSize
    ) -> QPixmap:
        """
        Generate a lightweight, page-optimized image directly at target display size.

        This creates images optimized for fast progressive loading:
        - Generated at exact display resolution (no scaling needed)
        - Minimal metadata and decorations for speed
        - Optimized for page layout display, not dictionary storage

        Args:
            sequence_data: The sequence data to generate image for
            target_size: Target size for the generated image

        Returns:
            QPixmap: Page-optimized image at target size
        """
        try:
            # Use the image exporter but with page-optimized settings
            if not self.sequence_card_tab.image_exporter:
                self.logger.error(
                    "No image exporter available for page-optimized generation"
                )
                return self._create_error_pixmap(target_size)

            # Load sequence into the temp beat frame
            self.sequence_card_tab.image_exporter.temp_beat_frame.load_sequence(
                sequence_data.sequence_data
            )

            # Calculate optimal scale factor for target size
            scale_factor = self._calculate_optimal_scale_factor(target_size)

            # Page-optimized generation options (balanced for speed and visibility)
            page_optimized_options = {
                "add_beat_numbers": True,  # Keep for identification
                "add_reversal_symbols": False,  # Skip for speed
                "add_user_info": True,  # Keep for progressive loading
                "add_word": True,  # Keep word for identification
                "add_difficulty_level": True,  # Keep for identification
                "include_start_position": True,  # Keep start position for progressive loading
                "combined_grids": False,
                "additional_height_top": 0,  # Will be calculated by HeightDeterminer
                "additional_height_bottom": 0,  # Will be calculated by HeightDeterminer
                "dynamic_scale_factor": scale_factor,  # NEW: Dynamic scaling
            }

            self.logger.info(
                f"🎨 Page-optimized options: scale={scale_factor:.3f}, word={page_optimized_options['add_word']}"
            )

            # Generate image at target size
            qimage = self.sequence_card_tab.image_exporter.export_manager.image_creator.create_sequence_image(
                sequence_data.sequence_data,
                page_optimized_options,
                dictionary=False,  # Not for dictionary storage
                fullscreen_preview=False,
                override_word=sequence_data.word,
            )

            if qimage and not qimage.isNull():
                # Convert to pixmap - should already be at correct size due to scale factor
                pixmap = QPixmap.fromImage(qimage)

                self.logger.info(
                    f"✅ Generated page-optimized image: {pixmap.size()} for target {target_size}"
                )

                # Only scale if there's a significant size difference (avoid unnecessary scaling)
                size_diff_width = abs(pixmap.width() - target_size.width())
                size_diff_height = abs(pixmap.height() - target_size.height())

                if size_diff_width > 10 or size_diff_height > 10:
                    self.logger.warning(
                        f"⚠️ Image size mismatch, scaling: {pixmap.size()} → {target_size}"
                    )
                    pixmap = pixmap.scaled(
                        target_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,  # High quality scaling when needed
                    )
                    self.logger.info(f"🔄 Scaled to: {pixmap.size()}")

                return pixmap
            else:
                self.logger.warning(
                    "Page-optimized image generation returned null image"
                )
                return self._create_error_pixmap(target_size)

        except Exception as e:
            self.logger.error(f"Error in page-optimized image generation: {e}")
            return self._create_error_pixmap(target_size)

    def _create_error_pixmap(self, size: QSize) -> QPixmap:
        """Create an error pixmap at the specified size."""
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt

        error_pixmap = QPixmap(size)
        error_pixmap.fill(QColor(240, 240, 240))

        painter = QPainter(error_pixmap)
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Arial", max(8, size.height() // 20)))
        painter.drawText(
            error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error\nLoading\nImage"
        )
        painter.end()

        return error_pixmap

    def _calculate_optimal_scale_factor(self, target_size: QSize) -> float:
        """
        Calculate the optimal scale factor using reverse-calculation approach.

        This method:
        1. Determines what the full-size image dimensions would be with standard 950x950 pictographs
        2. Calculates the ratio between available page space and full-size dimensions
        3. Returns a scale factor that ensures proper proportional scaling of all elements

        Args:
            target_size: Target size for the final image (from page_factory.get_cell_size())

        Returns:
            float: Scale factor to apply consistently across all image creator components
        """
        try:
            # Base pictograph size is hardcoded at 950x950 throughout the system
            BASE_PICTOGRAPH_SIZE = 950

            # Step 1: Get the actual layout that would be used for image generation
            try:
                # Use the same layout calculation as the image creator for accuracy
                layout_handler = (
                    self.sequence_card_tab.image_exporter.export_manager.layout_handler
                )
                columns, rows = layout_handler.calculate_layout(
                    16,  # Typical sequence length for progressive loading
                    True,  # Include start position
                )
                self.logger.debug(f"Actual layout from image creator: {columns}x{rows}")
            except Exception as e:
                # Fallback to safe estimates if layout calculation fails
                self.logger.warning(f"Layout calculation failed, using fallback: {e}")
                columns, rows = (
                    5,
                    4,
                )  # Conservative estimate for 16-beat + start position

            # Step 2: Calculate what the full-size image dimensions would be
            # This includes the core pictograph grid plus additional heights for labels
            core_image_width = columns * BASE_PICTOGRAPH_SIZE
            core_image_height = rows * BASE_PICTOGRAPH_SIZE

            # Estimate additional heights that would be added (using standard calculations)
            # These are the heights that HeightDeterminer would add for word/user info
            estimated_additional_height_top = 300  # Standard for word label
            estimated_additional_height_bottom = 150  # Standard for user info

            full_image_width = core_image_width
            full_image_height = (
                core_image_height
                + estimated_additional_height_top
                + estimated_additional_height_bottom
            )

            # Step 3: Calculate scale ratio based on available page space
            # Use width as the primary constraint since it's typically more limiting
            width_scale_ratio = target_size.width() / full_image_width
            height_scale_ratio = target_size.height() / full_image_height

            # Use the smaller ratio to ensure the image fits within the target size
            scale_factor = min(width_scale_ratio, height_scale_ratio)

            # Step 4: Apply safety bounds to prevent extreme scaling
            scale_factor = max(scale_factor, 0.05)  # Minimum 5% to maintain readability
            scale_factor = min(scale_factor, 1.0)  # Maximum 100% to prevent oversizing

            self.logger.info(f"🎯 REVERSE-CALCULATED SCALE FACTOR: {scale_factor:.3f}")
            self.logger.info(
                f"   📐 Layout: {columns}x{rows}, Full size: {full_image_width}x{full_image_height}"
            )
            self.logger.info(
                f"   📏 Target: {target_size}, Ratios: W={width_scale_ratio:.3f}, H={height_scale_ratio:.3f}"
            )

            return scale_factor

        except Exception as e:
            self.logger.error(f"Error in reverse-calculation scale factor: {e}")
            # Fallback to a conservative default that should work in most cases
            return 0.2  # 20% of original size

    def _create_error_label(self) -> QWidget:
        """Create an error label when image generation fails."""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

        # Get cell size from page factory
        cell_size = self.sequence_card_tab.page_factory.get_cell_size()

        # Create error pixmap
        error_pixmap = QPixmap(cell_size)
        error_pixmap.fill(QColor(240, 240, 240))

        painter = QPainter(error_pixmap)
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(
            error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error\nLoading\nImage"
        )
        painter.end()

        # Create label
        error_label = QLabel()
        error_label.setPixmap(error_pixmap)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setFixedSize(error_pixmap.size())

        return error_label

    def _convert_sequence_data_to_dict(self, sequence_data: Any) -> dict:
        """Convert GeneratedSequenceData object to dictionary format."""
        try:
            if hasattr(sequence_data, "__dict__"):
                # Convert object to dictionary
                sequence_dict = {}

                # Extract common attributes
                if hasattr(sequence_data, "word"):
                    sequence_dict["word"] = sequence_data.word
                if hasattr(sequence_data, "path"):
                    sequence_dict["path"] = sequence_data.path
                if hasattr(sequence_data, "metadata"):
                    sequence_dict["metadata"] = sequence_data.metadata
                elif hasattr(sequence_data, "sequence_length"):
                    sequence_dict["metadata"] = {
                        "sequence_length": sequence_data.sequence_length
                    }

                return sequence_dict
            elif isinstance(sequence_data, dict):
                # Already a dictionary
                return sequence_data
            else:
                # Fallback for unknown types
                return {}

        except Exception as e:
            self.logger.error(f"Error converting sequence data to dict: {e}")
            return {}

    def _create_simple_image_label(self, pixmap: QPixmap, sequence_data: Any):
        """Create a simple image label matching the printable system's output."""
        from PyQt6.QtWidgets import QLabel, QSizePolicy
        from PyQt6.QtCore import Qt

        # Create a simple image label without complex metadata handling
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setScaledContents(False)

        # Set size policy to match printable system
        image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        image_label.setFixedSize(pixmap.size())

        # Store minimal metadata safely
        try:
            if hasattr(sequence_data, "word") and sequence_data.word:
                image_label.setProperty("sequence_word", sequence_data.word)
            if hasattr(sequence_data, "sequence_length"):
                image_label.setProperty(
                    "sequence_length", sequence_data.sequence_length
                )
        except Exception as e:
            self.logger.debug(f"Could not set metadata properties: {e}")

        return image_label

    def _on_placeholder_replace_requested(self, sequence_card_widget):
        """Handle placeholder replacement requests."""
        # This is called when a placeholder requests to be replaced
        # The actual replacement logic is handled by replace_placeholder_with_sequence
        pass

    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        return {
            "total_expected": self.total_expected_sequences,
            "completed": self.completed_sequences,
            "remaining": self.total_expected_sequences - self.completed_sequences,
            "progress_percentage": (
                self.completed_sequences / max(1, self.total_expected_sequences)
            )
            * 100,
            "pages_created": len(self.pages),
            "placeholders_remaining": len(self.placeholders)
            - len(self.replaced_placeholders),
        }

    def cleanup(self):
        """Clean up all resources."""
        self._cleanup_existing_layout()
        self.total_expected_sequences = 0
        self.completed_sequences = 0
