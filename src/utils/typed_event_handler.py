from typing import TypeVar, Generic, Callable, Optional
import logging

T = TypeVar("T")
logger = logging.getLogger(__name__)


class TypedEventHandler(Generic[T]):
    def __init__(self, handler: Callable[[T], None]):
        self._handler = handler
        self._enabled = True

    def handle(self, event: T) -> None:
        if not self._enabled:
            return

        try:
            self._handler(event)
        except Exception as e:
            logger.error(f"Error handling event {type(event)}: {e}")

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled
