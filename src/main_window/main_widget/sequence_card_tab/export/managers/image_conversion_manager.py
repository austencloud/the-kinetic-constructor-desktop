import io
import numpy as np
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer, Qt
from PIL import Image


class ImageConversionManager:
    def __init__(self):
        self.conversion_stats = {
            "successful_conversions": 0,
            "memory_errors": 0,
            "fallback_conversions": 0,
        }

    def qimage_to_pil(self, qimage: QImage, max_dimension: int = 3000) -> Image.Image:
        try:
            original_width, original_height = qimage.width(), qimage.height()
            scale_factor = self._calculate_scale_factor(
                original_width, original_height, max_dimension
            )

            if scale_factor < 1.0:
                qimage = self._scale_qimage(qimage, scale_factor)

            qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
            width, height = qimage.width(), qimage.height()

            ptr = qimage.bits()
            ptr.setsize(height * width * 4)

            try:
                arr = np.array(ptr, copy=True).reshape((height, width, 4))
                arr = arr[..., [2, 1, 0, 3]]
                pil_image = Image.fromarray(arr, "RGBA")
                arr = None
                self.conversion_stats["successful_conversions"] += 1
                return pil_image

            except MemoryError:
                self.conversion_stats["memory_errors"] += 1
                return self._alternative_conversion(qimage)

        except MemoryError as e:
            return self._handle_memory_error(qimage, max_dimension)

    def _calculate_scale_factor(
        self, width: int, height: int, max_dimension: int
    ) -> float:
        if width <= max_dimension and height <= max_dimension:
            return 1.0

        width_factor = max_dimension / width if width > max_dimension else 1.0
        height_factor = max_dimension / height if height > max_dimension else 1.0
        return min(width_factor, height_factor)

    def _scale_qimage(self, qimage: QImage, scale_factor: float) -> QImage:
        new_width = int(qimage.width() * scale_factor)
        new_height = int(qimage.height() * scale_factor)

        return qimage.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _alternative_conversion(self, qimage: QImage) -> Image.Image:
        try:
            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            qimage.save(buffer, "PNG", quality=100)
            buffer.seek(0)

            pil_image = Image.open(io.BytesIO(buffer.data().data()))
            self.conversion_stats["fallback_conversions"] += 1
            return pil_image.copy()
        except Exception:
            return self._create_error_image()

    def _handle_memory_error(self, qimage: QImage, max_dimension: int) -> Image.Image:
        if max_dimension > 2000:
            return self.qimage_to_pil(qimage, max_dimension=2000)
        elif max_dimension > 1500:
            return self.qimage_to_pil(qimage, max_dimension=1500)
        elif max_dimension > 1000:
            return self.qimage_to_pil(qimage, max_dimension=1000)
        else:
            return self._create_error_image()

    def _create_error_image(self) -> Image.Image:
        return Image.new("RGBA", (400, 300), (255, 0, 0, 128))

    def get_conversion_stats(self) -> dict:
        return self.conversion_stats.copy()
