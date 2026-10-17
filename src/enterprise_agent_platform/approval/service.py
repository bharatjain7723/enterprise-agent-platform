from datetime import UTC, datetime
from uuid import uuid4

from enterprise_agent_platform.approval.protocols import ApprovalStore
from enterprise_agent_platform.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalNotFoundError(LookupError):
    """Raised when an approval request does not exist."""


class InvalidApprovalTransitionError(ValueError):
    """Raised when an approval request cannot transition to a new state."""


class ApprovalService:
    """Creates approval requests and records human decisions."""

    def __init__(self, store: ApprovalStore) -> None:
        self._store = store

    async def request_approval(
        self,
        action_id: str,
        action: str,
        reason: str,
        payload: dict[str, object] | None = None,
    ) -> ApprovalRequest:
        if not action_id.strip():
            raise ValueError("Action ID cannot be empty.")
        if not action.strip():
            raise ValueError("Action cannot be empty.")
        if not reason.strip():
            raise ValueError("Reason cannot be empty.")

        request = ApprovalRequest(
            id=str(uuid4()),
            action_id=action_id,
            action=action,
            reason=reason,
            payload=payload or {},
            requested_at=datetime.now(UTC),
        )
        await self._store.save(request)
        return request

    async def get_request(self, request_id: str) -> ApprovalRequest:
        request = await self._store.get(request_id)
        if request is None:
            raise ApprovalNotFoundError(f"Approval request '{request_id}' was not found.")
        return request

    async def decide(
        self,
        request_id: str,
        decision: ApprovalStatus,
        *,
        reviewer_id: str,
        reviewer_feedback: str | None = None,
    ) -> ApprovalRequest:
        if not reviewer_id.strip():
            raise ValueError("Reviewer ID cannot be empty.")

        if decision not in (
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
        ):
            raise InvalidApprovalTransitionError("A decision must be APPROVED or REJECTED.")

        try:
            saved = await self._store.record_decision(
                request_id,
                decision,
                reviewer_id=reviewer_id,
                reviewer_feedback=reviewer_feedback,
                decided_at=datetime.now(UTC),
            )
        except ValueError as exc:
            raise InvalidApprovalTransitionError(str(exc)) from exc

        if saved is None:
            raise ApprovalNotFoundError(f"Approval request '{request_id}' was not found.")

        return saved
