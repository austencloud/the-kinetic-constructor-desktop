from dataclasses import dataclass
import time
import logging


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: float = 30.0


class CircuitBreakerManager:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.state = CircuitBreakerState(
            failure_threshold=failure_threshold, recovery_timeout=recovery_timeout
        )

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit breaker"""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if (
            self.state.failure_count >= self.state.failure_threshold
            and self.state.state == "CLOSED"
        ):
            self.state.state = "OPEN"
            logging.warning("Circuit breaker opened due to excessive failures")

    def record_success(self) -> None:
        """Record a success and potentially close the circuit breaker"""
        if self.state.state == "HALF_OPEN":
            self.state.state = "CLOSED"
            self.state.failure_count = 0
            logging.info("Circuit breaker closed after successful recovery")

    def is_open(self) -> bool:
        """Check if circuit breaker is preventing operations"""
        if self.state.state == "OPEN":
            time_since_failure = time.time() - self.state.last_failure_time
            if time_since_failure > self.state.recovery_timeout:
                self.state.state = "HALF_OPEN"
                logging.info("Circuit breaker moving to HALF_OPEN state")
                return False
            return True
        return False

    def attempt_recovery(self) -> None:
        """Attempt to recover from circuit breaker open state"""
        self.state.state = "HALF_OPEN"
        self.state.failure_count = 0
        logging.info("Attempting circuit breaker recovery")

    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        self.state.state = "CLOSED"
        self.state.failure_count = 0
        self.state.last_failure_time = 0.0
        logging.info("Circuit breaker manually reset")

    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state.state
