from typing import LiteralString
from PyQt6.QtWidgets import (
    QProgressBar,
    QVBoxLayout,
    QLabel,
    QWidget,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor


class RainbowProgressBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_value = 0
        self._setup_components()
        self._setup_layout()
        self._setup_animations()
        self._apply_glassmorphism_effects()

    def _setup_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.loading_label)
        layout.addStretch(1)
        layout.addWidget(self.percentage_label)
        layout.addStretch(1)
        layout.addWidget(self.progress_bar)
        layout.setContentsMargins(20, 20, 20, 20)  # Increased margins for glassmorphism
        layout.setSpacing(10)  # Increased spacing for better visual hierarchy
        self.setLayout(layout)

    def _setup_components(self) -> None:
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(self._get_modern_stylesheet())

        self.loading_label = QLabel("Loading...", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.percentage_label = QLabel("0%", self)
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _setup_animations(self) -> None:
        """Set up smooth animations for progress updates."""
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(300)  # 300ms smooth transition
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _apply_glassmorphism_effects(self) -> None:
        """Apply glassmorphism effects to the progress bar container."""
        # Multi-layered shadow effect for depth
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(20)
        shadow_effect.setXOffset(0)
        shadow_effect.setYOffset(4)
        shadow_effect.setColor(QColor(0, 0, 0, 60))  # Subtle shadow
        self.setGraphicsEffect(shadow_effect)

        # Apply glassmorphism styling to the container
        self.setStyleSheet(
            """
            RainbowProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
            }
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """
        )

    def set_value(self, value) -> None:
        """Set progress value with smooth animation."""
        if value == self._current_value:
            return

        # Ensure monotonic progress (never go backwards)
        if value < self._current_value:
            return

        self._current_value = value

        # Animate to new value
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(value)
        self.progress_animation.start()

        # Update percentage label immediately for responsiveness
        self.percentage_label.setText(f"{value}%")

    def get_value(self) -> int:
        """Get the current progress value."""
        return self._current_value

    def reset(self) -> None:
        """Reset progress to 0."""
        self._current_value = 0
        self.progress_bar.setValue(0)
        self.percentage_label.setText("0%")

    def _get_modern_stylesheet(self) -> LiteralString:
        """Modern 2025 glassmorphism progress bar styling with dynamic gradients."""
        stylesheet = """
            QProgressBar {
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.1);
                height: 12px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 18px;
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 59, 48, 0.9),     /* Modern red */
                    stop:0.15 rgba(255, 149, 0, 0.9),  /* Modern orange */
                    stop:0.3 rgba(255, 204, 0, 0.9),   /* Modern yellow */
                    stop:0.45 rgba(52, 199, 89, 0.9),  /* Modern green */
                    stop:0.6 rgba(0, 122, 255, 0.9),   /* Modern blue */
                    stop:0.75 rgba(88, 86, 214, 0.9),  /* Modern indigo */
                    stop:1 rgba(175, 82, 222, 0.9)     /* Modern violet */
                );
                margin: 1px;
            }
            QProgressBar::chunk:hover {
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 59, 48, 1.0),     /* Brighter on hover */
                    stop:0.15 rgba(255, 149, 0, 1.0),
                    stop:0.3 rgba(255, 204, 0, 1.0),
                    stop:0.45 rgba(52, 199, 89, 1.0),
                    stop:0.6 rgba(0, 122, 255, 1.0),
                    stop:0.75 rgba(88, 86, 214, 1.0),
                    stop:1 rgba(175, 82, 222, 1.0)
                );
            }
        """
        return stylesheet

    def _get_stylesheet(self) -> LiteralString:
        """Legacy method for backward compatibility."""
        return self._get_modern_stylesheet()
