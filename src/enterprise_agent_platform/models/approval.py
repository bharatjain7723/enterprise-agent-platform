from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExecutionStatus(StrEnum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ApprovalRequest(BaseModel):
    """A human decision authorizing a specific action and payload."""

    id: str
    action_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)

    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime
    decided_at: datetime | None = None
    reviewer_id: str | None = None
    reviewer_feedback: str | None = None

    execution_status: ExecutionStatus = ExecutionStatus.NOT_STARTED
    execution_id: str | None = None
    execution_started_at: datetime | None = None
    execution_finished_at: datetime | None = None
    execution_error: str | None = None
