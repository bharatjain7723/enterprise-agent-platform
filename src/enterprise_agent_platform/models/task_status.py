from enum import StrEnum


class TaskStatus(StrEnum):
    """Execution status of a task within a workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
