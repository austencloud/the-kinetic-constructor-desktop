"""
Tests for the turn configuration component.
"""

import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.main_window.main_widget.settings_dialog.ui.codex_exporter.components.turn_config_style_provider import (
    TurnConfigStyleProvider,
)
from src.main_window.main_widget.settings_dialog.ui.codex_exporter.components.grid_mode_selector import (
    GridModeSelector,
)
from src.main_window.main_widget.settings_dialog.ui.codex_exporter.components.turn_slider import (
    TurnSlider,
)
from src.main_window.main_widget.settings_dialog.ui.codex_exporter.components.turn_pair_display import (
    TurnPairDisplay,
)
from src.main_window.main_widget.settings_dialog.ui.codex_exporter.components.generate_all_checkbox import (
    GenerateAllCheckbox,
)
from src.main_window.main_widget.settings_dialog.ui.codex_exporter.components.turn_config_container import (
    TurnConfigContainer,
)


@pytest.fixture
def app():
    """Create a QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # No need to clean up as we're not creating a new app if one exists


@pytest.fixture
def test_widget(app):
    """Create a test widget for testing."""
    from PyQt6.QtWidgets import QWidget

    widget = QWidget()
    widget.resize(800, 600)
    widget.show()
    yield widget
    widget.close()


def test_turn_config_style_provider(test_widget):
    """Test that the TurnConfigStyleProvider can be instantiated."""
    style_provider = TurnConfigStyleProvider(test_widget)
    assert style_provider is not None
    assert style_provider.get_card_style() is not None
    assert style_provider.get_section_title_style() is not None


def test_grid_mode_selector(test_widget):
    """Test that the GridModeSelector can be instantiated."""
    style_provider = TurnConfigStyleProvider(test_widget)
    grid_mode_selector = GridModeSelector(test_widget, style_provider)
    assert grid_mode_selector is not None
    assert grid_mode_selector.get_grid_mode() in ["diamond", "box"]


def test_turn_slider(test_widget):
    """Test that the TurnSlider can be instantiated."""
    style_provider = TurnConfigStyleProvider(test_widget)
    turn_slider = TurnSlider("Test Slider", "#FF0000", test_widget, style_provider, 1.0)
    assert turn_slider is not None
    assert turn_slider.get_value() == 1.0

    # Test setting value
    turn_slider.set_value(2.0)
    assert turn_slider.get_value() == 2.0

    # Test enabling/disabling
    turn_slider.set_enabled(False)
    assert not turn_slider.slider.isEnabled()
    turn_slider.set_enabled(True)
    assert turn_slider.slider.isEnabled()


def test_turn_pair_display(test_widget):
    """Test that the TurnPairDisplay can be instantiated."""
    style_provider = TurnConfigStyleProvider(test_widget)
    turn_pair_display = TurnPairDisplay(test_widget, style_provider, (1.0, 2.0))
    assert turn_pair_display is not None

    # Test updating values
    turn_pair_display.update_values(2.5, 3.0)
    assert "(2.5, 3.0)" in turn_pair_display.pair_value.text()

    # Test enabling/disabling
    turn_pair_display.set_enabled(False)
    assert not turn_pair_display.pair_value.isEnabled()
    turn_pair_display.set_enabled(True)
    assert turn_pair_display.pair_value.isEnabled()


def test_generate_all_checkbox(test_widget):
    """Test that the GenerateAllCheckbox can be instantiated."""
    style_provider = TurnConfigStyleProvider(test_widget)
    checkbox = GenerateAllCheckbox(test_widget, style_provider)
    assert checkbox is not None
    assert not checkbox.is_checked()

    # Test setting checked state
    checkbox.set_checked(True)
    assert checkbox.is_checked()
    checkbox.set_checked(False)
    assert not checkbox.is_checked()


def test_turn_config_container(test_widget):
    """Test that the TurnConfigContainer can be instantiated."""
    turn_config = TurnConfigContainer(test_widget)
    assert turn_config is not None

    # Test getting turn values
    turn_values = turn_config.get_turn_values()
    assert "red_turns" in turn_values
    assert "blue_turns" in turn_values
    assert "generate_all" in turn_values
    assert "grid_mode" in turn_values

    # Test updating sliders state
    turn_config._update_sliders_state(True)
    assert not turn_config.first_turn_slider.slider.isEnabled()
    assert not turn_config.second_turn_slider.slider.isEnabled()

    turn_config._update_sliders_state(False)
    assert turn_config.first_turn_slider.slider.isEnabled()
    assert turn_config.second_turn_slider.slider.isEnabled()
