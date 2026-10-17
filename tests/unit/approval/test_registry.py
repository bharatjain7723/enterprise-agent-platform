import pytest

from enterprise_agent_platform.approval.registry import ActionRegistry


class FakeAction:
    async def execute(
        self,
        payload: dict[str, object],
        *,
        idempotency_key: str,
    ) -> object:
        return payload


def test_register_and_resolve_action() -> None:
    registry = ActionRegistry()
    action = FakeAction()

    registry.register("deploy_application", action)

    assert registry.get("deploy_application") is action


def test_duplicate_action_registration_is_rejected() -> None:
    registry = ActionRegistry()
    registry.register("deploy_application", FakeAction())

    with pytest.raises(ValueError, match="already registered"):
        registry.register("deploy_application", FakeAction())


@pytest.mark.parametrize("action_id", ["", " ", "\t"])
def test_blank_action_id_is_rejected(action_id: str) -> None:
    registry = ActionRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register(action_id, FakeAction())


def test_unregistered_action_raises_lookup_error() -> None:
    registry = ActionRegistry()

    with pytest.raises(LookupError, match="not registered"):
        registry.get("unknown_action")
