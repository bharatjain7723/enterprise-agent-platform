import asyncio
from datetime import UTC, datetime

import pytest

from enterprise_agent_platform.approval.in_memory_store import (
    InMemoryApprovalStore,
)
from enterprise_agent_platform.approval.service import (
    ApprovalNotFoundError,
    ApprovalService,
    InvalidApprovalTransitionError,
)
from enterprise_agent_platform.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
)


@pytest.fixture
def store() -> InMemoryApprovalStore:
    return InMemoryApprovalStore()


@pytest.fixture
def service(store: InMemoryApprovalStore) -> ApprovalService:
    return ApprovalService(store)


@pytest.mark.asyncio
async def test_request_approval_creates_pending_request(
    service: ApprovalService,
    store: InMemoryApprovalStore,
) -> None:
    request = await service.request_approval(
        action_id="deploy_application",
        action="Deploy application",
        reason="Release candidate passed tests.",
    )

    assert request.id
    assert request.status == ApprovalStatus.PENDING
    assert request.requested_at.tzinfo is not None
    assert request.decided_at is None
    assert request.reviewer_id is None

    stored = await store.get(request.id)
    assert stored == request


@pytest.mark.asyncio
@pytest.mark.parametrize("action_id", ["", " ", "\t", "\n"])
async def test_blank_action_id_is_rejected(
    service: ApprovalService,
    action_id: str,
) -> None:
    with pytest.raises(ValueError, match="Action ID cannot be empty"):
        await service.request_approval(action_id, "Deploy application", "Valid reason")


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["", " ", "\t", "\n"])
async def test_blank_action_is_rejected(
    service: ApprovalService,
    action: str,
) -> None:
    with pytest.raises(ValueError, match="Action cannot be empty"):
        await service.request_approval("some_id", action, "Valid reason")


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["", " ", "\t", "\n"])
async def test_blank_reason_is_rejected(
    service: ApprovalService,
    reason: str,
) -> None:
    with pytest.raises(ValueError, match="Reason cannot be empty"):
        await service.request_approval("deploy_application", "Deploy application", reason)


@pytest.mark.asyncio
async def test_get_request_returns_existing_request(
    service: ApprovalService,
) -> None:
    created = await service.request_approval(
        "deploy_application",
        "Deploy application",
        "Deployment requires review.",
    )

    assert await service.get_request(created.id) == created


@pytest.mark.asyncio
async def test_get_missing_request_raises_not_found(
    service: ApprovalService,
) -> None:
    with pytest.raises(ApprovalNotFoundError, match="was not found"):
        await service.get_request("missing-id")


@pytest.mark.asyncio
async def test_approval_records_reviewer_status_and_timestamp(
    service: ApprovalService,
    store: InMemoryApprovalStore,
) -> None:
    request = await service.request_approval(
        "deploy_application",
        "Deploy application",
        "Release is ready.",
    )

    result = await service.decide(
        request.id,
        ApprovalStatus.APPROVED,
        reviewer_id="reviewer-123",
    )

    assert result.status == ApprovalStatus.APPROVED
    assert result.reviewer_id == "reviewer-123"
    assert result.decided_at is not None
    assert result.decided_at.tzinfo is not None
    assert result.decided_at >= request.requested_at
    assert await store.get(request.id) == result


@pytest.mark.asyncio
async def test_rejection_records_reviewer_feedback(
    service: ApprovalService,
) -> None:
    request = await service.request_approval(
        "delete_customer_records",
        "Delete customer records",
        "Cleanup requested.",
    )

    result = await service.decide(
        request.id,
        ApprovalStatus.REJECTED,
        reviewer_id="reviewer-456",
        reviewer_feedback="Retention policy prohibits deletion.",
    )

    assert result.status == ApprovalStatus.REJECTED
    assert result.reviewer_id == "reviewer-456"
    assert result.decided_at is not None
    assert result.reviewer_feedback == ("Retention policy prohibits deletion.")


@pytest.mark.asyncio
@pytest.mark.parametrize("reviewer_id", ["", " ", "\t", "\n"])
async def test_blank_reviewer_id_is_rejected(
    service: ApprovalService,
    reviewer_id: str,
) -> None:
    request = await service.request_approval(
        "deploy_application",
        "Deploy application",
        "Review required.",
    )

    with pytest.raises(ValueError, match="Reviewer ID cannot be empty"):
        await service.decide(
            request.id,
            ApprovalStatus.APPROVED,
            reviewer_id=reviewer_id,
        )

    unchanged = await service.get_request(request.id)
    assert unchanged.status == ApprovalStatus.PENDING
    assert unchanged.reviewer_id is None
    assert unchanged.decided_at is None


@pytest.mark.asyncio
async def test_pending_is_not_a_valid_decision(
    service: ApprovalService,
) -> None:
    request = await service.request_approval(
        "restart_service",
        "Restart service",
        "Maintenance requested.",
    )

    with pytest.raises(
        InvalidApprovalTransitionError,
        match="must be APPROVED or REJECTED",
    ):
        await service.decide(
            request.id,
            ApprovalStatus.PENDING,
            reviewer_id="reviewer-123",
        )

    unchanged = await service.get_request(request.id)
    assert unchanged.status == ApprovalStatus.PENDING
    assert unchanged.decided_at is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "first_decision",
    [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED],
)
async def test_terminal_request_cannot_be_decided_again(
    service: ApprovalService,
    first_decision: ApprovalStatus,
) -> None:
    request = await service.request_approval(
        "execute_operation",
        "Execute operation",
        "Human review required.",
    )
    first_result = await service.decide(
        request.id,
        first_decision,
        reviewer_id="reviewer-first",
        reviewer_feedback="First decision",
    )

    opposite = (
        ApprovalStatus.REJECTED
        if first_decision == ApprovalStatus.APPROVED
        else ApprovalStatus.APPROVED
    )

    with pytest.raises(
        InvalidApprovalTransitionError,
        match="Cannot decide a request",
    ):
        await service.decide(
            request.id,
            opposite,
            reviewer_id="reviewer-second",
            reviewer_feedback="Second decision",
        )

    final_result = await service.get_request(request.id)
    assert final_result == first_result


@pytest.mark.asyncio
async def test_concurrent_decisions_allow_only_one_winner(
    service: ApprovalService,
) -> None:
    request = await service.request_approval(
        "deploy_application",
        "Deploy application",
        "Release is ready.",
    )

    async def decide(
        decision: ApprovalStatus,
        reviewer_id: str,
    ) -> ApprovalStatus | None:
        try:
            result = await service.decide(
                request.id,
                decision,
                reviewer_id=reviewer_id,
            )
            return result.status
        except InvalidApprovalTransitionError:
            return None

    results = await asyncio.gather(
        decide(ApprovalStatus.APPROVED, "reviewer-a"),
        decide(ApprovalStatus.REJECTED, "reviewer-b"),
    )

    assert sum(result is not None for result in results) == 1

    stored = await service.get_request(request.id)
    assert stored.status in (
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
    )
    assert stored.reviewer_id in ("reviewer-a", "reviewer-b")
    assert stored.decided_at is not None


@pytest.mark.asyncio
async def test_mutating_retrieved_request_does_not_change_storage(
    service: ApprovalService,
) -> None:
    request = await service.request_approval(
        "deploy_application",
        "Deploy application",
        "Review required.",
    )

    retrieved = await service.get_request(request.id)
    retrieved.status = ApprovalStatus.APPROVED

    stored = await service.get_request(request.id)
    assert stored.status == ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_store_returns_independent_copies(
    store: InMemoryApprovalStore,
) -> None:
    request = ApprovalRequest(
        id="approval-1",
        action_id="restart_service",
        action="Restart service",
        reason="Maintenance.",
        requested_at=datetime.now(UTC),
    )
    await store.save(request)

    retrieved = await store.get(request.id)
    assert retrieved is not None
    retrieved.status = ApprovalStatus.REJECTED

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.status == ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_request_missing_during_decision_raises_not_found() -> None:
    class DisappearingStore(InMemoryApprovalStore):
        async def record_decision(
            self,
            request_id: str,
            decision: ApprovalStatus,
            *,
            reviewer_id: str,
            reviewer_feedback: str | None,
            decided_at: datetime,
        ) -> ApprovalRequest | None:
            return None

    service = ApprovalService(DisappearingStore())
    request = await service.request_approval(
        "execute_operation",
        "Execute operation",
        "Requires approval.",
    )

    with pytest.raises(ApprovalNotFoundError, match="was not found"):
        await service.decide(
            request.id,
            ApprovalStatus.APPROVED,
            reviewer_id="reviewer-123",
        )


@pytest.mark.asyncio
async def test_duplicate_request_id_is_rejected(
    store: InMemoryApprovalStore,
) -> None:
    request = ApprovalRequest(
        id="duplicate-id",
        action_id="deploy_application",
        action="Deploy application",
        reason="Original request.",
        requested_at=datetime.now(UTC),
    )
    await store.save(request)

    duplicate = request.model_copy(update={"reason": "Duplicate request."})

    with pytest.raises(ValueError, match="already exists"):
        await store.save(duplicate)

    stored = await store.get(request.id)
    assert stored is not None
    assert stored.reason == "Original request."
