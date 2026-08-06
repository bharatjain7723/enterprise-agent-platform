class PlatformError(Exception):
    """Base exception for errors raised by the platform."""


class RetryableError(PlatformError):
    """An error caused by a temporary condition that may succeed on retry."""


class NonRetryableError(PlatformError):
    """An error that should fail immediately without retrying."""
