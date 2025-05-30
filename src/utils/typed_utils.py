"""
Typed utility functions to improve type safety throughout the application.

This module provides properly typed versions of common utility functions
that were previously untyped or poorly typed.
"""

from typing import TypeVar, Optional, Union, Dict, List, Any, Callable, Tuple
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize
import logging

from .sizeable import Sizeable
from .typed_event_handler import TypedEventHandler

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

logger = logging.getLogger(__name__)


def calc_font_size(
    parent_height: int,
    factor: float = 0.03,
    min_size: int = 10,
    max_size: Optional[int] = None,
) -> int:
    """
    Calculate font size based on parent height with proper type safety.

    Args:
        parent_height: Height of the parent widget in pixels
        factor: Scaling factor (default: 0.03)
        min_size: Minimum font size (default: 10)
        max_size: Maximum font size (optional)

    Returns:
        Calculated font size in points

    Raises:
        ValueError: If parent_height is negative or factor is not positive
    """
    if parent_height < 0:
        raise ValueError("Parent height cannot be negative")

    if factor <= 0:
        raise ValueError("Factor must be positive")

    calculated_size = max(int(parent_height * factor), min_size)

    if max_size is not None:
        calculated_size = min(calculated_size, max_size)

    return calculated_size


def calc_label_size(text: str, font: QFont) -> Tuple[int, int]:
    """
    Calculate the size needed for a text label with proper type safety.

    Args:
        text: The text to measure
        font: The font to use for measurement

    Returns:
        Tuple of (width, height) in pixels

    Raises:
        ValueError: If text is empty or font is invalid
    """
    if not text:
        raise ValueError("Text cannot be empty")

    if not font or not font.family():
        raise ValueError("Font must be valid")

    from PyQt6.QtGui import QFontMetrics

    metrics = QFontMetrics(font)
    width = metrics.horizontalAdvance(text)
    height = metrics.height()

    return (width, height)


def safe_get_dict_value(
    dictionary: Dict[K, V],
    key: K,
    default: Optional[V] = None,
    expected_type: Optional[type] = None,
) -> Optional[V]:
    """
    Safely get a value from a dictionary with type checking.

    Args:
        dictionary: The dictionary to search
        key: The key to look for
        default: Default value if key not found
        expected_type: Expected type of the value (optional validation)

    Returns:
        The value or default

    Raises:
        TypeError: If the value is not of the expected type
    """
    if not isinstance(dictionary, dict):
        logger.warning(f"Expected dict, got {type(dictionary)}")
        return default

    value = dictionary.get(key, default)

    if expected_type is not None and value is not None:
        if not isinstance(value, expected_type):
            logger.error(
                f"Value for key '{key}' is {type(value)}, expected {expected_type}"
            )
            raise TypeError(
                f"Value for key '{key}' is {type(value)}, expected {expected_type}"
            )

    return value


def safe_cast(
    value: Any, target_type: type, default: Optional[T] = None
) -> Optional[T]:
    """
    Safely cast a value to a target type.

    Args:
        value: The value to cast
        target_type: The target type
        default: Default value if casting fails

    Returns:
        The cast value or default
    """
    if value is None:
        return default

    try:
        if target_type == bool:
            # Special handling for boolean conversion
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)

        return target_type(value)

    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to cast {value} to {target_type}: {e}")
        return default


def validate_widget_size(widget: QWidget, min_size: Optional[QSize] = None) -> bool:
    """
    Validate that a widget has a reasonable size.

    Args:
        widget: The widget to validate
        min_size: Minimum acceptable size (optional)

    Returns:
        True if size is valid, False otherwise
    """
    if not widget:
        return False

    size = widget.size()

    if size.width() <= 0 or size.height() <= 0:
        return False

    if min_size is not None:
        if size.width() < min_size.width() or size.height() < min_size.height():
            return False

    return True


def create_safe_callback(
    callback: Callable[..., Any],
    error_handler: Optional[Callable[[Exception], None]] = None,
) -> Callable[..., Optional[Any]]:
    """
    Create a safe wrapper around a callback that handles exceptions.

    Args:
        callback: The callback function to wrap
        error_handler: Optional error handler function

    Returns:
        A safe wrapper function
    """

    def safe_wrapper(*args, **kwargs) -> Optional[Any]:
        try:
            return callback(*args, **kwargs)
        except Exception as e:
            if error_handler:
                error_handler(e)
            else:
                logger.error(f"Error in callback {callback.__name__}: {e}")
            return None

    return safe_wrapper


def ensure_list(value: Union[T, List[T]]) -> List[T]:
    """
    Ensure a value is a list.

    Args:
        value: A single value or list of values

    Returns:
        A list containing the value(s)
    """
    if isinstance(value, list):
        return value
    return [value]


def filter_none_values(dictionary: Dict[K, Optional[V]]) -> Dict[K, V]:
    """
    Filter out None values from a dictionary.

    Args:
        dictionary: Dictionary that may contain None values

    Returns:
        Dictionary with None values removed
    """
    return {k: v for k, v in dictionary.items() if v is not None}


def merge_dicts_safely(*dicts: Dict[K, V]) -> Dict[K, V]:
    """
    Safely merge multiple dictionaries.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result: Dict[K, V] = {}

    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
        else:
            logger.warning(f"Skipping non-dict value in merge: {type(d)}")

    return result
