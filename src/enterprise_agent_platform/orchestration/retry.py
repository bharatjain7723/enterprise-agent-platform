import random
from dataclasses import dataclass

from enterprise_agent_platform.exceptions import RetryableError


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration controlling task retry behavior."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    jitter_seconds: float = 0.5

    def should_retry(
        self,
        attempts: int,
        error: Exception,
    ) -> bool:
        """Return whether another execution attempt is allowed."""

        return attempts < self.max_attempts and isinstance(error, RetryableError)

    def get_delay(
        self,
        attempts: int,
    ) -> float:
        """Calculate the delay before the next retry."""

        exponential_delay = self.base_delay_seconds * (2 ** (attempts - 1))

        capped_delay = min(
            exponential_delay,
            self.max_delay_seconds,
        )

        jitter = random.uniform(
            0,
            self.jitter_seconds,
        )

        return capped_delay + jitter
