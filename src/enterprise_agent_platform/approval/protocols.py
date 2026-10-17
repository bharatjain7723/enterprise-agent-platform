from datetime import datetime
from typing import Protocol

from enterprise_agent_platform.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
    ExecutionStatus,
)


class ApprovalStore(Protocol):
    """Storage interface for approval requests."""

    async def save(self, request: ApprovalRequest) -> None: ...

    async def get(self, request_id: str) -> ApprovalRequest | None: ...

    async def update(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRequest | None: ...

    async def claim_execution(
        self,
        request_id: str,
        execution_id: str,
    ) -> ApprovalRequest | None:
        """Atomically claim an approved request for execution."""
        ...

    async def record_decision(
        self,
        request_id: str,
        decision: ApprovalStatus,
        *,
        reviewer_id: str,
        reviewer_feedback: str | None,
        decided_at: datetime,
    ) -> ApprovalRequest | None: ...

    async def finish_execution(
        self,
        request_id: str,
        execution_id: str,
        status: ExecutionStatus,
        *,
        finished_at: datetime,
        error: str | None = None,
    ) -> ApprovalRequest | None: ...
