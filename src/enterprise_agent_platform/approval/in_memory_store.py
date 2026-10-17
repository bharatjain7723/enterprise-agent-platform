import asyncio
from datetime import UTC, datetime

from enterprise_agent_platform.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
    ExecutionStatus,
)


class InMemoryApprovalStore:
    """In-memory approval storage with atomic execution claiming."""

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._lock = asyncio.Lock()

    async def save(self, request: ApprovalRequest) -> None:
        async with self._lock:
            if request.id in self._requests:
                raise ValueError(f"Approval request '{request.id}' already exists.")

            self._requests[request.id] = request.model_copy(deep=True)

    async def get(self, request_id: str) -> ApprovalRequest | None:
        async with self._lock:
            request = self._requests.get(request_id)
            return request.model_copy(deep=True) if request else None

    async def update(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRequest | None:
        async with self._lock:
            existing = self._requests.get(request.id)

            if existing is None:
                return None

            # Approval-critical details must remain unchanged.
            if (
                request.action_id != existing.action_id
                or request.action != existing.action
                or request.reason != existing.reason
                or request.payload != existing.payload
                or request.requested_at != existing.requested_at
            ):
                raise ValueError(
                    "Cannot modify the action or payload of an existing approval request."
                )

            updated = request.model_copy(deep=True)
            self._requests[request.id] = updated

            return updated.model_copy(deep=True)

    async def claim_execution(
        self,
        request_id: str,
        execution_id: str,
    ) -> ApprovalRequest | None:
        async with self._lock:
            request = self._requests.get(request_id)

            if request is None:
                return None

            if request.status != ApprovalStatus.APPROVED:
                return None

            if request.execution_status != ExecutionStatus.NOT_STARTED:
                return None

            claimed = request.model_copy(
                update={
                    "execution_status": ExecutionStatus.RUNNING,
                    "execution_id": execution_id,
                    "execution_started_at": datetime.now(UTC),
                },
                deep=True,
            )

            self._requests[request_id] = claimed
            return claimed.model_copy(deep=True)

    async def record_decision(
        self,
        request_id: str,
        decision: ApprovalStatus,
        *,
        reviewer_id: str,
        reviewer_feedback: str | None,
        decided_at: datetime,
    ) -> ApprovalRequest | None:
        async with self._lock:
            request = self._requests.get(request_id)

            if request is None:
                return None

            if request.status != ApprovalStatus.PENDING:
                raise ValueError(f"Cannot decide a request with status '{request.status}'.")

            if decision not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
                raise ValueError("A decision must be APPROVED or REJECTED.")

            updated = request.model_copy(
                update={
                    "status": decision,
                    "reviewer_id": reviewer_id,
                    "reviewer_feedback": reviewer_feedback,
                    "decided_at": decided_at,
                },
                deep=True,
            )

            self._requests[request_id] = updated
            return updated.model_copy(deep=True)

    async def finish_execution(
        self,
        request_id: str,
        execution_id: str,
        status: ExecutionStatus,
        *,
        finished_at: datetime,
        error: str | None = None,
    ) -> ApprovalRequest | None:
        async with self._lock:
            request = self._requests.get(request_id)

            if request is None:
                return None

            if request.execution_status != ExecutionStatus.RUNNING:
                return None

            if request.execution_id != execution_id:
                return None

            if status not in (
                ExecutionStatus.SUCCEEDED,
                ExecutionStatus.FAILED,
                ExecutionStatus.UNKNOWN,
            ):
                raise ValueError("Execution can only finish as SUCCEEDED, FAILED, or UNKNOWN.")

            if status == ExecutionStatus.SUCCEEDED and error is not None:
                raise ValueError("A successful execution cannot have an error.")

            if status != ExecutionStatus.SUCCEEDED and not error:
                raise ValueError("A non-successful execution must include an error description.")

            updated = request.model_copy(
                update={
                    "execution_status": status,
                    "execution_finished_at": finished_at,
                    "execution_error": error,
                },
                deep=True,
            )

            self._requests[request_id] = updated
            return updated.model_copy(deep=True)
