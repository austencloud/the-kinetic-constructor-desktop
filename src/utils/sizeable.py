from typing import Protocol, runtime_checkable


@runtime_checkable
class Sizeable(Protocol):
    def width(self) -> int: ...

    def height(self) -> int: ...
