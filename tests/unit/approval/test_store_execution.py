import asyncio
from datetime import UTC, datetime

import pytest

from enterprise_agent_platform.approval.in_memory_store import (
    InMemoryApprovalStore,
)
from enterprise_agent_platform.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
    ExecutionStatus,
)


def make_approved_request(
    request_id: str = "approval-1",
) -> ApprovalRequest:
    return ApprovalRequest(
        id=request_id,
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
        payload={
            "environment": "staging",
            "version": "v1.4.0",
            "metadata": {"region": "us-ashburn-1"},
        },
        requested_at=datetime.now(UTC),
        status=ApprovalStatus.APPROVED,
    )


@pytest.mark.asyncio
async def test_claim_execution_moves_approved_request_to_running() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    claimed = await store.claim_execution(request.id, "execution-1")

    assert claimed is not None
    assert claimed.execution_status == ExecutionStatus.RUNNING
    assert claimed.execution_id == "execution-1"


@pytest.mark.asyncio
async def test_claim_execution_rejects_pending_request() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    request.status = ApprovalStatus.PENDING
    await store.save(request)

    result = await store.claim_execution(request.id, "execution-2")

    assert result is None
    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.NOT_STARTED


@pytest.mark.asyncio
async def test_only_one_concurrent_claim_succeeds() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    results = await asyncio.gather(
        store.claim_execution(request.id, "execution-a"),
        store.claim_execution(request.id, "execution-b"),
    )

    successful_claims = [result for result in results if result is not None]
    assert len(successful_claims) == 1
    assert successful_claims[0].execution_status == ExecutionStatus.RUNNING


@pytest.mark.asyncio
async def test_claim_execution_rejects_second_claim() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    first = await store.claim_execution(request.id, "execution-first")
    second = await store.claim_execution(request.id, "execution-second")

    assert first is not None
    assert second is None

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_id == "execution-first"


@pytest.mark.asyncio
async def test_claim_execution_returns_none_for_missing_request() -> None:
    store = InMemoryApprovalStore()

    result = await store.claim_execution("missing", "execution-1")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field_name", "changed_value"),
    [
        ("action_id", "delete_database"),
        ("action", "Delete database"),
        ("reason", "Changed reason"),
        ("payload", {"environment": "production"}),
        (
            "requested_at",
            datetime(2020, 1, 1, tzinfo=UTC),
        ),
    ],
)
async def test_update_rejects_changes_to_approval_critical_fields(
    field_name: str,
    changed_value: object,
) -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    changed_request = request.model_copy(
        update={field_name: changed_value},
        deep=True,
    )

    with pytest.raises(ValueError, match="Cannot modify"):
        await store.update(changed_request)

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.action_id == request.action_id
    assert stored.action == request.action
    assert stored.reason == request.reason
    assert stored.payload == request.payload
    assert stored.requested_at == request.requested_at


@pytest.mark.asyncio
async def test_update_allows_execution_status_changes() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    claimed = await store.claim_execution(request.id, "execution-1")
    assert claimed is not None

    completed = claimed.model_copy(
        update={
            "execution_status": ExecutionStatus.SUCCEEDED,
        },
    )
    saved = await store.update(completed)

    assert saved is not None
    assert saved.execution_status == ExecutionStatus.SUCCEEDED

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.payload == request.payload
    assert stored.action_id == request.action_id


@pytest.mark.asyncio
async def test_mutating_original_request_does_not_change_stored_payload() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    request.payload["environment"] = "production"
    request.payload["metadata"]["region"] = "changed-region"

    stored = await store.get(request.id)

    assert stored is not None
    assert stored.payload["environment"] == "staging"
    assert stored.payload["metadata"]["region"] == "us-ashburn-1"


@pytest.mark.asyncio
async def test_mutating_retrieved_request_does_not_change_stored_payload() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request()
    await store.save(request)

    retrieved = await store.get(request.id)
    assert retrieved is not None

    retrieved.payload["environment"] = "production"
    retrieved.payload["metadata"]["region"] = "changed-region"

    stored = await store.get(request.id)

    assert stored is not None
    assert stored.payload["environment"] == "staging"
    assert stored.payload["metadata"]["region"] == "us-ashburn-1"


@pytest.mark.asyncio
async def test_update_returns_none_for_missing_request() -> None:
    store = InMemoryApprovalStore()
    request = make_approved_request("missing")

    result = await store.update(request)

    assert result is None


@pytest.mark.asyncio
async def test_finish_execution_rejects_wrong_execution_id() -> None:
    store = InMemoryApprovalStore()
    request = ApprovalRequest(
        id="approval-finish-1",
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
        requested_at=datetime.now(UTC),
        status=ApprovalStatus.APPROVED,
    )
    await store.save(request)

    claimed = await store.claim_execution(request.id, "execution-owner")
    assert claimed is not None

    result = await store.finish_execution(
        request.id,
        "execution-imposter",
        ExecutionStatus.SUCCEEDED,
        finished_at=datetime.now(UTC),
    )

    assert result is None
    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.RUNNING


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_status",
    [ExecutionStatus.NOT_STARTED, ExecutionStatus.RUNNING],
)
async def test_finish_execution_rejects_non_terminal_status(
    invalid_status: ExecutionStatus,
) -> None:
    store = InMemoryApprovalStore()
    request = ApprovalRequest(
        id="approval-finish-2",
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
        requested_at=datetime.now(UTC),
        status=ApprovalStatus.APPROVED,
    )
    await store.save(request)
    claimed = await store.claim_execution(request.id, "execution-owner")
    assert claimed is not None

    with pytest.raises(ValueError, match="only finish"):
        await store.finish_execution(
            request.id,
            "execution-owner",
            invalid_status,
            finished_at=datetime.now(UTC),
        )

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.execution_status == ExecutionStatus.RUNNING


@pytest.mark.asyncio
async def test_finish_execution_requires_error_for_unknown_outcome() -> None:
    store = InMemoryApprovalStore()
    request = ApprovalRequest(
        id="approval-finish-3",
        action_id="deploy_application",
        action="Deploy application",
        reason="Release is ready.",
        requested_at=datetime.now(UTC),
        status=ApprovalStatus.APPROVED,
    )
    await store.save(request)
    claimed = await store.claim_execution(request.id, "execution-owner")
    assert claimed is not None

    with pytest.raises(ValueError, match="must include an error"):
        await store.finish_execution(
            request.id,
            "execution-owner",
            ExecutionStatus.UNKNOWN,
            finished_at=datetime.now(UTC),
        )
