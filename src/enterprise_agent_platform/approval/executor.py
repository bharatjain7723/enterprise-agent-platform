from datetime import UTC, datetime
from uuid import uuid4

from enterprise_agent_platform.approval.protocols import ApprovalStore
from enterprise_agent_platform.approval.registry import ActionRegistry
from enterprise_agent_platform.approval.service import (
    ApprovalNotFoundError,
)
from enterprise_agent_platform.models.approval import (
    ApprovalStatus,
    ExecutionStatus,
)


class ActionNotApprovedError(PermissionError):
    """Raised when an action has not been approved."""


class ApprovedActionExecutor:
    """Claims approved requests and executes registered actions."""

    def __init__(
        self,
        store: ApprovalStore,
        registry: ActionRegistry,
    ) -> None:
        self._store = store
        self._registry = registry

    async def execute(self, request_id: str) -> object:
        request = await self._store.get(request_id)

        if request is None:
            raise ApprovalNotFoundError(f"Approval request '{request_id}' was not found.")

        if request.status != ApprovalStatus.APPROVED:
            raise ActionNotApprovedError(
                f"Action cannot execute: approval status is '{request.status}'."
            )

        # Resolve before claiming so an unknown action does not leave
        # the request stuck in RUNNING.
        action = self._registry.get(request.action_id)
        execution_id = str(uuid4())

        claimed = await self._store.claim_execution(
            request_id,
            execution_id,
        )
        if claimed is None:
            raise ActionNotApprovedError("Request is no longer eligible for execution.")

        try:
            result = await action.execute(
                claimed.payload,
                idempotency_key=execution_id,
            )
        except Exception as exc:
            saved = await self._store.finish_execution(
                request_id,
                execution_id,
                ExecutionStatus.UNKNOWN,
                finished_at=datetime.now(UTC),
                error=str(exc) or type(exc).__name__,
            )

            if saved is None:
                raise RuntimeError(
                    "Action raised an exception, but its execution outcome "
                    "could not be recorded. Reconcile before retrying."
                ) from exc

            raise

        saved = await self._store.finish_execution(
            request_id,
            execution_id,
            ExecutionStatus.SUCCEEDED,
            finished_at=datetime.now(UTC),
        )

        if saved is None:
            # The action may already have executed. Never retry blindly.
            raise RuntimeError(
                "Action completed, but its execution outcome could not "
                "be recorded. Reconcile before retrying."
            )

        return result
