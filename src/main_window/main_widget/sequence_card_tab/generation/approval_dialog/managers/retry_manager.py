from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from dataclasses import dataclass
from typing import List, Dict, Callable
import time
import logging


@dataclass
class RetryState:
    attempts: int = 0
    last_error: str = ""
    last_attempt_time: float = 0.0
    backoff_multiplier: float = 1.5


class RetryManager(QObject):
    retry_attempted = pyqtSignal(str, int)  # sequence_id, attempt_number

    def __init__(
        self, max_retries: int = 3, base_delay: int = 1000, max_delay: int = 10000
    ):
        super().__init__()
        self.max_retries = max_retries
        self.base_retry_delay = base_delay
        self.max_retry_delay = max_delay

        self.retry_states: Dict[str, RetryState] = {}
        self.retry_queue: List[str] = []
        self.retry_callbacks: Dict[str, Callable] = {}

        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self._process_pending_retries)

    def record_failure(self, sequence_id: str, error_message: str) -> None:
        """Record a failure for retry tracking"""
        if sequence_id not in self.retry_states:
            self.retry_states[sequence_id] = RetryState()

        self.retry_states[sequence_id].attempts += 1
        self.retry_states[sequence_id].last_error = error_message
        self.retry_states[sequence_id].last_attempt_time = time.time()

    def should_retry(
        self, sequence_id: str, circuit_breaker_open: bool = False
    ) -> bool:
        """Determine if a sequence should be retried"""
        if sequence_id not in self.retry_states:
            return True

        retry_state = self.retry_states[sequence_id]

        if retry_state.attempts >= self.max_retries:
            logging.info(f"Max retries ({self.max_retries}) exceeded for {sequence_id}")
            return False

        if circuit_breaker_open:
            logging.info(f"Circuit breaker open, skipping retry for {sequence_id}")
            return False

        return True

    def schedule_retry(self, sequence_id: str, retry_callback: Callable) -> None:
        """Schedule a retry attempt with exponential backoff"""
        try:
            if sequence_id not in self.retry_states:
                self.retry_states[sequence_id] = RetryState()

            retry_state = self.retry_states[sequence_id]
            delay = min(
                self.base_retry_delay
                * (retry_state.backoff_multiplier ** (retry_state.attempts - 1)),
                self.max_retry_delay,
            )

            logging.info(
                f"Scheduling retry {retry_state.attempts}/{self.max_retries} for {sequence_id} in {delay}ms"
            )

            self.retry_queue.append(sequence_id)
            self.retry_callbacks[sequence_id] = retry_callback
            self.retry_attempted.emit(sequence_id, retry_state.attempts)

            if not self.retry_timer.isActive():
                self.retry_timer.start(int(delay))

        except Exception as e:
            logging.error(f"Error scheduling retry for {sequence_id}: {e}")
            raise

    def _process_pending_retries(self) -> None:
        """Process queued retry attempts"""
        if not self.retry_queue:
            self.retry_timer.stop()
            return

        try:
            sequence_id = self.retry_queue.pop(0)

            if sequence_id in self.retry_callbacks:
                callback = self.retry_callbacks[sequence_id]
                callback(sequence_id)
                del self.retry_callbacks[sequence_id]
            else:
                logging.warning(f"No retry callback found for {sequence_id}")

            if self.retry_queue:
                self.retry_timer.start(self.base_retry_delay)
            else:
                self.retry_timer.stop()

        except Exception as e:
            logging.error(f"Error processing retry queue: {e}")
            self.retry_timer.stop()

    def clear_retry_queue(self) -> None:
        """Clear all pending retries"""
        self.retry_queue.clear()
        self.retry_callbacks.clear()
        if self.retry_timer.isActive():
            self.retry_timer.stop()

    def get_retry_count(self, sequence_id: str) -> int:
        """Get current retry count for a sequence"""
        if sequence_id in self.retry_states:
            return self.retry_states[sequence_id].attempts
        return 0

    def get_pending_retries_count(self) -> int:
        """Get number of pending retries"""
        return len(self.retry_queue)

    def configure_policy(
        self, max_retries: int = 3, base_delay: int = 1000, max_delay: int = 10000
    ) -> None:
        """Configure retry policy parameters"""
        self.max_retries = max_retries
        self.base_retry_delay = base_delay
        self.max_retry_delay = max_delay
        logging.info(
            f"Retry policy configured: max_retries={max_retries}, base_delay={base_delay}ms, max_delay={max_delay}ms"
        )
