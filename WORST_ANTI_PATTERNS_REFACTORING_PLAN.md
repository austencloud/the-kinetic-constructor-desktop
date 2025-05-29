# 🔥 Worst Anti-Patterns Refactoring Plan - 2025 Standards

## Executive Summary

This document identifies the most critical anti-patterns in the codebase that violate 2025 coding standards. Each pattern is categorized by severity and includes specific refactoring strategies for systematic elimination.

## 🚨 Critical Severity (Fix Immediately)

### 1. Lambda Closure Capture Anti-Pattern

**Pattern**: Lambda expressions in signal connections capturing variables by closure
**Risk Level**: CRITICAL - Causes memory leaks and race conditions

#### Locations:

- `src/main_window/main_widget/sequence_card_tab/generation/approval_dialog/image_manager.py:36-49`
- Multiple other signal connection points throughout codebase

#### Current Bad Code:

```python
worker.image_generated.connect(
    lambda seq_id, pixmap: self._on_image_generated(seq_id, pixmap, cards),
    Qt.ConnectionType.QueuedConnection,
)
worker.finished.connect(
    lambda seq_id=sequence_data.id: self._on_worker_finished(seq_id),
    Qt.ConnectionType.QueuedConnection,
)
```

#### Refactoring Strategy:

```python
# Option 1: Partial functions
from functools import partial
worker.image_generated.connect(
    partial(self._on_image_generated, cards=cards),
    Qt.ConnectionType.QueuedConnection,
)

# Option 2: Signal mapper pattern
from PyQt6.QtCore import QSignalMapper
self.signal_mapper = QSignalMapper()
self.signal_mapper.mapped[str].connect(self._on_worker_finished)
worker.finished.connect(lambda: self.signal_mapper.map(sequence_data.id))

# Option 3: Wrapper methods (recommended)
def _create_image_handler(self, cards: Dict[str, SequenceCard]):
    def handler(seq_id: str, pixmap: QPixmap):
        self._on_image_generated(seq_id, pixmap, cards)
    return handler

worker.image_generated.connect(
    self._create_image_handler(cards),
    Qt.ConnectionType.QueuedConnection,
)
```

#### Priority: P0 (Fix within 1 week)

---

### 2. Silent Exception Swallowing

**Pattern**: Bare except blocks and silent exception handling
**Risk Level**: CRITICAL - Masks bugs and makes debugging impossible

#### Locations:

- `src/main_window/main_widget/sequence_card_tab/core/cache_manager.py:230`
- Multiple fallback patterns throughout codebase
- Various `except Exception: pass` blocks

#### Current Bad Code:

```python
try:
    # complex operation
except Exception:
    # Silently continue on cache file errors
    pass

except AttributeError:
    pass
```

#### Refactoring Strategy:

```python
# Use Result pattern
from typing import Union, Optional
from dataclasses import dataclass

@dataclass
class Result[T]:
    value: Optional[T] = None
    error: Optional[Exception] = None

    @property
    def is_success(self) -> bool:
        return self.error is None

# Proper error handling
def safe_operation() -> Result[str]:
    try:
        result = complex_operation()
        return Result(value=result)
    except SpecificException as e:
        logger.warning(f"Expected error in operation: {e}")
        return Result(error=e)
    except Exception as e:
        logger.error(f"Unexpected error in operation: {e}")
        return Result(error=e)

# Usage
result = safe_operation()
if result.is_success:
    process_value(result.value)
else:
    handle_error(result.error)
```

#### Priority: P0 (Fix within 1 week)

---

### 3. HasAttr Chain of Doom

**Pattern**: Multiple nested hasattr checks for object traversal
**Risk Level**: HIGH - Violates Tell Don't Ask, brittle coupling

#### Locations:

- All fallback patterns in dependency injection fixes
- Worker access patterns
- Tab access patterns

#### Current Bad Code:

```python
if (
    construct_tab
    and hasattr(construct_tab, "option_picker")
    and hasattr(construct_tab.option_picker, "updater")
):
    construct_tab.option_picker.updater.refresh_options()
```

#### Refactoring Strategy:

```python
# Option 1: Safe navigation utility
class SafeNavigator:
    def __init__(self, obj):
        self._obj = obj

    def get(self, *attrs):
        current = self._obj
        for attr in attrs:
            if not hasattr(current, attr):
                return None
            current = getattr(current, attr)
        return current

    def call(self, *attrs, **kwargs):
        method = self.get(*attrs)
        if callable(method):
            return method(**kwargs)
        return None

# Usage
nav = SafeNavigator(construct_tab)
nav.call("option_picker", "updater", "refresh_options")

# Option 2: Protocol-based interfaces
from typing import Protocol

class OptionUpdater(Protocol):
    def refresh_options(self) -> None: ...

class ConstructTab(Protocol):
    option_picker: OptionUpdater

# Type-safe access
def update_options(tab: Optional[ConstructTab]) -> None:
    if tab and tab.option_picker:
        tab.option_picker.refresh_options()
```

#### Priority: P1 (Fix within 2 weeks)

---

## 🔥 High Severity (Fix Next)

### 4. God Object Anti-Pattern

**Pattern**: Classes with multiple responsibilities
**Risk Level**: HIGH - Violates SRP, unmaintainable

#### Locations:

- `ApprovalDialogImageManager` (image generation + worker management + diagnostics + progress)
- `MainWidget` (UI + coordination + state + event handling)
- Various manager classes

#### Refactoring Strategy:

```python
# Split ApprovalDialogImageManager into focused classes

class ImageGenerationCoordinator:
    def __init__(self, worker_factory: WorkerFactory):
        self._worker_factory = worker_factory
        self._workers: Dict[str, ImageGenerationWorker] = {}

    def start_generation(self, sequences: List[GeneratedSequenceData]) -> None:
        for seq_data in sequences:
            worker = self._worker_factory.create(seq_data)
            self._workers[seq_data.id] = worker
            worker.start()

class ImageResultHandler:
    def __init__(self, card_repository: CardRepository):
        self._cards = card_repository

    def handle_success(self, seq_id: str, pixmap: QPixmap) -> None:
        card = self._cards.get(seq_id)
        if card:
            card.set_image(pixmap)

class DiagnosticsCollector:
    def __init__(self):
        self._diagnostics: Dict[str, dict] = {}

    def collect(self, seq_id: str, data: dict) -> None:
        self._diagnostics[seq_id] = data

# Composed manager
class ImageGenerationManager:
    def __init__(self, coordinator: ImageGenerationCoordinator,
                 handler: ImageResultHandler,
                 diagnostics: DiagnosticsCollector):
        self._coordinator = coordinator
        self._handler = handler
        self._diagnostics = diagnostics
```

#### Priority: P1 (Fix within 2 weeks)

---

### 5. Mutable Default Arguments

**Pattern**: Using mutable objects as default parameters
**Risk Level**: HIGH - Shared state bugs

#### Locations:

- Various utility functions
- Configuration methods
- Factory methods

#### Current Bad Code:

```python
def process_data(items: List[str] = []) -> List[str]:
    items.append("processed")
    return items
```

#### Refactoring Strategy:

```python
def process_data(items: Optional[List[str]] = None) -> List[str]:
    if items is None:
        items = []
    result = items.copy()
    result.append("processed")
    return result
```

#### Priority: P1 (Fix within 2 weeks)

---

## ⚠️ Medium Severity (Address Systematically)

### 6. String-Based Coupling

**Pattern**: Using magic strings for component identification
**Risk Level**: MEDIUM - Brittle refactoring, runtime errors

#### Refactoring Strategy:

```python
# Use enums instead of magic strings
from enum import Enum

class TabType(Enum):
    CONSTRUCT = "construct"
    BROWSE = "browse"
    SEQUENCE_CARD = "sequence_card"
    GENERATE = "generate"

# Type-safe access
def get_tab(tab_type: TabType) -> Optional[Widget]:
    return self.tab_manager.get_tab_widget(tab_type.value)
```

#### Priority: P2 (Fix within 1 month)

---

### 7. Manual Resource Management

**Pattern**: Manual cleanup without context managers
**Risk Level**: MEDIUM - Resource leaks

#### Refactoring Strategy:

```python
# Use context managers
from contextlib import contextmanager

@contextmanager
def worker_lifecycle(worker: ImageGenerationWorker):
    try:
        worker.start()
        yield worker
    finally:
        if worker.isRunning():
            worker.terminate()
            worker.wait(1000)
        worker.deleteLater()

# Usage
with worker_lifecycle(worker) as w:
    # Use worker
    pass  # Automatic cleanup
```

#### Priority: P2 (Fix within 1 month)

---

### 8. Defensive Programming Overload

**Pattern**: Excessive fallback chains
**Risk Level**: MEDIUM - Indicates architectural problems

#### Refactoring Strategy:

```python
# Use dependency injection container
class ServiceContainer:
    def __init__(self):
        self._services: Dict[type, Any] = {}

    def register(self, service_type: type, instance: Any) -> None:
        self._services[service_type] = instance

    def get(self, service_type: type) -> Any:
        service = self._services.get(service_type)
        if service is None:
            raise ServiceNotFound(f"Service {service_type} not registered")
        return service

# Single point of access, no fallbacks needed
container = ServiceContainer()
construct_tab = container.get(ConstructTab)
```

#### Priority: P2 (Fix within 1 month)

---

## 🔧 Systematic Refactoring Plan

### Phase 1: Critical Fixes (Week 1-2)

1. **Lambda Closure Elimination**

   - Audit all signal connections
   - Replace with proper handler methods
   - Add tests for signal behavior

2. **Exception Handling Audit**
   - Replace bare except blocks
   - Implement Result pattern
   - Add proper logging

### Phase 2: Architecture Improvements (Week 3-6)

1. **God Object Decomposition**

   - Split large classes by responsibility
   - Introduce service layer
   - Implement dependency injection

2. **Resource Management**
   - Implement context managers
   - Add automatic cleanup
   - Fix memory leaks

### Phase 3: Code Quality (Week 7-8)

1. **String Coupling Elimination**

   - Replace magic strings with enums
   - Type-safe component access
   - Compile-time error detection

2. **Defensive Code Cleanup**
   - Remove excessive fallbacks
   - Implement proper DI container
   - Simplify access patterns

## 🧪 Testing Strategy

### Each Refactoring Must Include:

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **Regression Tests**: Ensure no functionality loss
4. **Performance Tests**: Verify no performance degradation

### Test Coverage Requirements:

- New code: 90%+ coverage
- Refactored code: 80%+ coverage
- Critical paths: 95%+ coverage

## 📊 Success Metrics

### Code Quality Metrics:

- Cyclomatic complexity < 10 per method
- Class responsibility count < 5
- Coupling factor < 0.3
- Zero bare except blocks

### Runtime Metrics:

- Memory leaks eliminated
- Signal connection stability
- Error recovery success rate > 95%

## 🚀 Migration Guidelines

### For Each Anti-Pattern:

1. **Identify**: Scan codebase for pattern
2. **Isolate**: Create focused test cases
3. **Refactor**: Apply modern pattern
4. **Validate**: Run comprehensive tests
5. **Deploy**: Gradual rollout with monitoring

### Tools for Detection:

- Static analysis with pylint/mypy
- Custom AST analyzers for patterns
- Runtime monitoring for memory leaks
- Performance profiling

---

**Next Action**: Start with P0 lambda closure fixes in image_manager.py as proof of concept.
