import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from enterprise_agent_platform.approval.executor import (
    ActionNotApprovedError,
    ApprovedActionExecutor,
)
from enterprise_agent_platform.approval.in_memory_store import (
    InMemoryApprovalStore,
)
from enterprise_agent_platform.approval.registry import ActionRegistry
from enterprise_agent_platform.approval.service import (
    ApprovalNotFoundError,
    ApprovalService,
)
from enterprise_agent_platform.models.approval import (
    ApprovalStatus,
    ExecutionStatus,
)


class FakeAction:
    def __init__(self, result: object = "completed") -> None:
        self.result = result
        self.calls: list[tuple[dict[str, Any], str]] = []
        self.error: Exception | None = None

    async def execute(
        self,
        payload: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> object:
        self.calls.append((payload, idempotency_key))
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def setup() -> tuple[
    InMemoryApprovalStore,
    ApprovalService,
    ActionRegistry,
    ApprovedActionExecutor,
]:
    store = InMemoryApprovalStore()
    service = ApprovalService(store)
    registry = ActionRegistry()
    executor = ApprovedActionExecutor(store, registry)
    return store, service, registry, executor


@pytest.mark.asyncio
async def test_approved_action_executes_and_records_success(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    store, service, registry, executor = setup
    action = FakeAction({"deployed": True})
    registry.register("deploy_application", action)

    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
        payload={"environment": "staging"},
    )
    await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    result = await executor.execute(request.id)

    assert result == {"deployed": True}
    assert len(action.calls) == 1
    assert action.calls[0][0] == {"environment": "staging"}
    execution_id = action.calls[0][1]
    assert execution_id

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.SUCCEEDED
    assert stored.execution_id == execution_id
    assert stored.execution_started_at is not None
    assert stored.execution_finished_at is not None
    assert stored.execution_finished_at >= stored.execution_started_at
    assert stored.execution_error is None


@pytest.mark.asyncio
async def test_pending_request_does_not_execute(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    _, service, registry, executor = setup
    action = FakeAction()
    registry.register("deploy_application", action)

    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Requires approval.",
    )

    with pytest.raises(ActionNotApprovedError):
        await executor.execute(request.id)

    assert action.calls == []


@pytest.mark.asyncio
async def test_rejected_request_does_not_execute(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    _, service, registry, executor = setup
    action = FakeAction()
    registry.register("delete_records", action)

    request = await service.request_approval(
        action_id="delete_records",
        action="Delete records",
        reason="Requires review.",
    )
    await service.decide(
        request.id,
        ApprovalStatus.REJECTED,
        reviewer_id="reviewer-123",
    )

    with pytest.raises(ActionNotApprovedError):
        await executor.execute(request.id)

    assert action.calls == []


@pytest.mark.asyncio
async def test_missing_request_does_not_execute(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    _, _, _, executor = setup

    with pytest.raises(ApprovalNotFoundError):
        await executor.execute("missing-request")


@pytest.mark.asyncio
async def test_unregistered_action_does_not_claim_request(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    store, service, _, executor = setup

    request = await service.request_approval(
        action_id="unknown_action",
        action="Unknown action",
        reason="Testing registration.",
    )
    await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    with pytest.raises(LookupError, match="not registered"):
        await executor.execute(request.id)

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.NOT_STARTED
    assert stored.execution_started_at is None


@pytest.mark.asyncio
async def test_second_execution_attempt_is_rejected(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    _, service, registry, executor = setup
    action = FakeAction()
    registry.register("deploy_application", action)

    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
    )
    await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    await executor.execute(request.id)

    with pytest.raises(ActionNotApprovedError):
        await executor.execute(request.id)

    assert len(action.calls) == 1


@pytest.mark.asyncio
async def test_action_error_records_unknown_outcome(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    store, service, registry, executor = setup
    action = FakeAction()
    action.error = TimeoutError("Downstream response timed out")
    registry.register("deploy_application", action)

    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
    )
    await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    with pytest.raises(TimeoutError, match="Downstream response timed out"):
        await executor.execute(request.id)

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.UNKNOWN
    assert stored.execution_error == "Downstream response timed out"
    assert stored.execution_started_at is not None
    assert stored.execution_finished_at is not None
    assert len(action.calls) == 1


@pytest.mark.asyncio
async def test_concurrent_attempts_execute_action_only_once(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    store, service, registry, executor = setup
    action = FakeAction()
    registry.register("deploy_application", action)

    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
    )
    await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    results = await asyncio.gather(
        executor.execute(request.id),
        executor.execute(request.id),
        return_exceptions=True,
    )

    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert len(action.calls) == 1

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_executor_does_not_overwrite_terminal_execution_state(
    setup: tuple[
        InMemoryApprovalStore,
        ApprovalService,
        ActionRegistry,
        ApprovedActionExecutor,
    ],
) -> None:
    store, service, registry, executor = setup
    action = FakeAction()
    registry.register("deploy_application", action)

    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
    )
    await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    await executor.execute(request.id)
    succeeded = await store.get(request.id)
    assert succeeded is not None
    assert succeeded.execution_id is not None

    # A late/stale worker cannot change a completed execution to UNKNOWN.
    late_update = await store.finish_execution(
        request.id,
        succeeded.execution_id,
        ExecutionStatus.UNKNOWN,
        finished_at=datetime.now(UTC),
        error="Late update",
    )

    assert late_update is None

    final = await store.get(request.id)
    assert final is not None
    assert final.execution_status == ExecutionStatus.SUCCEEDED
    assert final.execution_error is None
