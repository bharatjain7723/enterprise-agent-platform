from typing import Any, Protocol


class RegisteredAction(Protocol):
    """Interface for an executable, registered action."""

    async def execute(
        self,
        payload: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> Any: ...


class ActionRegistry:
    """Resolves action IDs to approved action implementations."""

    def __init__(self) -> None:
        self._actions: dict[str, RegisteredAction] = {}

    def register(
        self,
        action_id: str,
        action: RegisteredAction,
    ) -> None:
        if not action_id.strip():
            raise ValueError("Action ID cannot be empty.")

        if action_id in self._actions:
            raise ValueError(f"Action '{action_id}' is already registered.")

        self._actions[action_id] = action

    def get(self, action_id: str) -> RegisteredAction:
        try:
            return self._actions[action_id]
        except KeyError as exc:
            raise LookupError(f"Action '{action_id}' is not registered.") from exc
